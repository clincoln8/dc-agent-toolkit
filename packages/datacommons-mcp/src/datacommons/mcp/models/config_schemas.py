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


# A base configuration that includes common fields.
class BaseConfig(BaseModel):
    embeddings_index_name: str
    base_url: str
    name: str


# Configuration for the base Data Commons client.
class BaseDCClientConfig(BaseConfig):
    api_key: str

    # Override default value for base DC
    name: str = "Data Commons"
    # Override default value for base DC
    embeddings_index_name: str = "base_uae_mem"


# Configuration for custom Data Commons clients.
class CustomDCClientConfig(BaseConfig):
    # Override default value for base DC
    name: str = "Custom DC"


# The main client configuration.
class ClientConfig(BaseModel):
    base: BaseDCClientConfig
    custom_dcs: list[CustomDCClientConfig] = Field(default_factory=list)
