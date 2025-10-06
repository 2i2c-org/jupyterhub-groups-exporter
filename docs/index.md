# JupyterHub Groups Exporter

An externally-managed JupyterHub service to export user group memberships to Prometheus.

## Overview

The `jupyterhub-groups-exporter` project provides a service that integrates with [Zero to JupyterHub documentation](https://z2jh.jupyter.org) to export user group memberships as Prometheus metrics. This enables JupyterHub administrators to monitor usage and costs segmented by user groups using visualization tools like Grafana.

## Features

- Exports user group memberships from JupyterHub to Prometheus.
- Supports integration with Kubernetes clusters via Helm charts.

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
