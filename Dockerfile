FROM python:3.13-bookworm

RUN apt-get update > /dev/null && \
    apt-get install --yes tini > /dev/null && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir /opt/jupyterhub_groups_exporter
COPY pyproject.toml /opt/jupyterhub_groups_exporter
COPY LICENSE /opt/jupyterhub_groups_exporter
COPY README.md /opt/jupyterhub_groups_exporter
COPY jupyterhub_groups_exporter /opt/jupyterhub_groups_exporter/jupyterhub_groups_exporter

WORKDIR /opt/jupyterhub_groups_exporter

RUN pip install -e .

ENTRYPOINT ["tini", "--"]
