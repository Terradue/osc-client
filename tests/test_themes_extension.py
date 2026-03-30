from __future__ import annotations

import importlib.util
from pathlib import Path

import pystac
import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "osc_client" / "themes_extension.py"
)
SPEC = importlib.util.spec_from_file_location("osc_client.themes_extension", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
THEMES_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(THEMES_MODULE)

SCHEMA_URI = THEMES_MODULE.SCHEMA_URI
Theme = THEMES_MODULE.Theme
ThemeConcept = THEMES_MODULE.ThemeConcept
ThemesExtension = THEMES_MODULE.ThemesExtension


def make_theme() -> Theme:
    return Theme(
        scheme="https://example.com/themes",
        concepts=[
            ThemeConcept(
                id="climate",
                title="Climate",
                description="Climate-related resources",
                url="https://example.com/concepts/climate",
            )
        ],
    )


def test_item_themes_round_trip() -> None:
    item = pystac.Item(
        id="item-1",
        geometry={"type": "Point", "coordinates": [0.0, 0.0]},
        bbox=[0.0, 0.0, 0.0, 0.0],
        datetime=pystac.utils.str_to_datetime("2026-01-01T00:00:00Z"),
        properties={},
    )

    ext = ThemesExtension.ext(item, add_if_missing=True)
    ext.apply([make_theme()])

    assert SCHEMA_URI in item.stac_extensions
    assert item.properties["themes"][0]["scheme"] == "https://example.com/themes"
    assert ext.themes is not None
    assert ext.themes[0].concepts[0].id == "climate"


def test_collection_themes_summaries_round_trip() -> None:
    collection = pystac.Collection(
        id="collection-1",
        description="Test collection",
        extent=pystac.Extent(
            pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            pystac.TemporalExtent([[None, None]]),
        ),
        license="proprietary",
    )

    summaries = ThemesExtension.summaries(collection, add_if_missing=True)
    summaries.themes = [make_theme()]

    assert SCHEMA_URI in collection.stac_extensions
    assert collection.summaries.lists["themes"][0]["concepts"][0]["id"] == "climate"
    assert summaries.themes is not None
    assert summaries.themes[0].scheme == "https://example.com/themes"


def test_catalog_themes_round_trip() -> None:
    catalog = pystac.Catalog(id="catalog-1", description="Test catalog")

    ext = ThemesExtension.ext(catalog, add_if_missing=True)
    ext.themes = [make_theme()]

    assert SCHEMA_URI in catalog.stac_extensions
    assert catalog.extra_fields["themes"][0]["concepts"][0]["title"] == "Climate"
    assert ext.themes is not None
    assert ext.themes[0].concepts[0].url == "https://example.com/concepts/climate"


def test_ext_rejects_unsupported_type() -> None:
    with pytest.raises(pystac.ExtensionTypeError):
        ThemesExtension.ext("not-a-stac-object")
