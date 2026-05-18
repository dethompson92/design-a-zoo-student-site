#!/usr/bin/env python3
"""Validate the public student site package."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROWS = 1711
EXPECTED_HABITATS = 50
EXPECTED_GEOMETRY_EXAMPLES = 125
EXPECTED_GEOMETRY_CATEGORIES = 10

REQUIRED_FILES = [
    "index.html",
    "styles.css",
    "app.js",
    "geometry.html",
    "geometry-gallery.js",
    "enclosure-examples.html",
    "enclosure-examples.js",
    "data/animals.json",
    "data/animal_verification.json",
    "data/habitats.json",
    "data/geometry_examples.json",
    "docs/AUDIT.md",
    "docs/ANIMAL_DATA_AUDIT.md",
    "docs/GEOMETRY_GALLERY_AUDIT.md",
    ".github/workflows/pages.yml",
]

REQUIRED_ANIMAL_KEYS = {
    "animal_id",
    "animal_name",
    "scientific_name",
    "source_scientific_name",
    "verified_scientific_name",
    "verification_status",
    "verification_method",
    "primary_habitat",
    "world_region",
    "space_first_animal_sq_units",
    "space_each_additional_animal_sq_units",
    "minimum_family_group",
    "minimum_group_space_sq_units",
    "space_planning_sq_units",
    "space_planning_basis",
    "cost_per_animal_usd",
    "minimum_group_cost_usd",
    "cost_planning_usd",
    "cost_planning_basis",
    "swagg_revenue_equation",
    "suggested_enclosure_design_category",
    "suggested_physical_model_feature",
    "curriculum_connections",
    "data_note",
    "student_info_url",
    "animal_diversity_web_url",
    "gbif_url",
    "inaturalist_url",
    "habitat_research_url",
    "region_research_url",
    "animal_image_path",
    "image_alt",
    "image_credit",
    "image_source",
    "image_license_name",
    "image_license_url",
    "image_provider",
}

NUMERIC_KEYS = {
    "space_first_animal_sq_units",
    "space_each_additional_animal_sq_units",
    "minimum_family_group",
    "minimum_group_space_sq_units",
    "space_planning_sq_units",
    "cost_per_animal_usd",
    "minimum_group_cost_usd",
    "cost_planning_usd",
}

CONTAMINATION_PATTERN = re.compile(
    r"(box-shadow|transform|document|querySelector|swagg d|NOT FOUND|JAVASCRIPT|Generate the missing|UI logic)",
    re.IGNORECASE,
)

FORBIDDEN_PUBLIC_PATHS = [
    "Genspark_-_Your_All-in-One_AI_Workspace_conversation.html",
    "Genspark_-_Your_All-in-One_AI_Workspace_conversation.md",
    "Genspark_-_Your_All-in-One_AI_Workspace_data.json",
    "all_animals.csv",
    "all_animals_final.csv",
    "all_animals_comprehensive.csv",
    "animals",
    "Zoo",
    "tool_activity",
    "ai_thinking",
]

ALLOWED_LICENSE_TOKENS = {
    "cc0",
    "public domain",
    "publicdomain",
    "pd",
    "pdm",
    "cc by",
    "cc-by",
    "cc-by-sa",
    "cc by-sa",
    "cc by sa",
}

REQUIRED_GEOMETRY_KEYS = {
    "id",
    "title",
    "slug",
    "source_filename",
    "asset_path",
    "category_slug",
    "category",
    "category_description",
    "animal_group",
    "habitat_theme",
    "geometry_type",
    "design_use",
    "keywords",
    "width",
    "height",
}


def load_json(path: str) -> object:
    return json.loads((SITE_ROOT / path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def normalize_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_value.lower())


def validate_files() -> None:
    for required in REQUIRED_FILES:
        require((SITE_ROOT / required).exists(), f"Missing required file: {required}")

    for forbidden in FORBIDDEN_PUBLIC_PATHS:
        require(not (SITE_ROOT / forbidden).exists(), f"Forbidden raw artifact is present: {forbidden}")

    habitat_images = sorted((SITE_ROOT / "assets" / "habitats").glob("*.png"))
    require(len(habitat_images) == EXPECTED_HABITATS, f"Expected {EXPECTED_HABITATS} habitat PNGs, found {len(habitat_images)}")

    geometry_images = sorted((SITE_ROOT / "assets" / "geometry").glob("**/*.webp"))
    require(
        len(geometry_images) == EXPECTED_GEOMETRY_EXAMPLES,
        f"Expected {EXPECTED_GEOMETRY_EXAMPLES} geometry WebP images, found {len(geometry_images)}",
    )
    geometry_pngs = sorted((SITE_ROOT / "assets" / "geometry").glob("**/*.png"))
    require(not geometry_pngs, "Geometry source PNGs should not be copied into the public assets folder")

    geometry_pages = sorted((SITE_ROOT / "geometry").glob("*.html"))
    require(
        len(geometry_pages) == EXPECTED_GEOMETRY_CATEGORIES,
        f"Expected {EXPECTED_GEOMETRY_CATEGORIES} geometry category pages, found {len(geometry_pages)}",
    )


def validate_data() -> None:
    animals = load_json("data/animals.json")
    habitats = load_json("data/habitats.json")
    geometry = load_json("data/geometry_examples.json")
    require(isinstance(animals, list), "animals.json must be a list")
    require(isinstance(habitats, list), "habitats.json must be a list")
    require(isinstance(geometry, dict), "geometry_examples.json must be an object")
    require(len(animals) == EXPECTED_ROWS, f"Expected {EXPECTED_ROWS} animal entries, found {len(animals)}")
    require(len(habitats) == EXPECTED_HABITATS, f"Expected {EXPECTED_HABITATS} habitats, found {len(habitats)}")
    validate_geometry_data(geometry)

    ids = [row["animal_id"] for row in animals]
    require(len(ids) == len(set(ids)), "Animal IDs must be unique")
    normalized_names = [normalize_name(row["animal_name"]) for row in animals]
    require(len(normalized_names) == len(set(normalized_names)), "Animal names must be deduplicated")

    habitat_names = {row["name"] for row in habitats}
    animal_habitats = {row["primary_habitat"] for row in animals}
    require(habitat_names == animal_habitats, "Habitats in animals.json and habitats.json must match")

    for row in animals:
        missing = REQUIRED_ANIMAL_KEYS - set(row)
        require(not missing, f"{row.get('animal_id', 'unknown row')} is missing keys: {sorted(missing)}")
        require(not CONTAMINATION_PATTERN.search(row["animal_name"]), f"Contaminated animal name: {row['animal_name']}")
        for key in NUMERIC_KEYS:
            require(isinstance(row[key], int), f"{row['animal_id']} {key} must be an integer")
            require(row[key] >= 0, f"{row['animal_id']} {key} must be nonnegative")
        require(row["minimum_family_group"] >= 1, f"{row['animal_id']} minimum_family_group must be at least 1")
        require(
            row["space_planning_sq_units"] == row["minimum_group_space_sq_units"],
            f"{row['animal_id']} planning space must equal minimum group space",
        )
        require(
            row["cost_planning_usd"] == row["minimum_group_cost_usd"],
            f"{row['animal_id']} planning cost must equal minimum group cost",
        )
        require(row["verification_status"] in {"verified", "needs_review"}, f"{row['animal_id']} has invalid verification_status")
        for key in [
            "student_info_url",
            "animal_diversity_web_url",
            "gbif_url",
            "inaturalist_url",
            "habitat_research_url",
            "region_research_url",
        ]:
            require(str(row[key]).startswith("https://"), f"{row['animal_id']} {key} must be an https URL")
        if row["animal_image_path"]:
            require((SITE_ROOT / row["animal_image_path"]).exists(), f"Missing animal image: {row['animal_image_path']}")
            require(row["image_credit"], f"{row['animal_id']} image_credit is required for approved images")
            require(row["image_source"], f"{row['animal_id']} image_source is required for approved images")
            require(row["image_license_name"], f"{row['animal_id']} image_license_name is required for approved images")
            require(row["image_license_url"], f"{row['animal_id']} image_license_url is required for approved images")
            normalized_license = row["image_license_name"].lower().replace("_", " ")
            require(
                any(token in normalized_license for token in ALLOWED_LICENSE_TOKENS),
                f"{row['animal_id']} has a disallowed image license: {row['image_license_name']}",
            )
        else:
            require(not row["image_credit"], f"{row['animal_id']} has image_credit without image_path")
            require(not row["image_source"], f"{row['animal_id']} has image_source without image_path")

    for habitat in habitats:
        require((SITE_ROOT / habitat["image_path"]).exists(), f"Missing habitat image: {habitat['image_path']}")
        require(habitat["animal_count"] >= 1, f"{habitat['name']} must have at least one animal")


def validate_geometry_data(geometry: dict) -> None:
    categories = geometry.get("categories")
    examples = geometry.get("examples")
    require(isinstance(categories, list), "geometry categories must be a list")
    require(isinstance(examples, list), "geometry examples must be a list")
    require(
        len(categories) == EXPECTED_GEOMETRY_CATEGORIES,
        f"Expected {EXPECTED_GEOMETRY_CATEGORIES} geometry categories, found {len(categories)}",
    )
    require(
        len(examples) == EXPECTED_GEOMETRY_EXAMPLES,
        f"Expected {EXPECTED_GEOMETRY_EXAMPLES} geometry examples, found {len(examples)}",
    )

    category_slugs = {category["slug"] for category in categories}
    require(len(category_slugs) == len(categories), "Geometry category slugs must be unique")
    ids = [example["id"] for example in examples]
    source_names = [example["source_filename"] for example in examples]
    require(len(ids) == len(set(ids)), "Geometry example IDs must be unique")
    require(len(source_names) == len(set(source_names)), "Geometry source filenames must be unique")

    for category in categories:
        page = SITE_ROOT / "geometry" / f"{category['slug']}.html"
        require(page.exists(), f"Missing geometry category page: {page.relative_to(SITE_ROOT)}")

    for example in examples:
        missing = REQUIRED_GEOMETRY_KEYS - set(example)
        require(not missing, f"Geometry example {example.get('id', 'unknown')} missing keys: {sorted(missing)}")
        require(example["category_slug"] in category_slugs, f"{example['id']} has unknown geometry category")
        require(str(example["asset_path"]).startswith("assets/geometry/"), f"{example['id']} has invalid asset path")
        require(str(example["asset_path"]).endswith(".webp"), f"{example['id']} geometry asset must be WebP")
        require((SITE_ROOT / example["asset_path"]).exists(), f"Missing geometry image: {example['asset_path']}")
        require(isinstance(example["keywords"], list) and example["keywords"], f"{example['id']} must have keywords")
        require(int(example["width"]) > 0 and int(example["height"]) > 0, f"{example['id']} has invalid dimensions")


def validate_markup() -> None:
    html = (SITE_ROOT / "index.html").read_text(encoding="utf-8")
    for token in [
        "searchInput",
        "habitatFilter",
        "regionFilter",
        "designFilter",
        "cardResults",
        "animalTableBody",
        "Classroom data note",
        "SWAGG",
        "data-sort-key",
        "geometry.html",
        "enclosure-examples.html",
    ]:
        require(token in html, f"index.html is missing expected token: {token}")

    geometry_html = (SITE_ROOT / "geometry.html").read_text(encoding="utf-8")
    for token in ["geometryGallery", "geometrySearch", "Geometry Example Gallery", "geometry-gallery.js"]:
        require(token in geometry_html, f"geometry.html is missing expected token: {token}")

    sizes_html = (SITE_ROOT / "enclosure-examples.html").read_text(encoding="utf-8")
    for token in ["sizeExamples", "sizeSearch", "Enclosure Size Examples", "enclosure-examples.js"]:
        require(token in sizes_html, f"enclosure-examples.html is missing expected token: {token}")


def main() -> None:
    validate_files()
    validate_data()
    validate_markup()
    print("Validation passed: 1,711 animals, 50 habitats, 125 geometry examples, and clean public package.")


if __name__ == "__main__":
    main()
