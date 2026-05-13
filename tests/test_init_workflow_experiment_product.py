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

from __future__ import annotations

import gzip
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pystac

from transpiler_mate.ogcapi.records.ogcapi_records_models import (
    Language,
    Link,
    RecordCommonProperties,
    RecordGeoJSON,
)


def make_record(record_id: str, title: str = "Record") -> RecordGeoJSON:
    return RecordGeoJSON(
        id=record_id,
        properties=RecordCommonProperties(
            title=title,
            description=f"{title} description",
            created=datetime(2026, 1, 1, tzinfo=timezone.utc),
            keywords=["land"],
            license="CC-BY-4.0",
        ),
        links=[],
    )


def test_create_client_sets_bearer_header(osc_modules) -> None:
    package = osc_modules["package"]

    client = package.create_client("https://example.com", "secret-token")

    assert client.configuration.host == "https://example.com"
    assert client.header_name == "Authorization"
    assert client.header_value == "Bearer secret-token"


def test_retrieve_status_info_polls_until_success(monkeypatch, osc_modules) -> None:
    package = osc_modules["package"]
    status_code = package.StatusCode
    responses = iter(
        [
            package.StatusInfo(status=status_code.ACCEPTED),
            package.StatusInfo(status=status_code.RUNNING),
            package.StatusInfo(status=status_code.SUCCESSFUL),
        ]
    )

    class FakeStatusApi:
        def __init__(self, api_client):
            self.api_client = api_client

        def get_status(self, job_id):
            return next(responses)

    monkeypatch.setattr(package, "StatusApi", FakeStatusApi)
    monkeypatch.setattr(package.time, "sleep", lambda _: None)

    status = package.retrieve_status_info(object(), "job-1")

    assert status.status == status_code.SUCCESSFUL


def test_retrieve_status_info_raises_on_failure(monkeypatch, osc_modules) -> None:
    package = osc_modules["package"]

    class FakeStatusApi:
        def __init__(self, api_client):
            self.api_client = api_client

        def get_status(self, job_id):
            return package.StatusInfo(status=package.StatusCode.FAILED)

    monkeypatch.setattr(package, "StatusApi", FakeStatusApi)
    monkeypatch.setattr(package.time, "sleep", lambda _: None)

    try:
        package.retrieve_status_info(object(), "job-1")
    except Exception as exc:
        assert "terminated with status" in str(exc)
    else:
        raise AssertionError("Expected failure for unsuccessful status")


def test_serialize_yaml_writes_file(tmp_path, osc_modules) -> None:
    package = osc_modules["package"]
    target = tmp_path / "nested" / "data.yaml"

    package.serialize_yaml({"answer": 42}, target)

    assert target.exists()
    assert "answer: 42" in target.read_text()


def test_dump_data_writes_json_and_updates_catalog(tmp_path, osc_modules) -> None:
    package = osc_modules["package"]
    catalog_path = tmp_path / "records" / "catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog = pystac.Catalog(id="root", description="Root")
    catalog.save_object(dest_href=catalog_path.as_posix(), include_self_link=False)

    output = tmp_path / "records" / "abc" / "record.json"
    package.dump_data(
        {"id": "abc", "properties": {"title": "Record title"}},
        output,
    )

    assert output.exists()
    updated_catalog = pystac.Catalog.from_file(catalog_path.as_posix())
    hrefs = [link.get_href() for link in updated_catalog.links]
    assert "./abc/record.json" in hrefs


