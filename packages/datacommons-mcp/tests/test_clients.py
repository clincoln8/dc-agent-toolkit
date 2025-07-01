from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.datacommons.mcp.clients import create_clients
from src.datacommons.mcp.config import BASE_DC_CONFIG
from src.datacommons.mcp.models.observation_schemas import ObservationRequest


@pytest.mark.asyncio
async def test_fetch_place_dcids() -> None:
    multi_client = create_clients(BASE_DC_CONFIG)
    res = await multi_client.base_dc.search_places(["california, maryland"])
    assert True


@pytest.mark.asyncio
async def test_fetch_child_place_type_dcids() -> None:
    multi_client = create_clients(BASE_DC_CONFIG)
    res = await multi_client.base_dc.get_child_place_type_dcids("geoId/06")
    print(res)
    assert True


@pytest.mark.asyncio
async def test_search_svs() -> None:
    multi_client = create_clients(BASE_DC_CONFIG)
    res = await multi_client.base_dc.search_svs(["total population"])
    assert True


@pytest.mark.asyncio
async def test_fetch_obs_with_no_custom_dcs() -> None:
    multi_client = create_clients(BASE_DC_CONFIG)
    res = await multi_client.fetch_obs(
        obs_request=ObservationRequest(
            variable_dcids=["Count_Person"], place_dcids=["geoId/06"]
        )
    )
    assert True
