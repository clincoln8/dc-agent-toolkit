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

from pydantic import BaseModel, Field


class ResolvedPlace(BaseModel):
    place_dcid: str
    place_name: str = Field(default_factory=str)
    place_types: list[str] = Field(default_factory=list)
    located_in: list[str] = Field(default_factory=list)


class ResolvedPlaces(BaseModel):
    query_to_place: dict[str, list[ResolvedPlace]] = Field(default_factory={})
