# Metrics

The [`jupyterhub-groups-exporter`](https://github.com/2i2c-org/jupyterhub-groups-exporter) project provides a [service](https://jupyterhub.readthedocs.io/en/latest/reference/services.html) that integrates with JupyterHub to export user group memberships as Prometheus metrics. This component is readily deployable as part of any JupyterHub instance, such as a standalone deployment or a Zero to JupyterHub deployment on Kubernetes.

The exporter provides a [Gauge metric](https://prometheus.io/docs/concepts/metric_types/) called `jupyterhub_user_group_info`, which contain the following labels:

- `namespace` – the Kubernetes namespace where the JupyterHub is deployed
- `usergroup` – the name of the user group
- `username` – the unescaped username of the user
- `username_escaped` – the escaped username, using kubespawner's legacy escaping scheme "escape"
- `username_safe` – the escaped username, using kubespawner's modern escaping scheme "safe"

Escaped usernames are useful because Kubernetes pods have characterset limits for valid pod label names (this limit does not apply to pod annotations). As of [Kubespawner v7.0](https://jupyterhub-kubespawner.readthedocs.io/en/latest/templates.html#upgrading-from-kubespawner-7), a "safe" escaping mechanism was introduced to template fields to enforce valid labels. Storing both types of usernames allows us to join escaped versions with their more human-readable unescaped usernames.

Exposing these metrics as an endpoint for Prometheus to scrape allows us to query and join groups data with a range of usage metrics to gain powerful group-level insights. Here is an example PromQL query that retrieves the memory usage by user group:

```promql
sum(
  container_memory_working_set_bytes{name!="", pod=~"jupyter-.*", namespace=~"$hub_name"}
    * on (namespace, pod) group_left(annotation_hub_jupyter_org_username, usergroup)
    group(
        kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~".*", pod=~"jupyter-.*"}
    ) by (pod, namespace, annotation_hub_jupyter_org_username)
    * on (namespace, annotation_hub_jupyter_org_username) group_left(usergroup)
    group(
      label_replace(jupyterhub_user_group_info{namespace=~"$hub_name", username=~".*", usergroup=~"$user_group"},
        "annotation_hub_jupyter_org_username", "$1", "username", "(.+)")
    ) by (annotation_hub_jupyter_org_username, usergroup, namespace)
) by (usergroup, namespace)
```
