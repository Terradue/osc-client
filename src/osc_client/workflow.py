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
from osc_client import save_record_geojson
from pathlib import Path
from pydantic import AnyUrl
from transpiler_mate.ogcapi_records.ogcapi_records_models import (
    Link,
    RecordGeoJSON
)

def execute(
    source: str,
    record_geojson: RecordGeoJSON,
    output: Path
):
    logger.debug(f"Enriching OGCP API Records...")
    
    workflow_link: Link = Link(
        href=AnyUrl(source),
        hreflang="en-US",
        rel="service-desc",
        type="application/cwl",
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

    logger.success(f"OGCP API Records enriched")

    save_record_geojson(
        record_geojson,
        output
    )