def test_dump_data_does_not_duplicate_existing_catalog_link(
    tmp_path, osc_modules
) -> None:
    package = osc_modules["package"]
    catalog_path = tmp_path / "records" / "catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog = pystac.Catalog(id="root", description="Root")
    catalog.add_link(
        pystac.Link(
            rel=pystac.RelType.ITEM,
            target="./abc/record.json",
            media_type="application/json",
            title="Record title",
        )
    )
    catalog.save_object(dest_href=catalog_path.as_posix(), include_self_link=False)

    output = tmp_path / "records" / "abc" / "record.json"
    package.dump_data(
        {"id": "abc", "properties": {"title": "Record title"}},
        output,
    )

    updated_catalog = pystac.Catalog.from_file(catalog_path.as_posix())
    hrefs = [link.get_href() for link in updated_catalog.links]
    assert hrefs.count("./abc/record.json") == 1


def test_load_record_geojson_enriches_transpiled_record(
    monkeypatch, osc_modules
) -> None:
    package = osc_modules["package"]

    class FakeResponse:
        status_code = 200
        reason = "OK"
        headers = {"Content-Type": "application/cwl"}

        def __init__(self, payload: bytes):
            self.raw = BytesIO(payload)

        def raise_for_status(self):
            return None

    class FakeSession:
        def __init__(self):
            self.mounted = {}

        def mount(self, scheme, adapter):
            self.mounted[scheme] = adapter

        def get(self, source, stream=True):
            return FakeResponse(gzip.compress(b"class: Command\n"))

    record = RecordGeoJSON(
        id="workflow-1",
        properties=RecordCommonProperties(
            title="Workflow",
            language=Language(code="en", name="English"),
            resourceLanguages=[Language(code="it", name="Italian")],
        ),
        links=[],
    )

    class FakeMetadataManager:
        def __init__(self, path):
            self.path = path
            self.metadata = SimpleNamespace(name="metadata")

    class FakeTranspiler:
        def transpile(self, metadata):
            return record.model_dump(by_alias=True, exclude_none=True)

    monkeypatch.setattr(package, "Session", FakeSession)
    monkeypatch.setattr(package, "MetadataManager", FakeMetadataManager)
    monkeypatch.setattr(package, "OgcRecordsTranspiler", FakeTranspiler)
    monkeypatch.setattr(package, "OCIAdapter", lambda: object())

    loaded = package.load_record_geojson(
        "https://example.com/workflow.cwl", "proj", "Project"
    )

    assert loaded.geometry.type == "MultiPoint"
    assert loaded.properties.language.alternate == "English"
    assert loaded.properties.languages[0].alternate == "English"
    assert loaded.properties.resource_languages[0].alternate == "Italian"
    assert loaded.links[-2].href == "../../projects/proj/collection.json"
    assert loaded.links[-1].href == "../../catalog.json"


def test_workflow_execute_enriches_and_serializes(
    monkeypatch, tmp_path, osc_modules
) -> None:
    workflow = osc_modules["workflow"]
    record = make_record("workflow-1", "Workflow")
    dumped = {}

    monkeypatch.setattr(
        workflow, "dump_data", lambda data, path: dumped.update(data=data, path=path)
    )

    workflow.execute(
        "https://example.com/workflow.cwl",
        "https://example.com/processes",
        record,
        "project-1",
        tmp_path,
    )

    assert record.properties.osc_project == "project-1"
    assert record.properties.osc_status == workflow.OscStatus.COMPLETED
    assert any(link.rel == "application" for link in record.links)
    assert any(link.rel == "via" for link in record.links)
    assert dumped["path"] == Path(tmp_path, "workflows/workflow-1/record.json")
    assert dumped["data"]["properties"]["osc:project"] == "project-1"


