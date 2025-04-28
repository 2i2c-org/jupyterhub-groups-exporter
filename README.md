# jupyterhub-groups-exporter

An externally-managed JupyterHub service to export user group memberships to Prometheus.

## Overview

A common user story is that JupyterHub admins would like to monitor usage and costs segmented by user groups. This allows them to advocate for better cost recovery based on their own internal needs and funding models.

The goal of this project is to provide a simple, externally-managed JupyterHub service that exports user group memberships to Prometheus. This allows JupyterHub admins to monitor usage and costs segmented by user groups using visualization tools like Grafana.

## Installation

> [!NOTE]  
> This README content is adapted from the [JupyterHub/helm-chart](https://github.com/jupyterhub/helm-chart) repository.

This repository stores in its [`gh-pages`
branch](https://github.com/2i2c-org/jupyterhub-groups-exporter/tree/gh-pages) _packaged_ Helm
charts for the [jupyterhub-groups-exporter](https://github.com/2i2c-org/jupyterhub-groups-exporter) project. These packaged Helm
charts are made available as a valid [Helm chart
repository](https://helm.sh/docs/chart_repository/) on [an automatically updated
website](https://2i2c.org/jupyterhub-groups-exporter/) thanks to [GitHub Pages](https://pages.github.com/).
We use [chartpress](https://github.com/jupyterhub/chartpress) to add package and add Helm charts to this Helm chart
repository.

## Usage

This Helm chart repository enables you to install the jupyterhub-groups-exporter
Helm chart directly from it into your Kubernetes cluster. Please refer to the
[JupyterHub Helm chart documentation](https://z2jh.jupyter.org) or the
[BinderHub Helm chart documentation](https://binderhub.readthedocs.io) for all
the additional details required.

```shell
helm repo add jupyterhub-groups-exporter https://2i2c.org/jupyterhub-groups-exporter
helm repo update
helm install jupyterhub-groups-exporter https://2i2c.org/jupyterhub-groups-exporter --version <version>
```
