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
"""
Clients module for interacting with Data Commons instances.
Provides classes for managing connections to both base and custom Data Commons instances.
"""

import asyncio
import json

import requests
from datacommons.mcp.config import ClientConfig
from datacommons.mcp.constants import BASE_DC_ID, DEFAULT_API_TIMEOUT
from datacommons.mcp.models.observation_schemas import (
    ObservationFacetResponse,
    ObservationRequest,
    PlaceData,
    SourceMetadata,
    VariableSeries,
)
from datacommons.mcp.models.resolve_place_schemas import ResolvedPlace, ResolvedPlaces
from datacommons_client.client import DataCommonsClient
from datacommons_client.endpoints.response import ObservationResponse


class DCClient:
    def __init__(
        self,
        dc_name: str = "Data Commons",
        base_url: str = None,
        api_key: str = None,
        idx: str = "base_uae_mem",
    ) -> None:
        """
        Initialize the DCClient with either an API key or a base URL.

        Args:
            api_key: API key for authentication
            base_url: Base URL for custom Data Commons instance
            idx: Index to use for SV search
        """
        if not api_key or not base_url:
            raise ValueError("Must specify either api_key or base_url")

        self.dc_name = dc_name
        self.idx = idx
        self.base_url = base_url

        if api_key:
            self.dc = DataCommonsClient(api_key=api_key)
        else:
            self.dc = DataCommonsClient(url=f"{base_url}/core/api/v2/")

    async def search_places(self, names: list[str]) -> ResolvedPlaces:
        response = self.dc.resolve.fetch_dcids_by_name(names=names)
        resolved_places = ResolvedPlaces(query_to_place={})

        all_place_dcids = set()
        for dcids in response.to_flat_dict().values():
            if isinstance(dcids, list):
                all_place_dcids.update(dcids)
            else:
                all_place_dcids.add(dcids)

        dcid_to_names = self.fetch_entity_names(all_place_dcids)
        dcid_to_types = self.fetch_entity_types(all_place_dcids)
        dcid_to_ancestors = self.fetch_place_ancestors(all_place_dcids)

        for search_query, dcids in response.to_flat_dict().items():
            places = resolved_places.query_to_place.setdefault(search_query, [])
            if not isinstance(dcids, list):
                dcids = [dcids]  # noqa: PLW2901
            for dcid in dcids:
                places.append(
                    ResolvedPlace(
                        place_dcid=dcid,
                        place_name=dcid_to_names[dcid],
                        place_types=dcid_to_types[dcid],
                        located_in=dcid_to_ancestors[dcid],
                    )
                )

        return resolved_places

    async def fetch_obs(self, obs_request: ObservationRequest) -> ObservationResponse:
        if obs_request.place_dcids:
            return self.dc.observation.fetch_observations_by_entity_dcid(
                date=obs_request.date,
                entity_dcids=obs_request.place_dcids,
                variable_dcids=obs_request.variable_dcids,
                filter_facet_ids=obs_request.facet_ids,
            )
        return self.dc.observation.fetch_observations_by_entity_type(
            date=obs_request.date,
            parent_entity=obs_request.parent_place_dcid,
            entity_type=obs_request.child_place_type_dcid,
            variable_dcids=obs_request.variable_dcids,
            filter_facet_ids=obs_request.facet_ids,
        )

    def fetch_entity_names(self, dcids: list[str]) -> dict:
        response = self.dc.node.fetch_entity_names(entity_dcids=dcids)
        return {dcid: name.value for dcid, name in response.items()}

    def fetch_entity_types(self, dcids: list[str]) -> dict:
        response = self.dc.node.fetch_property_values(
            node_dcids=dcids, properties="typeOf"
        )
        return {
            dcid: list(response.extract_connected_dcids(dcid, "typeOf"))
            for dcid in response.get_properties()
        }

    def fetch_place_ancestors(self, dcids: list[str]) -> dict:
        response = self.dc.node.fetch_place_ancestors(dcids)
        dcid_to_ancestors = {}
        for child_place, ancestors in response.items():
            found_ancestors = dcid_to_ancestors.setdefault(child_place, set())
            for ancestor in ancestors:
                found_ancestors.add(ancestor.get("name", ""))
                if "Country" in ancestor.get("types"):
                    break
        return dcid_to_ancestors

    def add_place_metadata_to_obs(self, obs_response: ObservationFacetResponse) -> None:
        all_place_dcids = list(obs_response.place_data.keys())
        names = self.fetch_entity_names(all_place_dcids)
        for place_dcid, name in names.items():
            obs_response.place_data[place_dcid].place_name = name

    async def search_svs(self, queries: list[str], *, skip_topics: bool = True) -> dict:
        results_map = {}
        skip_topics_param = "&skip_topics=true" if skip_topics else ""
        endpoint_url = f"{self.base_url}/api/nl/search-vector"
        api_endpoint = f"{endpoint_url}?idx={self.idx}{skip_topics_param}"
        headers = {"Content-Type": "application/json"}

        for query in queries:
            payload = {"queries": [query]}
            try:
                response = requests.post(
                    api_endpoint,
                    data=json.dumps(payload),
                    headers=headers,
                    timeout=DEFAULT_API_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("queryResults", {})

                if (
                    query in results
                    and "SV" in results[query]
                    and "CosineScore" in results[query]
                ):
                    sv_list = results[query]["SV"]
                    score_list = results[query]["CosineScore"]
                    sorted_results = sorted(
                        zip(sv_list, score_list, strict=True),
                        key=lambda x: (-x[1], x[0]),
                    )
                    sv_list, score_list = zip(*sorted_results, strict=True)

                    # Assuming len(sv_list) == len(score_list) as per user prompt
                    # Iterate up to the top 5, or fewer if less than 5 results are available.
                    num_results_available = len(sv_list)
                    num_results_to_take = min(num_results_available, 5)

                    top_results = [
                        {"SV": sv_list[i], "CosineScore": score_list[i]}
                        for i in range(num_results_to_take)
                    ]

                    results_map[query] = top_results
                else:
                    # This case handles if the query is in the response, but SV/CosineScore is missing/empty
                    results_map[query] = []

            except Exception as e:  # noqa: BLE001
                print(f"An unexpected error occurred for query '{query}': {e}")
                results_map[query] = []
        return results_map

    async def get_child_place_type_dcids(
        self,
        parent_place_dcid: str,
    ) -> bool:
        all_admin_areas = list(
            self.dc.node.fetch_property_values(
                node_dcids="AdministrativeArea", properties="subClassOf", out=False
            ).extract_connected_dcids("AdministrativeArea", "subClassOf")
        )
        valid_admin_areas = []
        for admin_area in all_admin_areas:
            response = self.dc.node.fetch_place_children(
                place_dcids=parent_place_dcid,
                children_type=admin_area,
                as_dict=True,
            )
            if len(response.get(parent_place_dcid, [])) > 0:
                valid_admin_areas.append(admin_area)
        return valid_admin_areas


class MultiDCClient:
    def __init__(self, base_dc: DCClient, custom_dcs: list[DCClient]) -> None:
        self.base_dc = base_dc
        self.custom_dcs = custom_dcs
        # Map DC IDs to DCClient instances
        self.dc_map = {
            BASE_DC_ID: base_dc,
            **{client.base_url: client for client in custom_dcs},
        }
        self.min_custom_score = 0.7
        # For the DC federation case (i.e. more than one custom DC), raise the threshold to 0.8
        if self.custom_dcs and len(self.custom_dcs) >= 2:
            self.min_custom_score = 0.8

        self.variable_to_custom_source = {}

    async def search_svs(self, queries: list[str]) -> dict:
        """
        Search for SVs across all DC instances.

        Returns:
            A dictionary where:
            - keys are the input queries
            - values are dictionaries containing:
                - 'SV': The selected SV
                - 'CosineScore': The score of the SV
                - 'dc_id': The ID of the DC that provided the SV
        """
        results = {}

        # Search across all DCs in parallel
        all_results = await asyncio.gather(
            *[dc.search_svs(queries) for dc in [self.base_dc] + self.custom_dcs]
        )

        for query in queries:
            # Find the best SV from custom DCs first
            # TODO(clincoln8): Change this top X instead of only the top.
            # Include names + description + other metadata.
            best_custom_result = None
            best_custom_score = self.min_custom_score

            for idx, dc_results in enumerate(
                all_results[1:], 1
            ):  # Skip base DC results
                if query in dc_results:
                    for result in dc_results[query]:
                        if result["CosineScore"] > best_custom_score:
                            best_custom_score = result["CosineScore"]
                            best_custom_result = {
                                "SV": result["SV"],
                                "CosineScore": result["CosineScore"],
                                "dc_id": self.custom_dcs[idx - 1].base_url,
                            }

            # If no good custom result, use base DC result
            if not best_custom_result:
                base_results = all_results[0]
                if query in base_results and base_results[query]:
                    best_result = {
                        "SV": base_results[query][0]["SV"],
                        "CosineScore": base_results[query][0]["CosineScore"],
                        "dc_id": BASE_DC_ID,
                    }
                else:
                    best_result = None
            else:
                best_result = best_custom_result

            results[query] = best_result

        return results

    async def fetch_obs(
        self, obs_request: ObservationRequest
    ) -> ObservationFacetResponse:
        all_client_results = await asyncio.gather(
            *[dc.fetch_obs(obs_request) for dc in [self.base_dc] + self.custom_dcs]
        )

        final_response = ObservationFacetResponse()

        base_dc_response = all_client_results[0]

        # First merge in facets specifc to custom clients.
        for custom_client, response in zip(
            self.custom_dcs, all_client_results[1:], strict=True
        ):
            custom_facets = list(
                response.facets.keys() - base_dc_response.facets.keys()
            )
            if custom_facets:
                merge_obs_response(
                    final_response, response, custom_client.name, custom_facets
                )

        # Then merge in facets from base response
        merge_obs_response(final_response, base_dc_response, self.base_dc.dc_name)

        self.base_dc.add_place_metadata_to_obs(final_response)
        return final_response


def create_clients(config: ClientConfig) -> MultiDCClient:
    """
    Factory function to create MultiDCClient based on configuration.
    """
    base_config = config.base
    custom_configs = config.custom_dcs

    # Create base DC client
    base_dc = DCClient(
        dc_name=base_config.name,
        api_key=base_config.api_key,
        idx=base_config.embeddings_index_name,
        base_url=base_config.base_url,
    )

    # Create custom DC clients
    custom_dcs = [
        DCClient(
            dc_name=custom_config.name,
            base_url=custom_config.base_url,
            idx=custom_config.embeddings_index_name,
        )
        for custom_config in custom_configs
    ]

    return MultiDCClient(base_dc, custom_dcs)


def merge_obs_response(
    final_response: ObservationFacetResponse,
    api_response: ObservationResponse,
    api_client_id: str,
    selected_facet_ids: list[str] | None = None,
) -> None:
    flattened_api_response = api_response.get_data_by_entity()
    for variable_dcid, api_variable_data in flattened_api_response.items():
        for place_dcid, api_place_data in api_variable_data.items():
            # Get or initialize the place_data entry in final response
            if place_dcid not in final_response.place_data:
                final_response.place_data[place_dcid] = PlaceData(place_dcid=place_dcid)
            place_data = final_response.place_data[place_dcid]

            first_obs = None
            sources = []

            for facet in api_place_data.orderedFacets:
                if selected_facet_ids and facet not in selected_facet_ids:
                    continue

                facet_metadata = api_response.facets.get(facet.facetId)
                metadata = SourceMetadata(
                    **facet_metadata.to_dict(),
                    dc_client_id=api_client_id,
                    earliest_date=facet.earliestDate,
                    latest_date=facet.latestDate,
                    total_observations=facet.obsCount,
                )
                sources.append(metadata)
                if not first_obs:
                    first_obs = facet.observations

            # Append alternative sources to an existing variable series
            if variable_dcid in place_data.variable_series:
                place_data.variable_series[variable_dcid].alternative_sources.extend(
                    sources
                )
            # Otherwise create a new variable series with the first facet as the
            # primary one.
            else:
                if first_obs and sources:
                    place_data.variable_series[variable_dcid] = VariableSeries(
                        variable_dcid=variable_dcid,
                        source_metadata=sources[0],
                        observations=first_obs,
                        alternative_sources=sources[1:],
                    )
