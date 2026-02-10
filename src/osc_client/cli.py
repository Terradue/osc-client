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

from pathlib import Path

import click

@click.group()
@click.argument(
    'source',
    type=click.Path(
        path_type=Path,
        exists=True,
        readable=True,
        resolve_path=True
    ),
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
    source: Path,
    output: Path
):
    ctx.ensure_object(dict)
    ctx.obj["source"] = source

    output.parent.mkdir(
        parents=True, exist_ok=True
    )
    ctx.obj["output"] = output


@main.command(
    context_settings={'show_default': True}
)
@click.pass_context
def workflow(ctx):
    pass


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
