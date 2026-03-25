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
from ogc_api_processes_client.api_client import ApiClient
from ogc_api_processes_client.api.result_api import ResultApi
from ogc_api_processes_client.models.inline_or_ref_data import InlineOrRefData
from ogc_api_processes_client.models.link import Link as OgcApiProcessesLink
from ogc_api_processes_client.models.status_info import StatusInfo
from osc_client import (
    cast_model,
    create_client,
    retrieve_status_info,
    save_record_geojson,
    serialize_yaml
)
from osc_client.models import ProductProperties
from pathlib import Path
from pydantic import AnyUrl
from typing import Dict
from transpiler_mate.ogcapi_records import _to_datetime
from transpiler_mate.ogcapi_records.ogcapi_records_models import Link, RecordGeoJSON


def execute(
    source: str,
    ogc_api_processes_endpoint: str,
    record_geojson: RecordGeoJSON,
    job_id: str,
    experiment_url: str,
    output: Path,
    authorization_token: str | None,
):
    logger.debug(f"Enriching OGCP API Records...")

    record_geojson.links.append(
        Link(
            href=AnyUrl(experiment_url),
            hreflang="en-US",
            rel="derived_from",
            type="application/json",
            title=record_geojson.properties.title,
            created=record_geojson.properties.created,
            updated=record_geojson.properties.created,
        )
    )

    api_client: ApiClient = create_client(
        ogc_api_processes_endpoint, authorization_token
    )

    status_info: StatusInfo = retrieve_status_info(api_client=api_client, job_id=job_id)

    result_api: ResultApi = ResultApi(api_client)

    if not record_geojson.links:
        record_geojson.links = []

    try:
        results: Dict[str, InlineOrRefData] = result_api.get_result(
            job_id=job_id,
        )

        for output_value in results.values():
            logger.debug(f"{type(output)}: {output.__dict__}")

            if isinstance(output_value, OgcApiProcessesLink):
                record_geojson.links.append(
                    Link(
                        href=AnyUrl(output_value.href),
                        hreflang=output_value.hreflang,
                        rel=output_value.rel,
                        type=output_value.type,
                        title=output_value.title,
                        created=_to_datetime(datetime.now()),
                        updated=_to_datetime(datetime.now()),
                    )
                )
    except Exception as e:
        logger.error(f"An error occurred while retrieving results for {ogc_api_processes_endpoint}/jobs/{job_id}/results: {e}")

        response_data = result_api.get_result_without_preload_content(job_id)

        outputs_file: Path = Path(output.parent, "outputs.yaml")

        serialize_yaml(response_data.json(), outputs_file)

        record_geojson.links.append(
            Link(
                href=AnyUrl(outputs_file.absolute().as_uri()),
                hreflang="en-US",
                rel="output",
                type="application/yaml",
                title=f"Results of {record_geojson.properties.title}",
                created=_to_datetime(datetime.now()),
                updated=_to_datetime(datetime.now()),
            )
        )

    product_properties: ProductProperties = cast_model(
        record_geojson.properties, ProductProperties
    )
    product_properties.osc_experiment = experiment_url
    product_properties.osc_prov_was_derived_from = source
    product_properties.osc_prov_was_output_from = source

    record_geojson.properties = product_properties

    logger.success(f"OGCP API Records enriched")

    save_record_geojson(record_geojson, output)
