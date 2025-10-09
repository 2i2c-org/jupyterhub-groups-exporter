import logging
import string
from collections import Counter
from datetime import datetime, timedelta

import aiohttp
import backoff
import escapism
from aiohttp import web
from yarl import URL

from .metrics import MEMORY_REQUESTS_PER_USER, USER_GROUP, USER_GROUP_MEMORY

logger = logging.getLogger(__name__)


@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=12, logger=logger)
async def fetch_page(
    session: aiohttp.ClientSession, url: URL, path: str = False, params: dict = None
):
    """
    Fetch a page from the JupyterHub API.
    """
    url = url / path if path else url
    logger.debug(f"Fetching {url}")
    async with session.get(url, params=params) as response:
        return await response.json()


def _escape_username(username: str) -> str:
    """
    Escape the username when a 'safe' string is required, e.g. kubernetes pod labels, directory names, etc.
    """
    safe_chars = set(string.ascii_lowercase + string.digits)
    escaped_username = escapism.escape(
        username, safe=safe_chars, escape_char="-"
    ).lower()
    return escaped_username


async def update_user_group_info(
    app: web.Application,
):
    """
    Update the prometheus exporter with user group memberships fetched from the JupyterHub API.
    """
    session = app["session"]
    hub_url = app["hub_url"]
    allowed_groups = app["allowed_groups"]
    double_count = app["double_count"]
    namespace = app["namespace"]
    data = await fetch_page(session, hub_url, "hub/api/groups")
    if "_pagination" in data:
        logger.debug(f"Received paginated data: {data['_pagination']}")
        items = data["items"]
        next_info = data["_pagination"]["next"]
        while next_info:
            data = await fetch_page(session, next_info["url"])
            next_info = data["_pagination"]["next"]
            items.extend(data["items"])
    else:
        logger.debug("Received non-paginated data.")
        items = data

    logger.debug(f"Items: {items}")
    list_groups = (
        [group["name"] for group in items] if allowed_groups is None else allowed_groups
    )
    list_users = (
        [
            user
            for group in items
            if group["name"] in allowed_groups
            for user in group["users"]
        ]
        if allowed_groups
        else [user for group in items for user in group["users"]]
    )
    user_counts = Counter(list_users)
    users_in_multiple_groups = [
        user for user, count in user_counts.items() if count > 1
    ]
    unique_users = list(set(list_users))
    logger.debug(f"List groups: {list_groups}")
    logger.debug(f"Users in multiple groups: {users_in_multiple_groups}")
    logger.info(
        f"Updating {len(list_groups)} groups and {len(unique_users)} users for metric user_group_info."
    )
    # Clear previous prometheus metrics
    USER_GROUP.clear()
    # Filter out groups not in the allowed list
    for group in items.copy():
        if group["name"] not in list_groups:
            logger.debug(f"Group {group['name']} is not in allowed groups, skipping.")
            items.remove(group)
    # Invert the mapping from groups -> users to user -> groups
    user_to_groups = {}
    for group in items:
        for user in group["users"]:
            user_to_groups.setdefault(user, []).append(group["name"])
    # Loop over users
    for user in list(user_to_groups.keys()):
        if user in users_in_multiple_groups:
            USER_GROUP.labels(
                namespace=f"{namespace}",
                usergroup="multiple",
                username=f"{user}",
                username_escaped=_escape_username(user),
            ).set(1)
            logger.info(
                f"User {user} is in multiple groups: assigning to default group 'multiple'."
            )
            if double_count == False:
                continue
        for group in user_to_groups[user]:
            USER_GROUP.labels(
                namespace=f"{namespace}",
                usergroup=f"{group}",
                username=f"{user}",
                username_escaped=_escape_username(user),
            ).set(1)
            logger.info(f"User {user} is in group {group}.")
    app["user_group_map"] = user_to_groups


async def update_group_usage(app: web.Application):
    """
    Attach user and group labels for metrics used to populate the User Group Diagnostics dashboard.
    """
    logger.info("This is the update_group_usage coroutine.")
    namespace = app["namespace"]
    prometheus_host = app["prometheus_host"]
    prometheus_port = app["prometheus_port"]
    update_usage_interval = app["update_usage_interval"]
    app["user_group_map"]
    prometheus_api = URL.build(
        scheme="http", host=prometheus_host, port=prometheus_port
    )
    query = MEMORY_REQUESTS_PER_USER.replace(
        'namespace=~".*"', f'namespace="{namespace}"'
    )
    from_date = datetime.utcnow() - timedelta(seconds=update_usage_interval)
    to_date = datetime.utcnow()
    step = str(update_usage_interval) + "s"
    parameters = {
        "query": query,
        "start": from_date.isoformat() + "Z",
        "end": to_date.isoformat() + "Z",
        "step": step,
    }
    logger.debug(f"Prometheus query parameters: {parameters}")
    data = await fetch_page(
        session=app["session"],
        url=prometheus_api,
        path="api/v1/query_range",
        params=parameters,
    )
    if data["status"] != "success":
        raise aiohttp.ClientError(f"Bad response from Prometheus: {data}")
    results = data["data"]["result"]
    logger.debug(f"Prometheus results: {results}")
    USER_GROUP_MEMORY.clear()
    for r in results:
        USER_GROUP_MEMORY.labels(
            namespace=f"{namespace}",
            username=f"{r['metric']['username']}",
            username_escaped=_escape_username(r["metric"]["username"]),
            usergroup="multiple",
        ).set(float(r["values"][-1][-1]))
