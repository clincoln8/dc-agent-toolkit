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

from datacommons.mcp.constants import FETCH_DATE_ALL
from datacommons_client.models.observation import Facet, Observation
from pydantic import BaseModel, Field, model_validator


class ObservationRequest(BaseModel):
    variable_dcids: list[str]
    place_dcids: list[str] | None = None
    parent_place_dcid: str | None = None
    child_place_type_dcid: str | None = None
    facet_ids: list[str] | None = None
    date: str = FETCH_DATE_ALL

    @model_validator(mode="after")
    def check_place_definition(self) -> "ObservationRequest":
        """Ensures that either 'place_dcids' or the parent/child pair is provided,but not both."""
        has_dcids = bool(self.place_dcids)
        has_pair = bool(self.parent_place_dcid and self.child_place_type_dcid)

        if has_dcids == has_pair:
            raise ValueError(
                "Supply EITHER a list of place_dcids OR a complete (parent_place_dcid, child_place_type_dcid) pair."
            )

        return self


class SourceMetadata(Facet):
    dc_client_id: str
    earliest_date: str
    latest_date: str
    total_observations: int


class VariableSeries(BaseModel):
    variable_dcid: str
    source_metadata: SourceMetadata
    observations: list[Observation]
    alternative_sources: list[SourceMetadata] = Field(default_factory=list)


class PlaceData(BaseModel):
    place_dcid: str = Field(default_factory=str)
    place_name: str = Field(default_factory=str)
    variable_series: dict[str, VariableSeries] = Field(default_factory=dict)


class ObservationFacetResponse(BaseModel):
    place_data: dict[str, PlaceData] = Field(default_factory=dict)
