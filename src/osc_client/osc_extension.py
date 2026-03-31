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

from enum import Enum
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks

T = TypeVar("T", pystac.Item, pystac.Collection)

SCHEMA_URI: str = "https://stac-extensions.github.io/osc/v1.0.0/schema.json"
PREFIX: str = "osc:"

TYPE_PROP: str = PREFIX + "type"
STATUS_PROP: str = PREFIX + "status"
WORKFLOWS_PROP: str = PREFIX + "workflows"
PROJECT_PROP: str = PREFIX + "project"
REGION_PROP: str = PREFIX + "region"
VARIABLES_PROP: str = PREFIX + "variables"
MISSIONS_PROP: str = PREFIX + "missions"
EXPERIMENT_PROP: str = PREFIX + "experiment"


class OscType(str, Enum):
    PROJECT = "project"
    PRODUCT = "product"


class OscStatus(str, Enum):
    PLANNED = "planned"
    ONGOING = "ongoing"
    COMPLETED = "completed"


class OscExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """Implements the Open Science Catalog extension for Items and Collections."""

    name: Literal["osc"] = "osc"

    def apply_project(
        self,
        *,
        status: OscStatus,
        workflows: list[str] | None = None,
    ) -> None:
        """Apply the OSC project fields."""
        self.osc_type = OscType.PROJECT
        self.status = status
        self.workflows = workflows

        # Project and product shapes are mutually exclusive in the schema.
        self.project = None
        self.region = None
        self.variables = None
        self.missions = None
        self.experiment = None

    def apply_product(
        self,
        *,
        status: OscStatus,
        project: str,
        region: str | None = None,
        variables: list[str] | None = None,
        missions: list[str] | None = None,
        experiment: str | None = None,
    ) -> None:
        """Apply the OSC product fields."""
        self.osc_type = OscType.PRODUCT
        self.status = status
        self.project = project
        self.region = region
        self.variables = variables
        self.missions = missions
        self.experiment = experiment

        # Project and product shapes are mutually exclusive in the schema.
        self.workflows = None

    @property
    def osc_type(self) -> OscType | None:
        value = self._get_property(TYPE_PROP, str)
        return OscType(value) if value is not None else None

    @osc_type.setter
    def osc_type(self, value: OscType | None) -> None:
        self._set_property(TYPE_PROP, value.value if value is not None else None)

    @property
    def status(self) -> OscStatus | None:
        value = self._get_property(STATUS_PROP, str)
        return OscStatus(value) if value is not None else None

    @status.setter
    def status(self, value: OscStatus | None) -> None:
        self._set_property(STATUS_PROP, value.value if value is not None else None)

    @property
    def workflows(self) -> list[str] | None:
        return cast(list[str] | None, self._get_property(WORKFLOWS_PROP, list[str]))

    @workflows.setter
    def workflows(self, value: list[str] | None) -> None:
        self._set_property(WORKFLOWS_PROP, value)

    @property
    def project(self) -> str | None:
        return self._get_property(PROJECT_PROP, str)

    @project.setter
    def project(self, value: str | None) -> None:
        self._set_property(PROJECT_PROP, value)

    @property
    def region(self) -> str | None:
        return self._get_property(REGION_PROP, str)

    @region.setter
    def region(self, value: str | None) -> None:
        self._set_property(REGION_PROP, value)

    @property
    def variables(self) -> list[str] | None:
        return cast(list[str] | None, self._get_property(VARIABLES_PROP, list[str]))

    @variables.setter
    def variables(self, value: list[str] | None) -> None:
        self._set_property(VARIABLES_PROP, value)

    @property
    def missions(self) -> list[str] | None:
        return cast(list[str] | None, self._get_property(MISSIONS_PROP, list[str]))

    @missions.setter
    def missions(self, value: list[str] | None) -> None:
        self._set_property(MISSIONS_PROP, value)

    @property
    def experiment(self) -> str | None:
        return self._get_property(EXPERIMENT_PROP, str)

    @experiment.setter
    def experiment(self, value: str | None) -> None:
        self._set_property(EXPERIMENT_PROP, value)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> OscExtension[T]:
        """Extend an Item or Collection with OSC fields."""
        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(OscExtension[T], CollectionOscExtension(obj))
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(OscExtension[T], ItemOscExtension(obj))

        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))


class CollectionOscExtension(OscExtension[pystac.Collection]):
    """Attach the OSC extension to a Collection."""

    collection: pystac.Collection
    properties: dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionOscExtension Collection id={self.collection.id}>"


class ItemOscExtension(OscExtension[pystac.Item]):
    """Attach the OSC extension to an Item."""

    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemOscExtension Item id={self.item.id}>"


class OscExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: set[str] = set()
    stac_object_types = {
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.ITEM,
    }


OSC_EXTENSION_HOOKS: ExtensionHooks = OscExtensionHooks()

if SCHEMA_URI not in pystac.EXTENSION_HOOKS.hooks:
    pystac.EXTENSION_HOOKS.add_extension_hooks(OSC_EXTENSION_HOOKS)
