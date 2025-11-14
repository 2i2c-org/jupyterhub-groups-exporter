import copy
import logging
import string
from collections import Counter
from datetime import datetime, timedelta

import aiohttp
import backoff
import escapism
from aiohttp import web
from yarl import URL

from .metrics import USER_GROUP

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
    config: dict = None,
):
    """
    Update the prometheus exporter with user group memberships fetched from the JupyterHub API.
    """
    logger.info("This is the update_user_group_info coroutine.")
    session = app["session"]
    hub_url = app["hub_url"]
    allowed_groups = app["allowed_groups"]
    double_count = app["double_count"]
    namespace = app["namespace"]
    endpoints = ["hub/api/users", "hub/api/groups"]
    results = []
    for i in range(len(endpoints)):
        endpoint = endpoints[i]
        data = await fetch_page(session, hub_url, endpoint)
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
        results.extend(items)
    list_groups = []
    list_users = []
    for r in results:
        if r["kind"] == "group" and (
            r["name"] in allowed_groups or allowed_groups == []
        ):
            list_groups.append(r["name"])
        elif r["kind"] == "user":
            for group in r["groups"]:
                if group in allowed_groups or allowed_groups == []:
                    list_users.append(r["name"])
    user_counts = Counter(list_users)
    users_in_multiple_groups = [
        user for user, count in user_counts.items() if count > 1
    ]
    unique_users = list(set(list_users))
    logger.debug(f"List groups: {list_groups}")
    logger.debug(f"List users: {list_users}")
    logger.debug(f"Users in multiple groups: {users_in_multiple_groups}")
    logger.info(
        f"Updating {len(list_groups)} groups and {len(unique_users)} users for metric user_group_info."
    )
    user_to_groups = {}
    for r in results:
        user = r["name"]
        if r["kind"] == "user" and user in unique_users:
            if r["groups"] != []:
                for group in r["groups"]:
                    user_to_groups.setdefault(user, []).append(group)
        elif r["kind"] == "user":
            logger.debug(f"User {user} has no groups.")
            user_to_groups.setdefault(user, ["none"])
    logger.debug(f"User to groups mapping: {user_to_groups}")
    # Loop over users to export
    USER_GROUP.clear()
    for user in list(user_to_groups.keys()):
        if user in users_in_multiple_groups:
            user_to_groups[user].append("multiple")
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


async def update_group_usage(app: web.Application, config: dict):
    """
    Attach user and group labels for metrics used to populate the User Group Diagnostics dashboard.
    """
    logger.info("This is the update_group_usage coroutine.")
    if not app.get("user_group_map"):
        logger.info("Doing nothing pending initialization of user_group_map.")
        return
    namespace = app["namespace"]
    prometheus_host = app["prometheus_host"]
    prometheus_port = app["prometheus_port"]
    update_metrics_interval = app["update_metrics_interval"]
    user_group_map = app["user_group_map"]
    logger.debug(f"User group map: {user_group_map}")
    prometheus_api = URL.build(
        scheme="http", host=prometheus_host, port=prometheus_port
    )
    query = config["query"].replace('namespace=~".*"', f'namespace="{namespace}"')
    from_date = datetime.utcnow() - timedelta(seconds=update_metrics_interval)
    to_date = datetime.utcnow()
    step = str(config["update_interval"]) + "s"
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
    joined = []
    for r in results:
        username = r["metric"]["username"]
        groups = user_group_map.get(username, [])
        if not groups:
            r_copy = copy.deepcopy(r)
            r_copy["metric"]["usergroup"] = "none"
            joined.append(r_copy)
            logger.debug(f"User {username} has no groups, assigning to 'none'.")
        else:
            for group in groups:
                r_copy = copy.deepcopy(r)
                r_copy["metric"]["usergroup"] = group
                joined.append(r_copy)
    logger.debug(f"Joined metrics: {joined}")
    # Export joined metrics
    config["metric"].clear()
    for j in joined:
        config["metric"].labels(
            namespace=f"{namespace}",
            username=f"{j['metric']['username']}",
            username_escaped=_escape_username(j["metric"]["username"]),
            usergroup=f"{j['metric']['usergroup']}",
        ).set(float(j["values"][-1][-1]))