def test_experiment_execute_enriches_and_serializes(
    monkeypatch, tmp_path, osc_modules
) -> None:
    experiment = osc_modules["experiment"]
    package = osc_modules["package"]
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    finished = datetime(2026, 1, 2, tzinfo=timezone.utc)
    record = make_record("experiment-1", "Experiment")
    dumped = {}
    serialized = {}

    monkeypatch.setattr(
        experiment, "create_client", lambda endpoint, token: ("client", endpoint, token)
    )
    monkeypatch.setattr(
        experiment,
        "retrieve_status_info",
        lambda client, job_id: experiment.StatusInfo(
            status=package.StatusCode.SUCCESSFUL,
            started=started,
            finished=finished,
            inputs={"region": "europe"},
            properties={"key": "value"},
        ),
    )
    monkeypatch.setattr(
        experiment,
        "serialize_yaml",
        lambda data, path: serialized.update(data=data, path=path),
    )
    monkeypatch.setattr(
        experiment,
        "dump_data",
        lambda data, path: dumped.update(data=data, path=path),
    )

    experiment.execute(
        project_id="project-1",
        workflow_id="workflow-1",
        record_geojson=record,
        ogc_api_processes_endpoint="https://example.com/processes",
        output=tmp_path,
        authorization_token="token",
    )

    assert serialized["data"] == {"region": "europe"}
    assert serialized["path"] == Path(tmp_path, "experiments/experiment-1/input.yaml")
    assert record.properties.osc_project == "project-1"
    assert record.properties.osc_workflow == "workflow-1"
    assert record.properties.osc_prov_generated_by == "osc-client"
    assert record.properties.osc_prov_started_at_time == started
    assert record.properties.osc_prov_ended_at_time == finished
    assert any(link.rel == "environment" for link in record.links)
    assert dumped["path"] == Path(tmp_path, "experiments/experiment-1/record.json")


def test_product_execute_builds_collection_and_serializes(
    monkeypatch, tmp_path, osc_modules
) -> None:
    product = osc_modules["product"]
    package = osc_modules["package"]
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    finished = datetime(2026, 1, 2, tzinfo=timezone.utc)
    record = make_record("product-1", "Product")
    record.links = [
        Link(
            rel="about",
            href="https://example.com/about",
            type="text/html",
            title="About",
        )
    ]
    dumped = {}
    serialized = {}

    monkeypatch.setattr(
        product, "create_client", lambda endpoint, token: ("client", endpoint, token)
    )
    monkeypatch.setattr(
        product,
        "retrieve_status_info",
        lambda api_client, job_id: product.StatusInfo(
            status=package.StatusCode.SUCCESSFUL,
            started=started,
            finished=finished,
        ),
    )

    class FakeResponse:
        def json(self):
            return {"output": "value"}

    class FakeResultApi:
        def __init__(self, api_client):
            self.api_client = api_client

        def get_result_without_preload_content(self, job_id):
            return FakeResponse()

    monkeypatch.setattr(product, "ResultApi", FakeResultApi)
    monkeypatch.setattr(
        product,
        "serialize_yaml",
        lambda data, path: serialized.update(data=data, path=path),
    )
    monkeypatch.setattr(
        product,
        "dump_data",
        lambda data, path, rel=None: dumped.update(data=data, path=path, rel=rel),
    )

    class FakeDatetime:
        @classmethod
        def now(cls):
            return datetime(2026, 1, 3, 12, 0, 0)

    monkeypatch.setattr(product, "datetime", FakeDatetime)

    product.execute(
        ogc_api_processes_endpoint="https://example.com/processes",
        record_geojson=record,
        project_id="project-1",
        experiment_id="experiment-1",
        output=tmp_path,
        authorization_token="token",
    )

    collection = pystac.Collection.from_dict(dumped["data"])
    osc_ext = product.OscExtension.ext(collection)
    themes_ext = product.ThemesExtension.ext(collection)

    assert serialized["data"] == {"output": "value"}
    assert serialized["path"] == Path(tmp_path, "products/product-1/output.yaml")
    assert collection.id == "product-1"
    assert osc_ext.project == "project-1"
    assert osc_ext.experiment == "experiment-1"
    assert osc_ext.status == product.OscStatus.COMPLETED
    assert themes_ext.themes is not None
    assert themes_ext.themes[0].concepts[0].id == "land"
    assert any(link.rel == "output" for link in collection.links)
    assert dumped["path"] == Path(tmp_path, "products/product-1/collection.json")
