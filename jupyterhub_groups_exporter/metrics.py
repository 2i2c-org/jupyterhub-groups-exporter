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
        "username_safe",
    ],
    namespace=namespace,
)

GROUP_USAGE_MEMORY = Gauge(
    "user_group_memory_bytes",
    "Working memory set usage in bytes by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
        "username_safe",
    ],
    namespace=namespace,
)

GROUP_USAGE_COMPUTE = Gauge(
    "user_group_cpu_seconds",
    "CPU usage in core seconds by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
        "username_safe",
    ],
    namespace=namespace,
)


GROUP_REQUESTS_MEMORY = Gauge(
    "user_group_memory_requests_bytes",
    "Memory requests in bytes by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
        "username_safe",
    ],
    namespace=namespace,
)


GROUP_REQUESTS_COMPUTE = Gauge(
    "user_group_cpu_requests_seconds",
    "CPU requests in core seconds by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
        "username_safe",
    ],
    namespace=namespace,
)


GROUP_HOME_DIR = Gauge(
    "user_group_home_dir_bytes",
    "Home directory usage in bytes by user and group.",
    [
        "namespace",
        "usergroup",
        "username",
        "username_escaped",
        "username_safe",
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
                kube_pod_annotations{namespace=~".*", annotation_hub_jupyter_org_username=~".*"}
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
                kube_pod_annotations{namespace=~".*", annotation_hub_jupyter_org_username=~".*"}
                ) by (pod, namespace, annotation_hub_jupyter_org_username)
            ) by (annotation_hub_jupyter_org_username, namespace),
        "username", "$1", "annotation_hub_jupyter_org_username", "(.*)"
    )
"""

REQUESTS_MEMORY = """
    label_replace(
        sum(
            kube_pod_container_resource_requests{resource="memory", namespace=~".*", pod=~"jupyter-.*"} * on (namespace, pod)
            group_left(annotation_hub_jupyter_org_username) group(
                kube_pod_annotations{namespace=~".*", annotation_hub_jupyter_org_username=~".*"}
                ) by (pod, namespace, annotation_hub_jupyter_org_username)
        ) by (annotation_hub_jupyter_org_username, namespace),
        "username", "$1", "annotation_hub_jupyter_org_username", "(.*)"
    )
"""

REQUESTS_COMPUTE = """
    label_replace(
        sum(
            kube_pod_container_resource_requests{resource="cpu", namespace=~".*", pod=~"jupyter-.*"} * on (namespace, pod)
            group_left(annotation_hub_jupyter_org_username) group(
                kube_pod_annotations{namespace=~".*", annotation_hub_jupyter_org_username=~".*"}
                ) by (pod, namespace, annotation_hub_jupyter_org_username)
        ) by (annotation_hub_jupyter_org_username, namespace),
        "username", "$1", "annotation_hub_jupyter_org_username", "(.*)"
    )     
"""

HOME_DIR = """
    max(
        dirsize_total_size_bytes{namespace=~".*"}
        * on (namespace, directory) group_left(username)
        group(
            label_replace(
            jupyterhub_user_group_info{namespace=~".*", username_escaped=~".*"},
                "directory", "$1", "username_escaped", "(.+)")
        ) by (directory, namespace, username)
    ) by (namespace, username)
"""

# Config for Prometheus queries


CONFIG_COMPUTE = [
    {
        "query": USAGE_MEMORY,
        "metric": GROUP_USAGE_MEMORY,
    },
    {
        "query": USAGE_COMPUTE,
        "metric": GROUP_USAGE_COMPUTE,
    },
    {
        "query": REQUESTS_MEMORY,
        "metric": GROUP_REQUESTS_MEMORY,
    },
    {
        "query": REQUESTS_COMPUTE,
        "metric": GROUP_REQUESTS_COMPUTE,
    },
]


CONFIG_DIRSIZE = [
    {
        "query": HOME_DIR,
        "metric": GROUP_HOME_DIR,
    },
]
