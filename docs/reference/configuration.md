# Configuration

## Exporter

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

## JupyterHub

To enable the `jupyterhub-groups-exporter` service in your JupyterHub deployment, you need to add the service configuration to your JupyterHub configuration through your [Zero To JupyterHub](https://z2jh.jupyter.org/en/stable/) (z2jh) chart values. Here is an example configuration:

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
