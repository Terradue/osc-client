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
    dump_data,
    serialize_yaml,
)
from osc_client.osc_extension import OscExtension, OscStatus, OscType
from pathlib import Path
from pystac import (
    Asset,
    Collection,
    Extent,
    Link,
    RelType,
    SpatialExtent,
    TemporalExtent,
)
from typing import Dict
from transpiler_mate.ogcapi_records import _to_datetime
from transpiler_mate.ogcapi_records.ogcapi_records_models import RecordGeoJSON


def execute(
    source: str,
    ogc_api_processes_endpoint: str,
    record_geojson: RecordGeoJSON,
    experiment_id: str,
    output: Path,
    authorization_token: str | None,
):
    logger.debug(f"Enriching STAC Collection...")
    target_file = Path(output, f"products/{record_geojson.id}/collection.json")

    collection: Collection = Collection(
        id=record_geojson.id,
        title=record_geojson.properties.title,
        description=record_geojson.properties.description
        if record_geojson.properties.description
        else f"{record_geojson.id} Product",
        extent=Extent(
            spatial=SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            temporal=TemporalExtent(
                [[record_geojson.properties.created, record_geojson.properties.created]]
            ),
        ),
        license=record_geojson.properties.license
        if record_geojson.properties.license
        else "proprietary",
        keywords=record_geojson.properties.keywords,
    )

    if record_geojson.links:
        for original_link in record_geojson.links:
            collection.add_link(
                Link(
                    rel=original_link.rel if original_link.rel else RelType.ALTERNATE,
                    target=original_link.href,
                    media_type=original_link.type,
                    title=original_link.title,
                )
            )

    collection.add_link(
        Link(
            rel=RelType.PARENT,
            target="../catalog.json",
            media_type="application/json",
            title="Products",
        )
    )
    collection.add_link(
        Link(
            target=f"../../experiments/{experiment_id}/record.json",
            rel="related",
            media_type="application/json",
            title=record_geojson.properties.title,
        )
    )

    api_client: ApiClient = create_client(
        ogc_api_processes_endpoint, authorization_token
    )

    status_info: StatusInfo = retrieve_status_info(
        api_client=api_client, job_id=record_geojson.id
    )

    result_api: ResultApi = ResultApi(api_client)

    try:
        results: Dict[str, InlineOrRefData] = result_api.get_result(
            job_id=record_geojson.id,
        )

        for output_value in results.values():
            logger.debug(f"{type(output)}: {output.__dict__}")

            if isinstance(output_value, OgcApiProcessesLink):
                collection.add_link(
                    Link(
                        target=output_value.href,
                        rel=RelType.ITEM,
                        media_type=output_value.type,
                        title=output_value.title,
                    )
                )
    except Exception as e:
        logger.error(
            f"An error occurred while retrieving results for {ogc_api_processes_endpoint}/jobs/{record_geojson.id}/results: {e}"
        )

        response_data = result_api.get_result_without_preload_content(record_geojson.id)

        outputs_file: Path = Path(target_file.parent, "output.yaml")

        serialize_yaml(response_data.json(), outputs_file)

        collection.add_asset(
            "output",
            Asset(
                href=f"./{outputs_file.name}",
                title="Output parameter",
                media_type="application/yaml",
                description=f"{record_geojson.id} Outputs",
            ),
        )

    osc_ext: OscExtension = OscExtension.ext(collection, add_if_missing=True)
    osc_ext.experiment = experiment_id
    osc_ext.osc_type = OscType.PRODUCT
    osc_ext.status = OscStatus.COMPLETED

    logger.success(f"STAC Collection enriched")

    dump_data(collection.to_dict(), target_file, RelType.CHILD)
