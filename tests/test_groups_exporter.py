import logging

from prometheus_client.parser import text_string_to_metric_families

logger = logging.getLogger(__name__)


async def test_hub_alive(admin_request):
    """Test that the hub is alive and responding to requests."""
    try:
        response = await admin_request(path="hub/api/info")
    except Exception:
        raise RuntimeError("Hub is not alive")
    assert response["version"] is not None


async def test_groups_exporter_alive(admin_request):
    """Test that the groups exporter service is alive and responding to requests.

    TODO: Test as an externally managed service.
    """
    try:
        response = await admin_request(
            path="services/groups-exporter/", parse_json=False
        )
    except Exception as e:
        logger.info(f"test_groups_exporter_alive: {e}")
        raise RuntimeError("JupyterHub groups exporter service is not alive")
    assert response is not None


async def test_groups_exporter_number(admin_request):
    """Test that the number of groups and users in the exporter matches the hub config."""
    response = await admin_request(
        path="services/groups-exporter/metrics", parse_json=False
    )
    if response:
        for family in text_string_to_metric_families(response):
            if family.name == "jupyterhub_user_group_info":
                logger.info(f"{len(family.samples)} groups and users collected.")
                assert len(family.samples) == 100  # see tests/jupyterhub_config.py
    else:
        raise RuntimeError("No response returned from groups exporter service")
