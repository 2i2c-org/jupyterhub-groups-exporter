# jupyterhub-groups-exporter

# [jupyterhub-groups-exporter](https://github.com/2i2c-org/jupyterhub-groups-exporter)

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
# Let helm the command line tool know about a Helm chart repository
# that we decide to name frx-challenges.
helm repo add jupyterhub-groups-exporter https://2i2c.org/jupyterhub-groups-exporter
helm repo update

# Simplified example on how to install a Helm chart from a Helm chart repository
# named jupyterhub-groups-exporter. See the Helm chart's documentation for additional details
# required.
helm install jupyterhub-groups-exporter https://2i2c.org/jupyterhub-groups-exporter --version <version>
```

## Local development of GitHub page

### Background knowledge

To locally develop the GitHub page for this repository, some background
understanding can be useful. A good start is to read [Helm's documentation about
Helm chart repositories](https://helm.sh/docs/chart_repository). After that,
keep this in mind.

- [GitHub Pages][] relies on [Jekyll][] that in turn use the [Liquid][] templating
  language (with some [additions](https://jekyllrb.com/docs/liquid/)) to
  generate and host static web pages.
- Everything that is to be used to generate [the GitHub
  Page](https://hub.jupyter.org/helm-chart/) is required to reside at the
  [`gh-pages` branch](https://github.com/jupyterhub/helm-chart/tree/gh-pages).
- Templates get data from a [Jekyll Data
  Folder](https://jekyllrb.com/docs/datafiles/#the-data-folder) that you can
  [inspect here](https://github.com/jupyterhub/helm-chart/tree/gh-pages/_data).
  This folder only contains a symlink file that in turn points to
  [index.yaml](https://github.com/jupyterhub/helm-chart/blob/gh-pages/index.yaml)
  which is a [important file for a Helm chart
  repository](https://helm.sh/docs/chart_repository/#the-index-file).
- [index.md](https://github.com/jupyterhub/helm-chart/blob/gh-pages/index.md)
  file will be converted to index.html by Jekyll and act as a Human readable
  page.
- [_config.yml](https://github.com/jupyterhub/helm-chart/blob/gh-pages/_config.yml)
  is a [Jekyll configuration file](https://jekyllrb.com/docs/configuration/).
- [Gemfile](https://github.com/jupyterhub/helm-chart/blob/gh-pages/Gemfile) acts
  like a `doc-requirements.txt` but for Ruby, allowing us to work with Jekyll
  locally a bit easier.
- [info.json](https://github.com/jupyterhub/helm-chart/blob/gh-pages/info.json)
  is a way for us to provide easy access to information from the templates
  underlying data source, the
  [index.yaml](https://github.com/jupyterhub/helm-chart/blob/gh-pages/index.yaml)
  file. We are for example using the rendered info.json to create the badges you
  find in this readme about the latest stable/pre/dev release.

### Setting up for local development

There are probably different ways to go about this, but sometimes what matters
is to have one at all. Doing the following was tested by @consideRatio
2019-10-19 on Ubuntu 19.04.

1. Install Ruby, Gem, and Bundler.

   1. Install [`rbenv`](https://github.com/rbenv/rbenv#installation).
   1. Install the [rbenv-build plugin](https://github.com/rbenv/ruby-build#installation) to allows you to use `rbenv install`.
   1. Run `rbenv install <version>` with the [latest stable version](https://www.ruby-lang.org/en/downloads/).
   1. Run `rbenv global <version>`.
   1. Verify you can run `ruby -v` and `gem -v`.
   1. Run `gem install bundler` to work with Gemfiles etc.

1. Install Jekyll.

   1. Checkout the `gh-pages` branch with `git checkout gh-pages`.
   1. Run `bundle install`

1. Start a local webserver.

   1. Run `bundle exec jekyll serve`.
   1. Visit http://localhost:4000.

[Kubernetes]: https://kubernetes.io
[Helm]: https://helm.sh
[Chartpress]: https://github.com/jupyterhub/chartpress
[Zero to JupyterHub K8s]: https://github.com/jupyterhub/zero-to-jupyterhub-k8s
[KubeSpawner]: https://github.com/jupyterhub/kubespawner
[repo2docker]: https://github.com/jupyter/repo2docker
[GitHub Pages]: https://pages.github.com/
[Jekyll]: https://jekyllrb.com
[Liquid]: https://shopify.github.io/liquid/
