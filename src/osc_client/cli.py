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

from osc_client import load_record_geojson
from osc_client.experiment import execute as execute_experiment
from osc_client.product import execute as execute_product
from osc_client.workflow import execute as execute_workflow
from pathlib import Path
from transpiler_mate.cli import _track
from transpiler_mate.ogcapi_records.ogcapi_records_models import RecordGeoJSON
from typing import Dict

import click


@click.group()
@click.argument("source", type=click.STRING, required=True)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=False,
    help="The output file path",
)
@click.pass_context
def main(ctx, source: str, output: Path):
    ctx.ensure_object(dict)
    ctx.obj["source"] = source

    record_geojson: RecordGeoJSON = load_record_geojson(source)
    ctx.obj["record_geojson"] = record_geojson

    ctx.obj["output"] = output


@main.command(context_settings={"show_default": True})
@click.pass_context
@click.option(
    "--project",
    type=click.STRING,
    required=True,
    help="The referencing OGC API Records workflow URL.",
)
def workflow(ctx, project: str):
    source: str = ctx.obj["source"]
    record_geojson: RecordGeoJSON = ctx.obj["record_geojson"]
    output: Path = ctx.obj["output"]
    execute_workflow(source, record_geojson, project, output)


@main.command(context_settings={"show_default": True})
@click.pass_context
@click.option(
    "--workflow-url",
    type=click.STRING,
    required=True,
    help="The referencing OGC API Records workflow URL.",
)
@click.option(
    "--ogc-api-processes-endpoint",
    type=click.STRING,
    required=True,
    help="The referencing OGC API Processes service URL.",
)
@click.option(
    "--job-id", type=click.STRING, required=True, help="The OGC API Processes Job ID."
)
@click.option(
    "--authorization-token",
    type=click.STRING,
    required=False,
    default=None,
    help="Authorization JSON Web Token'",
)
def experiment(
    ctx,
    workflow_url: str,
    ogc_api_processes_endpoint: str,
    job_id: str,
    authorization_token: str,
):
    source: str = ctx.obj["source"]
    record_geojson: RecordGeoJSON = ctx.obj["record_geojson"]
    output: Path = ctx.obj["output"]
    execute_experiment(
        source=source,
        workflow_url=workflow_url,
        record_geojson=record_geojson,
        ogc_api_processes_endpoint=ogc_api_processes_endpoint,
        job_id=job_id,
        output=output,
        authorization_token=authorization_token,
    )


@main.command(context_settings={"show_default": True})
@click.pass_context
@click.option(
    "--workflow-url",
    type=click.STRING,
    required=True,
    help="The referencing OGC API Records workflow URL.",
)
@click.option(
    "--ogc-api-processes-endpoint",
    type=click.STRING,
    required=True,
    help="The referencing OGC API Processes service URL.",
)
@click.option(
    "--job-id", type=click.STRING, required=True, help="The OGC API Processes Job ID."
)
@click.option(
    "--authorization-token",
    type=click.STRING,
    required=False,
    default=None,
    help="Authorization JSON Web Token'",
)
def products(
    ctx,
    experiment_url: str,
    ogc_api_processes_endpoint: str,
    job_id: str,
    authorization_token: str,
):
    source: str = ctx.obj["source"]
    record_geojson: RecordGeoJSON = ctx.obj["record_geojson"]
    output: Path = ctx.obj["output"]
    execute_product(
        source,
        ogc_api_processes_endpoint,
        record_geojson,
        job_id,
        experiment_url,
        output,
        authorization_token,
    )


# for command in [workflow, experiment, products]:
#     command.callback = _track(command.callback)
