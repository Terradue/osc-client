# Copyright 2026 Terradue
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

from ogc_api_client.api_client import ApiClient
from ogc_api_client.api.process_description_api import ProcessDescriptionApi
from ogc_api_client.configuration import Configuration
from ogc_api_client.models.process import Process


def execute(
    ogc_api_endpoint: str,
    process_id: str
):
    client = ApiClient(
        configuration=Configuration(
            host=ogc_api_endpoint,
        )
    )
    process_description_api = ProcessDescriptionApi(api_client=client)

    process_description: Process | None = None
    while not process_description:
        process_description = process_description_api.get_process_description(process_id)
