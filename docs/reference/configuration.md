# Configuration

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
