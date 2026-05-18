#!/usr/bin/env python3
"""Validate the public student site package."""

from __future__ import annotations

import json
import re
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROWS = 1844
EXPECTED_HABITATS = 50

REQUIRED_FILES = [
    "index.html",
    "styles.css",
    "app.js",
    "data/animals.json",
    "data/habitats.json",
    "docs/AUDIT.md",
    ".github/workflows/pages.yml",
]

REQUIRED_ANIMAL_KEYS = {
    "animal_id",
    "animal_name",
    "scientific_name",
    "primary_habitat",
    "world_region",
    "space_first_animal_sq_units",
    "space_each_additional_animal_sq_units",
    "minimum_family_group",
    "minimum_group_space_sq_units",
    "cost_per_animal_usd",
    "minimum_group_cost_usd",
    "swagg_revenue_equation",
    "suggested_enclosure_design_category",
    "suggested_physical_model_feature",
    "curriculum_connections",
    "data_note",
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
    "cost_per_animal_usd",
    "minimum_group_cost_usd",
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


def load_json(path: str) -> object:
    return json.loads((SITE_ROOT / path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_files() -> None:
    for required in REQUIRED_FILES:
        require((SITE_ROOT / required).exists(), f"Missing required file: {required}")

    for forbidden in FORBIDDEN_PUBLIC_PATHS:
        require(not (SITE_ROOT / forbidden).exists(), f"Forbidden raw artifact is present: {forbidden}")

    habitat_images = sorted((SITE_ROOT / "assets" / "habitats").glob("*.png"))
    require(len(habitat_images) == EXPECTED_HABITATS, f"Expected {EXPECTED_HABITATS} habitat PNGs, found {len(habitat_images)}")


def validate_data() -> None:
    animals = load_json("data/animals.json")
    habitats = load_json("data/habitats.json")
    require(isinstance(animals, list), "animals.json must be a list")
    require(isinstance(habitats, list), "habitats.json must be a list")
    require(len(animals) == EXPECTED_ROWS, f"Expected {EXPECTED_ROWS} animal entries, found {len(animals)}")
    require(len(habitats) == EXPECTED_HABITATS, f"Expected {EXPECTED_HABITATS} habitats, found {len(habitats)}")

    ids = [row["animal_id"] for row in animals]
    require(len(ids) == len(set(ids)), "Animal IDs must be unique")

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
    ]:
        require(token in html, f"index.html is missing expected token: {token}")


def main() -> None:
    validate_files()
    validate_data()
    validate_markup()
    print("Validation passed: 1,844 animals, 50 habitats, 50 habitat images, and clean public package.")


if __name__ == "__main__":
    main()
