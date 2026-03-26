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

from loguru import logger
from osc_client import cast_model, dump_data
from osc_client.models import OscStatus, WorkflowProperties
from pathlib import Path
from transpiler_mate.ogcapi_records.ogcapi_records_models import Link, RecordGeoJSON


def execute(source: str, record_geojson: RecordGeoJSON, project: str, output: Path):
    logger.debug(f"Enriching OGCP API Records...")

    record_geojson.links.append(  # type: ignore see osc_client.load_record_geojson
        Link(
            rel="parent",
            href="../catalog.json",
            type="application/json",
            title="Workflows",
            hreflang="en-US",
            created=None,
            updated=None,
        )
    )
    record_geojson.links.append(  # type: ignore see osc_client.load_record_geojson
        Link(
            href=source,
            hreflang="en-US",
            rel="application",
            type="application/cwl",
            title=record_geojson.properties.title,
            created=record_geojson.properties.created,
            updated=record_geojson.properties.created,
        )
    )
    record_geojson.links.append(  # type: ignore see osc_client.load_record_geojson
        Link(
            href="https://cwltool.readthedocs.io/en/latest/",
            hreflang="en-US",
            rel="application-platform",
            type="text/html",
            title="cwltool",
            created=None,
            updated=None,
        )
    )

    record_geojson.properties.type = "workflow"
    workflow_properties: WorkflowProperties = cast_model(
        record_geojson.properties,
        WorkflowProperties,
    )
    workflow_properties.osc_project = project
    workflow_properties.osc_status = OscStatus.COMPLETED
    record_geojson.properties = workflow_properties

    logger.success(f"OGCP API Records enriched")

    dump_data(
        record_geojson.model_dump(
            by_alias=True, exclude_none=True, serialize_as_any=True
        ),
        Path(output, f"workflows/{record_geojson.id}/record.json"),
    )
