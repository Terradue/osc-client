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
from pathlib import Path
from ogc_api_client.api_client import ApiClient
from ogc_api_client.api.status_api import StatusApi
from ogc_api_client.configuration import Configuration
from ogc_api_client.models.status_info import StatusInfo
from osc_client import (
    cast_model,
    save_record_geojson
)
from osc_client.models import ExperimentProperties
from pydantic import AnyUrl
from typing import Any
from transpiler_mate.ogcapi_records import _to_datetime
from transpiler_mate.ogcapi_records.ogcapi_records_models import (
    Link,
    RecordGeoJSON
)

import yaml
import time

PENDING = {"accepted", "running"}

SUCCEEDED = "succeeded"


def execute(
    source: str,
    workflow_url: str,
    record_geojson: RecordGeoJSON,
    ogc_api_endpoint: str,
    job_id: str,
    output: Path
):
    client = ApiClient(
        configuration=Configuration(
            host=ogc_api_endpoint,
        )
    )
    status_api = StatusApi(api_client=client)

    logger.debug(f"Retrieving the Job {job_id} status...")

    status_info: StatusInfo | None = None
    while status_info is None or status_info.status in PENDING:
        time.sleep(10)

        status_info = status_api.get_status(
            job_id=job_id
        )

        logger.debug(f"Job {job_id} status is {status_info.status}")

    if SUCCEEDED != status_info.status:
        raise Exception(f"Impossible to create the OGC API Records 'Experiment', job '{job_id}' terminated with status '{status_info.status}' on {ogc_api_endpoint}, report to your provider")

    logger.success(f"Job {job_id} execution is complete.")

    logger.debug(f"Enriching OGCP API Records...")
    
    workflow_link: Link = Link(
        href=AnyUrl(workflow_url),
        hreflang="en-US",
        rel="workflow",
        type="application/json",
        title=record_geojson.properties.title,
        created=record_geojson.properties.created,
        updated=record_geojson.properties.created
    )
    if record_geojson.links:
        record_geojson.links.append(
            workflow_link
        )
    else:
        record_geojson.links = [workflow_link]

    logger.debug("Reassembling OGC API Records 'Experiment' inputs...")

    record_geojson.links.append(
        Link(
            href=AnyUrl("./inputs.yaml"),
            hreflang="en-US",
            rel="input",
            type="application/yaml",
            title=f"Inputs for {record_geojson.properties.title}",
            created=_to_datetime(datetime.now()),
            updated=_to_datetime(datetime.now())
        )
    )

    input_files: Path = Path(
        output.parent,
        "inputs.yaml"
    )
    input_files.parent.mkdir(
        parents=True,
        exist_ok=True
    )
    with input_files.open("w") as output_stream:
        yaml.dump(
            getattr(status_info, "inputs") if hasattr(status_info, "inputs") else {},
            output_stream
        )

    logger.success(f"OGC API Records 'Experiment' inputs saved to {input_files.absolute()}")

    experiment_properties: ExperimentProperties = cast_model(
        record_geojson.properties,
        ExperimentProperties,
    )
    experiment_properties.osc_workflow = AnyUrl(source)
    experiment_properties.osc_prov_described_by_workflow = AnyUrl(workflow_url)
    experiment_properties.osc_prov_generated = "TODO"
    experiment_properties.osc_prov_generated_by = "osc-client"
    experiment_properties.osc_prov_started_at_time = status_info.started
    experiment_properties.osc_prov_ended_at_time = status_info.finished

    record_geojson.properties = experiment_properties

    logger.success(f"OGCP API Records enriched")

    save_record_geojson(
        record_geojson,
        output
    )
