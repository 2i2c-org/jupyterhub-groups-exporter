"""
NOTE: This JupyterHub configuration file is included in this repo for local development and testing.
"""

import os
import pathlib
import secrets
import sys

c = get_config()  # noqa

# API page limit is 50 for users and groups endpoints. Initialize with n_users, with 1 user per group.
n_users = 51
c.Authenticator.allowed_users = {f"user-{i}" for i in range(n_users)}
c.JupyterHub.load_groups = {
    f"group-{i}": dict(users=[f"user-{i}"]) for i in range(n_users)
}

c.Authenticator.admin_users = {"admin"}
c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.spawner_class = "simple"

c.JupyterHub.last_activity_interval = 3
c.JupyterHub.ip = "127.0.0.1"
c.JupyterHub.hub_ip = "127.0.0.1"
c.JupyterHub.port = 8000
c.JupyterHub.cleanup_proxy = True
c.JupyterHub.cleanup_servers = True

c.JupyterHub.load_roles = [
    {
        "name": "pytest",
        "scopes": [
            "read:hub",
            "users",
            "groups",
        ],
        "services": ["pytest"],
    },
    {
        "name": "groups-exporter",
        "scopes": [
            "users",
            "groups",
        ],
        "services": ["groups-exporter"],
    },
]

here = pathlib.Path(__file__).parent
token_file = here.joinpath("service-token")
if token_file.exists():
    with token_file.open("r") as f:
        token = f.read()
else:
    token = secrets.token_hex(16)
    with token_file.open("w") as f:
        f.write(token)

jupyterhub_groups_exporter_port = 8080
update_info_interval = 30
update_metrics_interval = 5
update_dirsize_interval = 5
c.JupyterHub.services = [
    {
        "name": "pytest",
        "api_token": os.environ.get("TEST_PYTEST_TOKEN"),
    },
    {
        "name": "groups-exporter",
        "api_token": token,
        "url": f"http://{c.JupyterHub.ip}:{jupyterhub_groups_exporter_port}",
        "command": [
            sys.executable,
            "-m",
            "jupyterhub_groups_exporter.app",
            "--port",
            f"{jupyterhub_groups_exporter_port}",
            "--hub_url",
            f"http://{c.JupyterHub.hub_ip}:{c.JupyterHub.port}",
            "--update_info_interval",
            f"{update_info_interval}",
            "--update_metrics_interval",
            f"{update_metrics_interval}",
            "--update_dirsize_interval",
            f"{update_dirsize_interval}",
            "--double_count",
            "true",
            "--jupyterhub_namespace",
            "default",
        ],
    },
]
