import os

from prometheus_client import Gauge

# Define Prometheus metrics

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

GROUP_MEMORY_USAGE = Gauge(
    "user_group_memory_bytes",
    "Working memory set usage in bytes by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
    ],
    namespace=namespace,
)

GROUP_COMPUTE_USAGE = Gauge(
    "user_group_cpu_seconds",
    "CPU usage in core seconds by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
    ],
    namespace=namespace,
)


GROUP_MEMORY_REQUESTS = Gauge(
    "user_group_memory_requests_bytes",
    "Memory requests in bytes by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
    ],
    namespace=namespace,
)


GROUP_COMPUTE_REQUESTS = Gauge(
    "user_group_cpu_requests_seconds",
    "CPU requests in core secounds by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
    ],
    namespace=namespace,
)

# Prometheus usage queries

USAGE_MEMORY = """
    label_replace(
        sum(
            container_memory_working_set_bytes{name!="", pod=~"jupyter-.*", namespace=~".*"} * on (namespace, pod)
            group_left(annotation_hub_jupyter_org_username)
            group(
                kube_pod_annotations{namespace=~".*", annotation_hub_jupyter_org_username!=""}
                ) by (pod, namespace, annotation_hub_jupyter_org_username)
            ) by (annotation_hub_jupyter_org_username, namespace),
        "username", "$1", "annotation_hub_jupyter_org_username", "(.*)"
    )
"""

USAGE_COMPUTE = """
    label_replace(
        sum(
            irate(container_cpu_usage_seconds_total{name!="", pod=~"jupyter-.*", namespace=~".*"}[5m]) * on (namespace, pod)
            group_left(annotation_hub_jupyter_org_username)
            group(
                kube_pod_annotations{namespace=~".*", annotation_hub_jupyter_org_username!=""}
                ) by (pod, namespace, annotation_hub_jupyter_org_username)
            ) by (annotation_hub_jupyter_org_username, namespace),
        "username", "$1", "annotation_hub_jupyter_org_username", "(.*)"
    )
"""

# Config for Prometheus usage queries

CONFIG = [
    {
        "query": USAGE_MEMORY,
        "update_interval": 1,
        "metric": GROUP_MEMORY_USAGE,
    },
    {
        "query": USAGE_COMPUTE,
        "update_interval": 1,
        "metric": GROUP_COMPUTE_USAGE,
    },
]
