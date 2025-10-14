"""
NOTE: This JupyterHub configuration file is included in this repo for local development.
"""

import pathlib
import secrets
import sys

c = get_config()  # noqa

# API page limit is 50 for users and groups endpoints. Initialize with n_users, with 1 user per group.
n_users = 5
c.Authenticator.allowed_users = {f"user-{i}" for i in range(n_users)}
c.JupyterHub.load_groups = {
    f"group-{i}": dict(users=[f"user-{i}"]) for i in range(n_users)
}
c.JupyterHub.load_groups.update({"group-2": dict(users=["user-0", "user-2"])})
c.JupyterHub.load_groups["group-1"]["users"].append("user-0")  # Add user-0 to group-1


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
log_level = "DEBUG"
c.JupyterHub.services = [
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
            "--log_level",
            f"{log_level}",
            "--jupyterhub_namespace",
            "default",
        ],
    },
]
