import os

from prometheus_client import Gauge

namespace = os.environ.get("JUPYTERHUB_METRICS_PREFIX", "jupyterhub")


USER_GROUP = Gauge(
    "user_group_info",
    "JupyterHub namespace, username and user group membership information.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
    ],
    namespace=namespace,
)

USER_GROUP_MEMORY = Gauge(
    "user_group_memory_bytes",
    "Memory usage in bytes by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
    ],
    namespace=namespace,
)
