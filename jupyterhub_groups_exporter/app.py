"""
Application backend to fetch user group memberships from the JupyterHub API and re-export usage data from Prometheus with user and group labels .
"""

import argparse
import asyncio
import logging
import os

import aiohttp
from aiohttp import web
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    generate_latest,
)
from yarl import URL

from .groups_exporter import update_user_group_info

logger = logging.getLogger(__name__)

registry_groups = CollectorRegistry()


def _str_to_bool(value: str) -> bool:
    if value.lower() == "true":
        return True
    else:
        return False


async def handle(request: web.Request):
    return web.Response(
        body=generate_latest(registry_groups),
        status=200,
        content_type="text/plain",
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
    app.router.add_get("/", handle)
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
        default="true",
        type=_str_to_bool,
        help="If 'true', double-count usage for users with multiple group memberships. If 'false', do not double-count. All users with multiple group memberships will be assigned to a default group called 'multiple'.",
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
            "JUPYTERHUB_SERVICE_PREFIX", "/services/groups-exporter/"
        ),
        type=str,
        help="JupyterHub service prefix, defaults to '/services/groups-exporter/'.",
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
