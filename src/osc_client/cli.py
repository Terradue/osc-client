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
from osc_client.workflow import execute as execute_workflow
from pathlib import Path
from transpiler_mate.cli import _track
from transpiler_mate.ogcapi_records.ogcapi_records_models import RecordGeoJSON

import click

@click.group()
@click.argument(
    'source',
    type=click.STRING,
    required=True
)
@click.option(
    '--output',
    type=click.Path(
        path_type=Path
    ),
    required=False,
    help="The output file path"
)
@click.pass_context
def main(
    ctx,
    source: str,
    output: Path
):
    ctx.ensure_object(dict)
    ctx.obj["source"] = source

    record_geojson: RecordGeoJSON = load_record_geojson(source)
    ctx.obj["record_geojson"] = record_geojson

    ctx.obj["output"] = output


@main.command(
    context_settings={'show_default': True}
)
@click.pass_context
@click.option(
    '--project',
    type=click.STRING,
    required=True,
    help="The referencing OGC API Records workflow URL."
)
def workflow(
    ctx,
    project: str
):
    source: str = ctx.obj["source"]
    record_geojson: RecordGeoJSON = ctx.obj["record_geojson"]
    output: Path = ctx.obj["output"]
    execute_workflow(
        source,
        record_geojson,
        project,
        output
    )

@main.command(
    context_settings={'show_default': True}
)
@click.pass_context
@click.option(
    '--workflow-url',
    type=click.STRING,
    required=True,
    help="The referencing OGC API Records workflow URL."
)
@click.option(
    '--ogc-api-endpoint',
    type=click.STRING,
    required=True,
    help="The referencing OGC API Processes service URL."
)
@click.option(
    '--job-id',
    type=click.STRING,
    required=True,
    help="The OGC API Processes Job ID."
)
def experiment(
    ctx,
    workflow_url: str,
    ogc_api_endpoint: str,
    job_id: str
):
    source: str = ctx.obj["source"]
    record_geojson: RecordGeoJSON = ctx.obj["record_geojson"]
    output: Path = ctx.obj["output"]
    execute_experiment(
        source,
        workflow_url,
        record_geojson,
        ogc_api_endpoint,
        job_id,
        output
    )


@main.command(
    context_settings={'show_default': True}
)
@click.pass_context
def products(ctx):
    pass


for command in [workflow, experiment, products]:
    command.callback = _track(command.callback)
