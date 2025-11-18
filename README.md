# jupyterhub-groups-exporter

An externally-managed JupyterHub service to export user group memberships to Prometheus.

## Overview

The `jupyterhub-groups-exporter` project provides a service that integrates with [Zero to JupyterHub documentation](https://z2jh.jupyter.org) to export user group memberships as Prometheus metrics. This enables JupyterHub administrators to monitor usage and costs segmented by user groups using visualization tools like Grafana.

## Features

- Exports user group memberships from JupyterHub to Prometheus.
- Supports integration with Kubernetes clusters via Helm charts.

## Installation

This repository provides packaged Helm charts for the `jupyterhub-groups-exporter` project. These charts are hosted in the [`gh-pages` branch](https://github.com/2i2c-org/jupyterhub-groups-exporter/tree/gh-pages) and made available as a Helm chart repository.

### Prerequisites

- Kubernetes cluster
- Helm installed ([Helm documentation](https://helm.sh/docs/intro/install/))

### Steps

1. Add the Helm chart repository:

   ```shell
   helm repo add jupyterhub-groups-exporter https://2i2c.org/jupyterhub-groups-exporter
   helm repo update
   ```

2. Install the Helm chart:

   ```shell
   helm install jupyterhub-groups-exporter https://2i2c.org/jupyterhub-groups-exporter --version <version>
   ```

## Usage

Once installed, the `jupyterhub-groups-exporter` service will interact with the JupyterHub API to retrieve user group memberships and expose them as Prometheus metrics. These metrics can then be queried with PromQL and visualized in Grafana dashboards.

### Configuration

#### Exporter

The exporter supports the following argument options:

- `--port`: Port to listen on for the groups exporter. Default is `9090`.
- `--update_exporter_interval`: Time interval (in seconds) between each update of the JupyterHub groups exporter. Default is `3600`.
- `--allowed_groups`: List of allowed user groups to be exported. If not provided, all groups will be exported.
- `--default_group`: Default group to account usage against for users with multiple group memberships. Default is `"other"`.
- `--hub_url`: JupyterHub service URL, e.g., `http://localhost:8000` for local development. Default is constructed using environment variables `HUB_SERVICE_HOST` and `HUB_SERVICE_PORT`.
- `--api_token`: Token to authenticate with the JupyterHub API. Default is fetched from the environment variable `JUPYTERHUB_API_TOKEN`.
- `--jupyterhub_namespace`: Kubernetes namespace where the JupyterHub is deployed. Default is fetched from the environment variable `NAMESPACE`.
- `--jupyterhub_metrics_prefix`: Prefix/namespace for the JupyterHub metrics for Prometheus. Default is `"jupyterhub"`.
- `--log_level`: Logging level for the exporter service. Options are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. Default is `"INFO"`.

#### JupyterHub

The [`jupyterhub-groups-exporter`](https://github.com/2i2c-org/jupyterhub-groups-exporter) project provides a [service](https://jupyterhub.readthedocs.io/en/latest/reference/services.html) that integrates with JupyterHub to export user group memberships as Prometheus metrics. This component is readily deployable as part of any JupyterHub instance, such as a standalone deployment or a [Zero to JupyterHub (z2jh)](https://z2jh.jupyter.org/en/stable/) deployment on Kubernetes.

To enable the `jupyterhub-groups-exporter` service in your JupyterHub deployment, you need to add the service configuration to your JupyterHub configuration through your z2jh chart values. Here is an example configuration:

```yaml
jupyterhub:
  hub:
    services:
      jupyterhub-groups-exporter: {}
    loadRoles:
      jupyterhub-groups-exporter:
        services:
          - jupyterhub-groups-exporter
        scopes:
          - users
          - groups
```

You may also need configure a few settings for your [authenticator](https://oauthenticator.readthedocs.io/en/latest/) to provide group information to the exporter service. Here is an example configuration for the `GitHubOAuthenticator`:

```yaml
jupyterhub:
  hub:
    config:
      GitHubOAuthenticator:
        enable_auth_state: true
        manage_groups: true
        populate_teams_in_auth_state: true
        scope:
          - read:org
```

### Exporting user group memberships to Prometheus

The exporter provides a [Gauge metric](https://prometheus.io/docs/concepts/metric_types/) called `jupyterhub_user_group_info`, which contain the following labels:

- `namespace` – the Kubernetes namespace where the JupyterHub is deployed
- `usergroup` – the name of the user group
- `username` – the unescaped username of the user
- `username_escape` – the escaped username

Escaped usernames are useful because Kubernetes pods have characterset limits for valid pod label names (this limit does not apply to pod annotations). Storing both types of usernames allows us to join escaped versions with their more human-readable unescaped usernames.

Exposing this metric as an endpoint for Prometheus to scrape allows us to query and join groups data with a range of usage metrics to gain powerful group-level insights. Here is an example PromQL query that retrieves the memory usage by user group:

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

### Visualizing user group resource usage with Grafana

The PromQL query above is rather long and complex to construct! However, you can benefit from an [upstream contribution](https://github.com/jupyterhub/grafana-dashboards/pull/149) to the [jupyterhub/grafana-dashboards](https://github.com/jupyterhub/grafana-dashboards) project where we have encapsulated the PromQL queries as Jsonnet code and represented them as Grafana Dashboard visualizations (also known as [Grafonnet](https://grafana.github.io/grafonnet/index.html)).

## Contributing

Contributions to the `jupyterhub-groups-exporter` project are welcome! Please follow the standard GitHub workflow:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request.

## License

This project is licensed under the [BSD 3-Clause License](LICENSE).

## Resources

- [Helm Chart Repository](https://2i2c.org/jupyterhub-groups-exporter/)
- [Zero to JupyterHub Documentation](https://z2jh.jupyter.org)
- [jupyterhub/grafana-dashboards](https://github.com/jupyterhub/grafana-dashboards)
