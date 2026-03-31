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

import importlib.util
import sys
import types
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src" / "osc_client"


def _load_module(module_name: str, path: Path, package: bool = False):
    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
        submodule_search_locations=[str(path.parent)] if package else None,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _install_ogc_api_processes_stubs() -> None:
    for name in list(sys.modules):
        if name == "ogc_api_processes_client" or name.startswith(
            "ogc_api_processes_client."
        ):
            del sys.modules[name]

    root = types.ModuleType("ogc_api_processes_client")
    api = types.ModuleType("ogc_api_processes_client.api")
    models = types.ModuleType("ogc_api_processes_client.models")
    api_client_mod = types.ModuleType("ogc_api_processes_client.api_client")
    configuration_mod = types.ModuleType("ogc_api_processes_client.configuration")
    status_api_mod = types.ModuleType("ogc_api_processes_client.api.status_api")
    result_api_mod = types.ModuleType("ogc_api_processes_client.api.result_api")
    status_code_mod = types.ModuleType("ogc_api_processes_client.models.status_code")
    status_info_mod = types.ModuleType("ogc_api_processes_client.models.status_info")
    inline_or_ref_mod = types.ModuleType(
        "ogc_api_processes_client.models.inline_or_ref_data"
    )
    link_mod = types.ModuleType("ogc_api_processes_client.models.link")

    @dataclass
    class Configuration:
        host: str

    @dataclass
    class ApiClient:
        configuration: Configuration
        header_name: str | None = None
        header_value: str | None = None

    class StatusCode(str, Enum):
        ACCEPTED = "accepted"
        RUNNING = "running"
        SUCCESSFUL = "successful"
        FAILED = "failed"

    @dataclass
    class StatusInfo:
        status: StatusCode
        started: object | None = None
        finished: object | None = None
        inputs: object | None = None
        properties: dict | None = field(default_factory=dict)

    class StatusApi:
        def __init__(self, api_client: ApiClient):
            self.api_client = api_client

        def get_status(self, job_id: str) -> StatusInfo:
            raise NotImplementedError

    class ResultApi:
        def __init__(self, api_client: ApiClient):
            self.api_client = api_client

        def get_result_without_preload_content(self, job_id: str):
            raise NotImplementedError

    class InlineOrRefData:
        pass

    @dataclass
    class Link:
        href: str
        type: str | None = None
        title: str | None = None

    configuration_mod.Configuration = Configuration
    api_client_mod.ApiClient = ApiClient
    status_code_mod.StatusCode = StatusCode
    status_info_mod.StatusInfo = StatusInfo
    status_api_mod.StatusApi = StatusApi
    result_api_mod.ResultApi = ResultApi
    inline_or_ref_mod.InlineOrRefData = InlineOrRefData
    link_mod.Link = Link

    root.api = api
    root.models = models
    root.api_client = api_client_mod
    root.configuration = configuration_mod
    api.status_api = status_api_mod
    api.result_api = result_api_mod
    models.status_code = status_code_mod
    models.status_info = status_info_mod
    models.inline_or_ref_data = inline_or_ref_mod
    models.link = link_mod

    sys.modules["ogc_api_processes_client"] = root
    sys.modules["ogc_api_processes_client.api"] = api
    sys.modules["ogc_api_processes_client.models"] = models
    sys.modules["ogc_api_processes_client.api_client"] = api_client_mod
    sys.modules["ogc_api_processes_client.configuration"] = configuration_mod
    sys.modules["ogc_api_processes_client.api.status_api"] = status_api_mod
    sys.modules["ogc_api_processes_client.api.result_api"] = result_api_mod
    sys.modules["ogc_api_processes_client.models.status_code"] = status_code_mod
    sys.modules["ogc_api_processes_client.models.status_info"] = status_info_mod
    sys.modules[
        "ogc_api_processes_client.models.inline_or_ref_data"
    ] = inline_or_ref_mod
    sys.modules["ogc_api_processes_client.models.link"] = link_mod


@pytest.fixture
def osc_modules():
    for name in list(sys.modules):
        if name == "osc_client" or name.startswith("osc_client."):
            del sys.modules[name]

    _install_ogc_api_processes_stubs()

    package = _load_module("osc_client", SRC_DIR / "__init__.py", package=True)
    about = _load_module("osc_client.__about__", SRC_DIR / "__about__.py")
    models = _load_module("osc_client.models", SRC_DIR / "models.py")
    osc_extension = _load_module(
        "osc_client.osc_extension", SRC_DIR / "osc_extension.py"
    )
    themes_extension = _load_module(
        "osc_client.themes_extension", SRC_DIR / "themes_extension.py"
    )
    workflow = _load_module("osc_client.workflow", SRC_DIR / "workflow.py")
    experiment = _load_module("osc_client.experiment", SRC_DIR / "experiment.py")
    product = _load_module("osc_client.product", SRC_DIR / "product.py")
    cli = _load_module("osc_client.cli", SRC_DIR / "cli.py")

    return {
        "package": package,
        "about": about,
        "models": models,
        "osc_extension": osc_extension,
        "themes_extension": themes_extension,
        "workflow": workflow,
        "experiment": experiment,
        "product": product,
        "cli": cli,
    }
