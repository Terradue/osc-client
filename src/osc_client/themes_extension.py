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

from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import map_opt

T = TypeVar("T", pystac.Catalog, pystac.Collection, pystac.Item)

SCHEMA_URI: str = "https://stac-extensions.github.io/themes/v1.0.0/schema.json"
THEMES_PROP: str = "themes"


class ThemeConcept:
    """A single concept within a STAC theme."""

    id: str
    title: str | None
    description: str | None
    url: str | None

    def __init__(
        self,
        id: str,
        title: str | None = None,
        description: str | None = None,
        url: str | None = None,
    ) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.url = url

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self.id}
        if self.title is not None:
            d["title"] = self.title
        if self.description is not None:
            d["description"] = self.description
        if self.url is not None:
            d["url"] = self.url
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ThemeConcept:
        return cls(
            id=cast(str, d["id"]),
            title=cast(str | None, d.get("title")),
            description=cast(str | None, d.get("description")),
            url=cast(str | None, d.get("url")),
        )

    def __repr__(self) -> str:
        return f"<ThemeConcept id={self.id}>"


class Theme:
    """A theme entry from the STAC themes extension."""

    scheme: str
    concepts: list[ThemeConcept]

    def __init__(self, scheme: str, concepts: list[ThemeConcept]) -> None:
        self.scheme = scheme
        self.concepts = concepts

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheme": self.scheme,
            "concepts": [concept.to_dict() for concept in self.concepts],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Theme:
        return cls(
            scheme=cast(str, d["scheme"]),
            concepts=[
                ThemeConcept.from_dict(concept)
                for concept in cast(list[dict[str, Any]], d["concepts"])
            ],
        )

    def __repr__(self) -> str:
        return f"<Theme scheme={self.scheme}>"


class ThemesExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Catalog | pystac.Collection | pystac.Item],
):
    """Implements the STAC themes extension for Catalogs, Collections, and Items."""

    name: Literal["themes"] = "themes"

    def apply(self, themes: list[Theme]) -> None:
        """Apply themes extension fields to the extended STAC object."""
        self.themes = themes

    @property
    def themes(self) -> list[Theme] | None:
        return map_opt(
            lambda themes: [Theme.from_dict(theme) for theme in themes],
            self._get_property(THEMES_PROP, list[dict[str, Any]]),
        )

    @themes.setter
    def themes(self, value: list[Theme] | None) -> None:
        self._set_property(
            THEMES_PROP,
            map_opt(lambda themes: [theme.to_dict() for theme in themes], value),
            pop_if_none=True,
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ThemesExtension[T]:
        """Extend a Catalog, Collection, or Item with themes fields."""
        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ThemesExtension[T], CollectionThemesExtension(obj))
        if isinstance(obj, pystac.Catalog):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ThemesExtension[T], CatalogThemesExtension(obj))
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ThemesExtension[T], ItemThemesExtension(obj))

        raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesThemesExtension:
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesThemesExtension(obj)


class CatalogThemesExtension(ThemesExtension[pystac.Catalog]):
    """Attach the themes extension to a Catalog."""

    catalog: pystac.Catalog
    properties: dict[str, Any]

    def __init__(self, catalog: pystac.Catalog):
        self.catalog = catalog
        self.properties = catalog.extra_fields

    def __repr__(self) -> str:
        return f"<CatalogThemesExtension Catalog id={self.catalog.id}>"


class CollectionThemesExtension(ThemesExtension[pystac.Collection]):
    """Attach the themes extension to a Collection."""

    collection: pystac.Collection
    properties: dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionThemesExtension Collection id={self.collection.id}>"


class ItemThemesExtension(ThemesExtension[pystac.Item]):
    """Attach the themes extension to an Item."""

    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemThemesExtension Item id={self.item.id}>"


class SummariesThemesExtension(SummariesExtension):
    """Extend collection summaries with the themes extension payload."""

    @property
    def themes(self) -> list[Theme] | None:
        return map_opt(
            lambda themes: [Theme.from_dict(theme) for theme in themes],
            self.summaries.get_list(THEMES_PROP),
        )

    @themes.setter
    def themes(self, value: list[Theme] | None) -> None:
        self._set_summary(
            THEMES_PROP,
            map_opt(lambda themes: [theme.to_dict() for theme in themes], value),
        )


class ThemesExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: set[str] = set()
    stac_object_types = {
        pystac.STACObjectType.CATALOG,
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.ITEM,
    }


THEMES_EXTENSION_HOOKS: ExtensionHooks = ThemesExtensionHooks()

if SCHEMA_URI not in pystac.EXTENSION_HOOKS.hooks:
    pystac.EXTENSION_HOOKS.add_extension_hooks(THEMES_EXTENSION_HOOKS)
