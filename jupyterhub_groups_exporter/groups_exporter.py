"""
Prometheus user groups exported by JupyterHub.
"""

import argparse
import asyncio
import logging
import os
import string
from collections import Counter

import aiohttp
import backoff
import escapism
from aiohttp import web
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Gauge,
    generate_latest,
)
from yarl import URL

logger = logging.getLogger(__name__)


registry_groups = CollectorRegistry()


@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=12, logger=logger)
async def fetch_page(session: aiohttp.ClientSession, hub_url: URL, path: str = False):
    """
    Fetch a page from the JupyterHub API.
    """
    url = hub_url / path if path else hub_url
    logger.debug(f"Fetching {url}")
    async with session.get(url) as response:
        return await response.json()


def escape_username(username: str) -> str:
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
    USER_GROUP = app["USER_GROUP"]
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
                username_escaped=escape_username(user),
            ).set(1)
            logger.info(
                f"User {user} is in multiple groups: assigning to default group 'multiple'."
            )
            if double_count == "False":
                continue
        for group in user_to_groups[user]:
            USER_GROUP.labels(
                namespace=f"{namespace}",
                usergroup=f"{group}",
                username=f"{user}",
                username_escaped=escape_username(user),
            ).set(1)
            logger.info(f"User {user} is in group {group}.")


async def handle_home(request: web.Request):
    return web.Response(
        text="Welcome to the JupyterHub user groups exporter service.", status=200
    )


async def handle_groups(request: web.Request):
    return web.Response(
        body=generate_latest(registry_groups),
        status=200,
        content_type=CONTENT_TYPE_LATEST,
    )


async def background_update(app: web.Application, update_function: callable):
    while True:
        try:
            data = await update_function(app)
            logger.debug(f"Fetched data: {data}")
        except Exception as e:
            logger.error(f"Error updating user group info: {e}")
        await asyncio.sleep(app["update_interval"])


async def on_startup(app):
    app["session"] = aiohttp.ClientSession(headers=app["headers"])
    logger.info("Client session started.")
    app["task"] = asyncio.create_task(background_update(app, update_user_group_info))


async def on_cleanup(app):
    await app["session"].close()
    logger.info("Client session closed.")


def sub_app(
    headers: str = None,
    hub_url: str = None,
    allowed_groups: list = None,
    double_count: str = None,
    namespace: str = None,
    jupyterhub_metrics_prefix: str = None,
    update_interval: int = None,
    USER_GROUP: Gauge = None,
):
    app = web.Application()
    app["headers"] = headers
    app["hub_url"] = URL(hub_url)
    app["allowed_groups"] = allowed_groups
    app["double_count"] = double_count
    app["namespace"] = namespace
    app["jupyterhub_metrics_prefix"] = jupyterhub_metrics_prefix
    app["update_interval"] = update_interval
    app["USER_GROUP"] = USER_GROUP
    app.router.add_get("/", handle_home)
    app.router.add_get("/metrics/user-groups", handle_groups)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def main():
    argparser = argparse.ArgumentParser(
        description="JupyterHub user groups exporter for Prometheus."
    )
    argparser.add_argument(
        "--port",
        default=9090,
        type=int,
        help="Port to listen on for the groups exporter.",
    )
    argparser.add_argument(
        "--update_exporter_interval",
        default=3600,
        type=int,
        help="Time interval between each update of the JupyterHub groups exporter (seconds).",
    )
    argparser.add_argument(
        "--allowed_groups",
        nargs="*",
        help="List of allowed user groups to be exported. If not provided, all groups will be exported.",
    )
    argparser.add_argument(
        "--double_count",
        default="True",
        type=str,
        help="If 'True', double-count usage for users with multiple group memberships. If 'False', do not double-count. All users with multiple group memberships will be assigned to a default group called 'multiple'.",
    )
    argparser.add_argument(
        "--hub_url",
        default=f"http://{os.environ.get('HUB_SERVICE_HOST')}:{os.environ.get('HUB_SERVICE_PORT')}",
        type=str,
        help="JupyterHub service URL, e.g. http://localhost:8000 for local development.",
    )
    argparser.add_argument(
        "--hub_service_prefix",
        default=os.environ.get(
            "JUPYTERHUB_SERVICE_PREFIX", "services/groups-exporter"
        ).rstrip("/"),
        type=str,
        help="JupyterHub service prefix, defaults to '/services/groups-exporter'.",
    )
    argparser.add_argument(
        "--hub_api_token",
        default=os.environ.get("JUPYTERHUB_API_TOKEN"),
        type=str,
        help="Token to talk to the JupyterHub API.",
    )
    argparser.add_argument(
        "--jupyterhub_namespace",
        default=os.environ.get("NAMESPACE"),
        type=str,
        help="Kubernetes namespace where the JupyterHub is deployed.",
    )
    argparser.add_argument(
        "--jupyterhub_metrics_prefix",
        default=os.environ.get("JUPYTERHUB_METRICS_PREFIX", "jupyterhub"),
        type=str,
        help="Prefix/namespace for the JupyterHub metrics for Prometheus.",
    )
    argparser.add_argument(
        "--log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str,
        help="Set logging level: DEBUG, INFO, WARNING, etc.",
    )

    args = argparser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [jupyterhub-groups-exporter] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.allowed_groups:
        logger.info(
            f"Filtering JupyterHub user groups exporter to only include: {args.allowed_groups}"
        )
    else:
        args.allowed_groups = None

    if args.double_count:
        logger.info(
            f"Double-count users with multiple group memberships: {args.double_count}"
        )

    logger.info(
        f"Starting JupyterHub user groups Prometheus exporter in namespace {args.jupyterhub_namespace}, port {args.port} with an update interval of {args.update_exporter_interval} seconds."
    )

    USER_GROUP = Gauge(
        "user_group_info",
        "JupyterHub namespace, username and user group membership information.",
        [
            "namespace",
            "usergroup",
            "username",
            "username_escaped",
        ],
        namespace=args.jupyterhub_metrics_prefix,
        registry=registry_groups,
    )

    URL(args.hub_url)
    headers = {
        "Accept": "application/jupyterhub-pagination+json",
        "Authorization": f"token {args.hub_api_token}",
    }

    app = web.Application()
    # Mount sub app to route the hub service prefix
    metrics_app = sub_app(
        headers=headers,
        hub_url=args.hub_url,
        allowed_groups=args.allowed_groups,
        double_count=args.double_count,
        namespace=args.jupyterhub_namespace,
        jupyterhub_metrics_prefix=args.jupyterhub_metrics_prefix,
        update_interval=args.update_exporter_interval,
        USER_GROUP=USER_GROUP,
    )
    app.add_subapp(args.hub_service_prefix, metrics_app)
    web.run_app(app, port=args.port)


if __name__ == "__main__":
    main()
