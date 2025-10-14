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
    generate_latest,
)
from yarl import URL

from .groups_exporter import update_group_usage, update_user_group_info
from .metrics import CONFIG_COMPUTE, CONFIG_DIRSIZE

logger = logging.getLogger(__name__)


def _str_to_bool(value: str) -> bool:
    if value.lower() == "true":
        return True
    else:
        return False


async def handle(request: web.Request):
    return web.Response(
        body=generate_latest(),
        status=200,
        content_type="text/plain",
    )


async def background_update(
    app: web.Application, config: dict, update_function: callable
):
    while True:
        try:
            data = await update_function(app, config)
            logger.debug(f"Fetched data for {update_function.__name__}: {data}")
        except Exception as e:
            logger.error(f"Error fetching data for {update_function.__name__}: {e}")
        await asyncio.sleep(int(config["update_interval"]))


async def on_startup(app):
    app["session"] = aiohttp.ClientSession(headers=app["headers"])
    logger.info("Client session started.")
    app["task"] = asyncio.create_task(
        background_update(
            app,
            {"update_interval": f"{app['update_info_interval']}"},
            update_user_group_info,
        )
    )
    for cfg in CONFIG_COMPUTE:
        cfg.update({"update_interval": f"{app['update_metrics_interval']}"})
        app["task"] = asyncio.create_task(
            background_update(app, dict(cfg), update_group_usage)
        )
    for cfg in CONFIG_DIRSIZE:
        cfg.update({"update_interval": f"{app['update_dirsize_interval']}"})
        app["task"] = asyncio.create_task(
            background_update(app, dict(cfg), update_group_usage)
        )


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
    update_info_interval: int = None,
    update_metrics_interval: int = None,
    update_dirsize_interval: int = None,
    prometheus_host: str = None,
    prometheus_port: int = None,
):
    app = web.Application()
    app["headers"] = headers
    app["hub_url"] = URL(hub_url)
    app["allowed_groups"] = allowed_groups
    app["double_count"] = double_count
    app["namespace"] = namespace
    app["jupyterhub_metrics_prefix"] = jupyterhub_metrics_prefix
    app["update_info_interval"] = update_info_interval
    app["update_metrics_interval"] = update_metrics_interval
    app["update_dirsize_interval"] = update_dirsize_interval
    app["prometheus_host"] = prometheus_host
    app["prometheus_port"] = prometheus_port
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
        "--update_info_interval",
        type=int,
        help="Time interval between each update of the user_group_info metric (seconds).",
    )
    argparser.add_argument(
        "--update_metrics_interval",
        type=int,
        help="Time interval between each update of the group usage metrics (seconds).",
    )
    argparser.add_argument(
        "--update_dirsize_interval",
        type=int,
        help="Time interval between each update of group home directory usage (seconds).",
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
        "--prometheus_host",
        default=os.environ.get(
            "SUPPORT_PROMETHEUS_SERVER_SERVICE_HOST",
            "localhost",  #  TODO: this env var is only available in the k8s support namespace
        ),
        type=str,
        help="Prometheus host URL.",
    )
    argparser.add_argument(
        "--prometheus_port",
        default=os.environ.get(
            "SUPPORT_PROMETHEUS_SERVER_SERVICE_PORT", "9090"
        ),  #  TODO: this env var is only available in the k8s support namespace
        type=int,
        help="Prometheus port.",
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

    if args.jupyterhub_metrics_prefix:
        os.environ["JUPYTERHUB_METRICS_PREFIX"] = args.jupyterhub_metrics_prefix

    logger.info(
        f"Starting JupyterHub user groups Prometheus exporter in namespace {args.jupyterhub_namespace}, port {args.port}."
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
        update_info_interval=args.update_info_interval,
        update_metrics_interval=args.update_metrics_interval,
        update_dirsize_interval=args.update_dirsize_interval,
        prometheus_host=args.prometheus_host,
        prometheus_port=args.prometheus_port,
    )
    app.add_subapp(args.hub_service_prefix, metrics_app)
    web.run_app(app, port=args.port)


if __name__ == "__main__":
    main()
