# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# server.py
from datacommons.mcp.clients import create_clients
from datacommons.mcp.config import BASE_DC_CONFIG
from datacommons.mcp.models.observation_schemas import (
    ObservationFacetResponse,
    ObservationRequest,
)
from datacommons.mcp.models.resolve_place_schemas import (
    ResolvedPlaces,
)

from mcp.server.fastmcp import FastMCP

# Create DC MultiClient
multi_dc_client = create_clients(BASE_DC_CONFIG)

# Create an MCP server
mcp = FastMCP("Data Commons")


@mcp.tool()
async def fetch_place_dcid(place_name: str) -> ResolvedPlaces:
    return multi_dc_client.base_dc.search_places([place_name])


@mcp.tool()
async def fetch_child_place_type_dcids(place_dcid: str) -> ResolvedPlaces:
    return multi_dc_client.base_dc.get_child_place_type_dcids(place_dcid)


@mcp.tool()
async def fetch_stat_vars(stat_var_descs: list[str]) -> None:
    return multi_dc_client.search_svs([stat_var_descs])


@mcp.tool()
async def fetch_observations(
    variable_dcids: list[str],
    place_dcids: list[str] | None = None,
    parent_place_dcid: str | None = None,
    child_place_type_dcid: str | None = None,
    facet_id_override: str | None = None,
) -> ObservationFacetResponse:
    """TODO"""
    # 1. Input validation
    obs_request = ObservationRequest(
        variable_dcids=variable_dcids,
        place_dcids=place_dcids,
        parent_place_dcid=parent_place_dcid,
        child_place_type_dcid=child_place_type_dcid,
        facet_ids=facet_id_override,
    )

    # Fetch Data
    return await multi_dc_client.fetch_obs(obs_request)
