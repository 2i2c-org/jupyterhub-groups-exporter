import pathlib
import secrets
import sys

c = get_config()  # noqa

# API page limit is 50 for users and groups endpoints. Initialize with n_users, with 1 user per group.
n_users = 100
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

jupyterhub_groups_exporter_port = 9090
jupyterhub_groups_exporter_interval = 10
c.JupyterHub.services = [
    {
        "name": "groups-exporter",
        "api_token": token,
        "url": f"http://{c.JupyterHub.ip}:{jupyterhub_groups_exporter_port}",
        "command": [
            sys.executable,
            "-m",
            "jupyterhub_groups_exporter.groups_exporter",
            "--port",
            f"{jupyterhub_groups_exporter_port}",
            "--update_exporter_interval",
            f"{jupyterhub_groups_exporter_interval}",
            "--log_level",
            "DEBUG",
        ],
    },
]
