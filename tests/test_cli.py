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

from pathlib import Path

from click.testing import CliRunner

from transpiler_mate.ogcapi_records.ogcapi_records_models import (
    RecordCommonProperties,
    RecordGeoJSON,
)


def make_record(record_id: str) -> RecordGeoJSON:
    return RecordGeoJSON(
        id=record_id,
        properties=RecordCommonProperties(title="Record"),
        links=[],
    )


def test_main_loads_context(monkeypatch, tmp_path, osc_modules) -> None:
    cli = osc_modules["cli"]
    runner = CliRunner()
    record = make_record("original-id")
    called = {}

    monkeypatch.setattr(
        cli, "load_record_geojson", lambda source, project_id, project_name: record
    )
    monkeypatch.setattr(
        cli,
        "execute_workflow",
        lambda source, ogc_api_processes_endpoint, record_geojson, project_id, output: (
            called.update(
                source=source,
                ogc_api_processes_endpoint=ogc_api_processes_endpoint,
                record_geojson=record_geojson,
                project_id=project_id,
                output=output,
            )
        ),
    )

    result = runner.invoke(
        cli.main,
        [
            "--id",
            "workflow-1",
            "--project-id",
            "project-1",
            "--project-name",
            "Project",
            "--ogc-api-processes-endpoint",
            "https://example.com/processes",
            "--output",
            str(tmp_path),
            "https://example.com/workflow.cwl",
            "workflow",
        ],
    )

    assert result.exit_code == 0
    assert called["source"] == "https://example.com/workflow.cwl"
    assert called["ogc_api_processes_endpoint"] == "https://example.com/processes"
    assert called["record_geojson"].id == "workflow-1"
    assert called["project_id"] == "project-1"
    assert called["output"] == Path(tmp_path)


def test_experiment_command_dispatches(monkeypatch, tmp_path, osc_modules) -> None:
    cli = osc_modules["cli"]
    runner = CliRunner()
    record = make_record("experiment-1")
    called = {}

    monkeypatch.setattr(
        cli, "load_record_geojson", lambda source, project_id, project_name: record
    )
    monkeypatch.setattr(
        cli,
        "execute_experiment",
        lambda **kwargs: called.update(kwargs),
    )

    result = runner.invoke(
        cli.main,
        [
            "--id",
            "experiment-1",
            "--project-id",
            "project-1",
            "--project-name",
            "Project",
            "--ogc-api-processes-endpoint",
            "https://example.com/processes",
            "--output",
            str(tmp_path),
            "https://example.com/workflow.cwl",
            "experiment",
            "--workflow-id",
            "workflow-1",
            "--authorization-token",
            "token",
        ],
    )

    assert result.exit_code == 0
    assert called["project_id"] == "project-1"
    assert called["workflow_id"] == "workflow-1"
    assert called["ogc_api_processes_endpoint"] == "https://example.com/processes"
    assert called["record_geojson"].id == "experiment-1"
    assert called["output"] == Path(tmp_path)
    assert called["authorization_token"] == "token"


def test_products_command_dispatches(monkeypatch, tmp_path, osc_modules) -> None:
    cli = osc_modules["cli"]
    runner = CliRunner()
    record = make_record("product-1")
    called = {}

    monkeypatch.setattr(
        cli, "load_record_geojson", lambda source, project_id, project_name: record
    )
    monkeypatch.setattr(
        cli,
        "execute_product",
        lambda *args: called.update(
            endpoint=args[0],
            record_geojson=args[1],
            project_id=args[2],
            experiment_id=args[3],
            output=args[4],
            authorization_token=args[5],
        ),
    )

    result = runner.invoke(
        cli.main,
        [
            "--id",
            "product-1",
            "--project-id",
            "project-1",
            "--project-name",
            "Project",
            "--ogc-api-processes-endpoint",
            "https://example.com/processes",
            "--output",
            str(tmp_path),
            "https://example.com/workflow.cwl",
            "products",
            "--experiment-id",
            "experiment-1",
            "--authorization-token",
            "token",
        ],
    )

    assert result.exit_code == 0
    assert called["endpoint"] == "https://example.com/processes"
    assert called["record_geojson"].id == "product-1"
    assert called["project_id"] == "project-1"
    assert called["experiment_id"] == "experiment-1"
    assert called["output"] == Path(tmp_path)
    assert called["authorization_token"] == "token"
