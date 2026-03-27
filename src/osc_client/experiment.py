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
from osc_client import (
    cast_model,
    create_client,
    retrieve_status_info,
    dump_data,
    serialize_yaml,
)
from ogc_api_processes_client.models.status_info import StatusInfo
from osc_client.models import ExperimentProperties
from pathlib import Path
from transpiler_mate.ogcapi_records.ogcapi_records_models import Link, RecordGeoJSON


def execute(
    project_id: str,
    workflow_id: str,
    record_geojson: RecordGeoJSON,
    ogc_api_processes_endpoint: str,
    output: Path,
    authorization_token: str,
):
    logger.debug(f"Enriching OGCP API Records...")

    record_geojson.links.append(  # type: ignore see osc_client.load_record_geojson
        Link(
            rel="parent",
            href="../catalog.json",
            type="application/json",
            title="Experiments",
            hreflang="en-US",
            created=None,
            updated=None,
        )
    )

    logger.debug("Reassembling OGC API Records 'Experiment' inputs...")

    status_info: StatusInfo = retrieve_status_info(
        create_client(ogc_api_processes_endpoint, authorization_token),
        record_geojson.id,
    )

    logger.debug(status_info.properties)

    target_file = Path(output, f"experiments/{record_geojson.id}/record.json")
    input_files: Path = Path(target_file.parent, "input.yaml")

    serialize_yaml(status_info.inputs, input_files)

    record_geojson.links.append(  # type: ignore see osc_client.load_record_geojson
        Link(
            href=f"./{input_files.name}",
            hreflang="en-US",
            rel="input",
            type="application/yaml",
            title="Input parameters",
            created=status_info.started,
            updated=status_info.started,
        )
    )

    logger.success(
        f"OGC API Records 'Experiment' inputs saved to {input_files.absolute()}"
    )

    record_geojson.properties.type = "experiment"
    experiment_properties: ExperimentProperties = cast_model(
        record_geojson.properties,
        ExperimentProperties,
    )
    experiment_properties.osc_project = project_id
    experiment_properties.osc_workflow = workflow_id
    experiment_properties.osc_prov_described_by_workflow = workflow_id
    # experiment_properties.osc_prov_generated = "TODO"
    experiment_properties.osc_prov_generated_by = "osc-client"
    experiment_properties.osc_prov_started_at_time = status_info.started
    experiment_properties.osc_prov_ended_at_time = status_info.finished

    record_geojson.properties = experiment_properties

    logger.success(f"OGCP API Records enriched")

    dump_data(
        record_geojson.model_dump(
            by_alias=True, exclude_none=True, serialize_as_any=True
        ),
        target_file,
    )
