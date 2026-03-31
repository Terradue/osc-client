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

from datetime import datetime, timezone

import pystac

from transpiler_mate.ogcapi_records.ogcapi_records_models import RecordCommonProperties


def test_about_exposes_version(osc_modules) -> None:
    assert osc_modules["about"].__version__ == "0.1.0"


def test_workflow_properties_preserve_aliases(osc_modules) -> None:
    models = osc_modules["models"]

    workflow = models.WorkflowProperties(
        title="Workflow",
        osc_project="project-1",
        osc_status=models.OscStatus.COMPLETED,
    )

    data = workflow.model_dump(by_alias=True)

    assert data["osc:type"] == "workflow"
    assert data["osc:project"] == "project-1"
    assert data["osc:status"] == "completed"


def test_cast_model_converts_record_common_properties(osc_modules) -> None:
    package = osc_modules["package"]
    models = osc_modules["models"]

    src = RecordCommonProperties(title="Workflow", description="Description")

    casted = package.cast_model(src, models.WorkflowProperties)

    assert casted.title == "Workflow"
    assert casted.description == "Description"
    assert casted.osc_type == "workflow"


def test_experiment_properties_accept_alias_fields(osc_modules) -> None:
    models = osc_modules["models"]
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ended = datetime(2026, 1, 2, tzinfo=timezone.utc)

    experiment = models.ExperimentProperties.model_validate(
        {
            "title": "Experiment",
            "osc:project": "project-1",
            "osc:workflow": "workflow-1",
            "osc-prov:generatedBy": "osc-client",
            "osc-prov:startedAtTime": started,
            "osc-prov:endedAtTime": ended,
        },
        by_alias=True,
    )

    assert experiment.osc_project == "project-1"
    assert experiment.osc_workflow == "workflow-1"
    assert experiment.osc_prov_generated_by == "osc-client"
    assert experiment.osc_prov_started_at_time == started
    assert experiment.osc_prov_ended_at_time == ended


def test_osc_extension_apply_project_sets_project_shape(osc_modules) -> None:
    osc_extension = osc_modules["osc_extension"]
    collection = pystac.Collection(
        id="collection-1",
        description="Collection",
        extent=pystac.Extent(
            pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            pystac.TemporalExtent([[None, None]]),
        ),
        license="proprietary",
    )

    ext = osc_extension.OscExtension.ext(collection, add_if_missing=True)
    ext.apply_project(
        status=osc_extension.OscStatus.PLANNED,
        workflows=["workflow-1"],
    )

    assert ext.osc_type == osc_extension.OscType.PROJECT
    assert ext.status == osc_extension.OscStatus.PLANNED
    assert ext.workflows == ["workflow-1"]
    assert ext.project is None
    assert osc_extension.SCHEMA_URI in collection.stac_extensions


def test_osc_extension_apply_product_sets_product_shape(osc_modules) -> None:
    osc_extension = osc_modules["osc_extension"]
    item = pystac.Item(
        id="item-1",
        geometry={"type": "Point", "coordinates": [0.0, 0.0]},
        bbox=[0.0, 0.0, 0.0, 0.0],
        datetime=pystac.utils.str_to_datetime("2026-01-01T00:00:00Z"),
        properties={},
    )

    ext = osc_extension.OscExtension.ext(item, add_if_missing=True)
    ext.apply_product(
        status=osc_extension.OscStatus.COMPLETED,
        project="project-1",
        region="europe",
        variables=["temperature"],
        missions=["sentinel-2"],
        experiment="experiment-1",
    )

    assert ext.osc_type == osc_extension.OscType.PRODUCT
    assert ext.project == "project-1"
    assert ext.region == "europe"
    assert ext.variables == ["temperature"]
    assert ext.missions == ["sentinel-2"]
    assert ext.experiment == "experiment-1"
    assert ext.workflows is None


def test_osc_extension_rejects_unsupported_type(osc_modules) -> None:
    osc_extension = osc_modules["osc_extension"]

    try:
        osc_extension.OscExtension.ext("not-a-stac-object")
    except pystac.ExtensionTypeError:
        pass
    else:
        raise AssertionError("Expected ExtensionTypeError")
