"""
Prometheus user groups exported by JupyterHub.
"""

import argparse
import asyncio
import logging
import os

import aiohttp
import backoff
from prometheus_client import Gauge, start_http_server
from yarl import URL

logger = logging.getLogger(__name__)


@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=8, logger=logger)
async def fetch_page(session: aiohttp.ClientSession, hub_url: URL, path: str = False):
    """
    Fetch a page from the JupyterHub API.
    """
    url = hub_url / path if path else hub_url
    logger.debug(f"Fetching {url}")
    async with session.get(url) as response:
        return await response.json()


async def update_user_group_info(
    session: aiohttp.ClientSession, hub_url: URL, USER_GROUP: Gauge
):
    """
    Update the prometheus exporter with user group memberships fetched from the JupyterHub API.
    """
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

    n_users = 0
    USER_GROUP.clear()  # Clear previous prometheus metrics
    for group in items:
        for user in group["users"]:
            n_users += 1
            USER_GROUP.labels(usergroup=f"{group['name']}", username=f"{user}").set(1)
    logger.info(f"Updated {len(items)} groups and {n_users} in user_group_info.")


async def main():
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
        "--hub_url",
        default=f"http://{os.environ.get('HUB_SERVICE_HOST')}:{os.environ.get('HUB_SERVICE_PORT')}",
        type=str,
        help="JupyterHub service URL, e.g. http://localhost:8000 for local development.",
    )
    argparser.add_argument(
        "--api_token",
        default=os.environ.get("JUPYTERHUB_API_TOKEN"),
        type=str,
        help="Token to talk to the JupyterHub API.",
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

    USER_GROUP = Gauge(
        "user_group_info",
        "JupyterHub username and user group membership information.",
        ["username", "usergroup"],
        namespace=args.jupyterhub_metrics_prefix,
    )

    start_http_server(args.port)
    logger.info(
        f"Starting JupyterHub user groups Prometheus exporter on port {args.port} with an update interval of {args.update_exporter_interval} seconds."
    )

    hub_url = URL(args.hub_url)
    headers = {
        "Accept": "application/jupyterhub-pagination+json",
        "Authorization": f"token {args.api_token}",
    }

    asyncio.get_event_loop()
    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            await update_user_group_info(session, hub_url, USER_GROUP)
            await asyncio.sleep(args.update_exporter_interval)


if __name__ == "__main__":
    asyncio.run(main())
