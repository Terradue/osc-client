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

from gzip import GzipFile
from io import (
    BytesIO,
    TextIOWrapper
)
from loguru import logger
from pathlib import Path
from requests import Session
from requests.adapters import HTTPAdapter
from session_adapters.file_adapter import FileAdapter
from session_adapters.http_conts import DEFAULT_ENCODING
from tempfile import NamedTemporaryFile
from typing import (
    Any,
    Mapping
)
from transpiler_mate.metadata import MetadataManager
from transpiler_mate.metadata.software_application_models import SoftwareApplication
from transpiler_mate.ogcapi_records import OgcRecordsTranspiler
from transpiler_mate.ogcapi_records.ogcapi_records_models import RecordGeoJSON

import json

def load_record_geojson(
    source: str
) -> RecordGeoJSON:
    session: Session = Session()
    http_adapter = HTTPAdapter()
    session.mount('http://', http_adapter)
    session.mount('https://', http_adapter)
    session.mount('file://', FileAdapter())

    logger.debug(f"> GET {source}...")

    response = session.get(source, stream=True)
    response.raise_for_status()

    logger.debug(f"< {response.status_code} {response.reason}")
    for k, v in response.headers.items():
        logger.debug(f"< {k}: {v}")

    # Read first 2 bytes to check for gzip
    magic = response.raw.read(2)
    remaining = response.raw.read() # Read rest of the stream
    combined = BytesIO(magic + remaining)

    if b'\x1f\x8b' == magic:
        logger.debug(f"gzip compression detected in response body from {source}")
        buffer = GzipFile(fileobj=combined)
    else:
        buffer = combined

    input_stream = TextIOWrapper(buffer, encoding=DEFAULT_ENCODING)

    fd = NamedTemporaryFile(
        mode="w",
        suffix=".cwl",
        encoding=DEFAULT_ENCODING
    )

    try:
        tmp_path = Path(fd.name)

        logger.debug(f"Caching the CWL document to a temporary file on {tmp_path.absolute()}...")

        with tmp_path.open("w") as output_stream:
            output_stream.write(input_stream.read())

        logger.success(f"CWL document stored to {tmp_path.absolute()} temporary file.")

        logger.debug(f"Reading Schema.org metadata from CWL document on {tmp_path.absolute()}...")

        manager: MetadataManager = MetadataManager(tmp_path)
        metadata: SoftwareApplication = manager.metadata

        logger.success(f"Schema.org metadata read from CWL document on {tmp_path.absolute()}.")

        logger.debug(f"Transpiling Schema.org metadata to OGCP API Records...")

        transpiler: OgcRecordsTranspiler = OgcRecordsTranspiler()

        data: Mapping[str, Any] = transpiler.transpile(metadata)

        record_geojson: RecordGeoJSON = RecordGeoJSON.model_validate(
            obj=data,
            by_alias=True
        )

        logger.success(f"Schema.org metadata transpiled to OGCP API Records.")

        return record_geojson
    finally:
        fd.close()


def save_record_geojson(
    record_geojson: RecordGeoJSON,
    output: Path
):
    logger.info(f"Serializing OGC API Records 'Experiment' to {output.absolute()}...")

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output.open('w') as output_stream:
        json.dump(
            record_geojson.model_dump(
                by_alias=True,
                exclude_none=True
            ),
            output_stream,
            indent=2
        )
    
    logger.success(f"OGC API Records 'Experiment' serialized to {output.absolute()}.")
