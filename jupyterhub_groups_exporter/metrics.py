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

# Prometheus usage queries

MEMORY_REQUESTS_PER_USER = """
    label_replace(
        sum(
        container_memory_working_set_bytes{name!="", pod=~"jupyter-.*", namespace=~".*"} * on (namespace, pod)
        group_left(annotation_hub_jupyter_org_username) group(
            kube_pod_annotations{annotation_hub_jupyter_org_username!=""}
            ) by (pod, namespace, annotation_hub_jupyter_org_username)
        ) by (annotation_hub_jupyter_org_username, namespace),
        "username", "$1", "annotation_hub_jupyter_org_username", "(.*)"
    )
"""
