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
from io import BytesIO, TextIOWrapper
from loguru import logger
from ogc_api_processes_client.api_client import ApiClient
from ogc_api_processes_client.api.status_api import StatusApi
from ogc_api_processes_client.configuration import Configuration
from ogc_api_processes_client.models.inline_or_ref_data import InlineOrRefData
from ogc_api_processes_client.models.status_code import StatusCode
from ogc_api_processes_client.models.status_info import StatusInfo
from pathlib import Path
from pydantic import BaseModel
from requests import Session
from requests.adapters import BaseAdapter, HTTPAdapter
from session_adapters.file_adapter import FileAdapter
from session_adapters.http_conts import DEFAULT_ENCODING
from session_adapters.oci_adapter import OCIAdapter
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Mapping, TypeVar
from transpiler_mate.metadata import MetadataManager
from transpiler_mate.metadata.software_application_models import SoftwareApplication
from transpiler_mate.ogcapi_records import OgcRecordsTranspiler
from transpiler_mate.ogcapi_records.ogcapi_records_models import RecordGeoJSON
from typing import Any

import yaml
import json
import time

PENDING = {"accepted", "running"}

def create_client(ogc_api_endpoint: str, authorization_token: str | None) -> ApiClient:
    return ApiClient(
        configuration=Configuration(
            host=ogc_api_endpoint,
        ),
        header_name="Authorization" if authorization_token else None,
        header_value=f"Bearer {authorization_token}" if authorization_token else None,
    )


def retrieve_status_info(api_client: ApiClient, job_id: str) -> StatusInfo:
    status_api = StatusApi(api_client=api_client)

    logger.debug(f"Retrieving the Job {job_id} status...")

    status_info: StatusInfo | None = None
    while status_info is None or status_info.status in PENDING:
        time.sleep(10)

        status_info = status_api.get_status(job_id=job_id)

        logger.debug(f"Job {job_id} status is {status_info.status}")

    if StatusCode.SUCCESSFUL != status_info.status:
        raise Exception(
            f"Impossible to create the OGC API Records 'Experiment', job '{job_id}' terminated with status '{status_info.status}', report to your provider"
        )

    logger.success(f"Job {job_id} execution is complete.")
    return status_info


def load_record_geojson(source: str) -> RecordGeoJSON:
    session: Session = Session()

    def mount_session(scheme: str, adapter: BaseAdapter):
        logger.debug(f"Mounting '{scheme}' scheme to '{type(adapter).__name__}'...")
        session.mount(scheme, adapter)
        logger.debug(
            f"Scheme '{scheme}' successfully mount to '{type(adapter).__name__}'"
        )

    http_adapter = HTTPAdapter()
    mount_session("http://", http_adapter)
    mount_session("https://", http_adapter)
    mount_session("file://", FileAdapter())
    mount_session("oci://", OCIAdapter())

    logger.debug(f"> GET {source}...")

    response = session.get(source, stream=True)
    response.raise_for_status()

    logger.debug(f"< {response.status_code} {response.reason}")
    for k, v in response.headers.items():
        logger.debug(f"< {k}: {v}")

    # Read first 2 bytes to check for gzip
    magic = response.raw.read(2)
    remaining = response.raw.read()  # Read rest of the stream
    combined = BytesIO(magic + remaining)

    if b"\x1f\x8b" == magic:
        logger.debug(f"gzip compression detected in response body from {source}")
        buffer = GzipFile(fileobj=combined)
    else:
        buffer = combined

    input_stream = TextIOWrapper(buffer, encoding=DEFAULT_ENCODING)

    fd = NamedTemporaryFile(mode="w", suffix=".cwl", encoding=DEFAULT_ENCODING)

    try:
        tmp_path = Path(fd.name)

        logger.debug(
            f"Caching the CWL document to a temporary file on {tmp_path.absolute()}..."
        )

        with tmp_path.open("w") as output_stream:
            output_stream.write(input_stream.read())

        logger.success(f"CWL document stored to {tmp_path.absolute()} temporary file.")

        logger.debug(
            f"Reading Schema.org metadata from CWL document on {tmp_path.absolute()}..."
        )

        manager: MetadataManager = MetadataManager(tmp_path)
        metadata: SoftwareApplication = manager.metadata

        logger.success(
            f"Schema.org metadata read from CWL document on {tmp_path.absolute()}."
        )

        logger.debug(f"Transpiling Schema.org metadata to OGCP API Records...")

        transpiler: OgcRecordsTranspiler = OgcRecordsTranspiler()

        data: Mapping[str, Any] = transpiler.transpile(metadata)

        record_geojson: RecordGeoJSON = RecordGeoJSON.model_validate(
            obj=data, by_alias=True
        )

        if not record_geojson.links:
            record_geojson.links = []

        logger.success(f"Schema.org metadata transpiled to OGCP API Records.")

        return record_geojson
    finally:
        fd.close()


T = TypeVar("T", bound=BaseModel)


def cast_model(src: BaseModel, dst_cls: type[T]) -> T:
    # mode="python" preserves datetimes, URLs, etc.
    data = src.model_dump(mode="python", by_alias=True, exclude_none=False)
    return dst_cls.model_validate(data, by_alias=True)


def save_record_geojson(record_geojson: RecordGeoJSON, output: Path):
    logger.info(f"Serializing OGC API Records 'Experiment' to {output.absolute()}...")

    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w") as output_stream:
        json.dump(
            record_geojson.model_dump(
                by_alias=True, exclude_none=True, serialize_as_any=True
            ),
            output_stream,
            indent=2,
        )

    logger.success(f"OGC API Records 'Experiment' serialized to {output.absolute()}.")


def serialize_yaml(data: Any, target_file: Path):
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with target_file.open("w") as output_stream:
        yaml.dump(
            data,
            output_stream,
        )
