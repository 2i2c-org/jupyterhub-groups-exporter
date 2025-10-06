# Installation

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
