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

from datetime import datetime
from loguru import logger
from ogc_api_client.api_client import ApiClient
from ogc_api_client.models.inline_or_ref_data import InlineOrRefData
from ogc_api_client.models.link import Link as OgcApiProcessesLink
from ogc_api_client.models.status_info import StatusInfo
from osc_client import (
    cast_model,
    create_client,
    retrieve_status_info,
    retrieve_results,
    save_record_geojson
)
from osc_client.models import ProductProperties
from pathlib import Path
from pydantic import AnyUrl
from typing import Dict
from transpiler_mate.ogcapi_records import _to_datetime
from transpiler_mate.ogcapi_records.ogcapi_records_models import (
    Link,
    RecordGeoJSON
)

def execute(
    source: str,
    ogc_api_endpoint: str,
    record_geojson: RecordGeoJSON,
    job_id: str,
    experiment_url: str,
    output: Path,
    authorization_token: str | None
):
    api_client: ApiClient = create_client(ogc_api_endpoint)

    status_info: StatusInfo = retrieve_status_info(
        api_client=api_client,
        job_id=job_id
    )

    results: Dict[str, InlineOrRefData] = retrieve_results(
        api_client=api_client,
        job_id=job_id,
        headers=headers
    )

    if not record_geojson.links:
        record_geojson.links = []

    for output_value in results.values():
        if isinstance(output_value, OgcApiProcessesLink):
            record_geojson.links.append(
                Link(
                    href=AnyUrl(output_value.href),
                    hreflang=output_value.hreflang,
                    rel=output_value.rel,
                    type=output_value.type,
                    title=output_value.title,
                    created=_to_datetime(datetime.now()),
                    updated=_to_datetime(datetime.now())
                )
            )


    product_properties: ProductProperties = cast_model(
        record_geojson.properties,
        ProductProperties
    )
    product_properties.osc_experiment = experiment_url
    product_properties.osc_prov_was_derived_from = source
    product_properties.osc_prov_was_output_from = source

    record_geojson.properties = product_properties

    logger.success(f"OGCP API Records enriched")

    save_record_geojson(
        record_geojson,
        output
    )
