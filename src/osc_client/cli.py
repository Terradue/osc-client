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

from osc_client.workflow import execute as execute_workflow
from pathlib import Path
from requests import Session
from requests.adapters import HTTPAdapter
from session_adapters.file_adapter import FileAdapter
from transpiler_mate.cli import _track

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

    session: Session = Session()
    http_adapter = HTTPAdapter()
    session.mount('http://', http_adapter)
    session.mount('https://', http_adapter)
    session.mount('file://', FileAdapter())
    ctx.obj["session"] = session

    output.parent.mkdir(
        parents=True, exist_ok=True
    )
    ctx.obj["output"] = output


@main.command(
    context_settings={'show_default': True}
)
@click.pass_context
def workflow(ctx):
    source: str = ctx.obj["source"]
    session: Session = ctx.obj["session"]
    output: Path = ctx.obj["output"]
    execute_workflow(
        source,
        session,
        output
    )

@main.command(
    context_settings={'show_default': True}
)
@click.pass_context
def experiment(ctx):
    pass


@main.command(
    context_settings={'show_default': True}
)
@click.pass_context
def products(ctx):
    pass


for command in [workflow, experiment, products]:
    command.callback = _track(command.callback)
