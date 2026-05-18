#!/usr/bin/env python3
"""Build public JSON data and audit artifacts for the student site."""

from __future__ import annotations

import csv
import json
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SITE_ROOT.parent
SOURCE_CSV = PROJECT_ROOT / "Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package" / "zoo_animals_student_database_final.csv"
SOURCE_HABITATS = PROJECT_ROOT / "Wild_Ecosystem_Habitats_Collection"
DATA_DIR = SITE_ROOT / "data"
ASSET_DIR = SITE_ROOT / "assets" / "habitats"
DOCS_DIR = SITE_ROOT / "docs"

EXPECTED_ROWS = 1844
EXPECTED_HABITATS = 50

REQUIRED_SOURCE_COLUMNS = [
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
]

PUBLIC_ANIMAL_COLUMNS = REQUIRED_SOURCE_COLUMNS + [
    "animal_image_path",
    "image_alt",
    "image_credit",
    "image_source",
]

HABITAT_IMAGE_OVERRIDES = {
    "Amphibian House": "habitat_36_steaming_jungle_floor.png",
    "Flooded Forests (Varzea/Igapo)": "habitat_45_flooded_forests.png",
    "Freshwater Swamp/Wetlands": "habitat_15_freshwater_swamp.png",
    "Insectarium": "habitat_39_micro_jungle_forest_floor.png",
    "Invertebrate House": "habitat_40_tide_pool_micro_ecosystem.png",
    "Nocturnal House": "habitat_33_nocturnal_forest.png",
    "Reptile House - Desert": "habitat_37_deep_desert_dunes.png",
    "Reptile House - Tropical": "habitat_38_wet_rainforest_understory.png",
    "South American Grasslands (Pampas)": "habitat_08_south_american_pampas.png",
    "Temperate Aviary": "habitat_34_temperate_forest_canopy.png",
    "Tropical Aviary": "habitat_35_deep_tropical_jungle.png",
    "Tropical Coastal/Beach": "habitat_20_tropical_coastal.png",
    "Urban/City Wildlife": "habitat_43_reclaimed_abandoned_city.png",
}

CONTAMINATION_PATTERN = re.compile(
    r"(box-shadow|transform|document|querySelector|swagg d|NOT FOUND|JAVASCRIPT|Generate the missing|UI logic)",
    re.IGNORECASE,
)


def normalize(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_value.lower())


def label_from_habitat_file(path: Path) -> str:
    base = path.stem
    label = re.sub(r"^habitat_\d+_", "", base)
    label = label.replace("_remake", "").replace("_", " ")
    return label


def parse_int(row: dict[str, str], key: str) -> int:
    raw = row.get(key, "").replace(",", "").strip()
    if raw == "":
        raise ValueError(f"Missing numeric value for {key} in {row.get('animal_id', 'unknown row')}")
    return int(raw)


def load_rows() -> list[dict[str, object]]:
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [column for column in REQUIRED_SOURCE_COLUMNS if column not in reader.fieldnames]
        if missing_columns:
            raise SystemExit(f"Source CSV is missing required columns: {missing_columns}")

        animals: list[dict[str, object]] = []
        for row in reader:
            if CONTAMINATION_PATTERN.search(row["animal_name"]):
                raise SystemExit(f"Contaminated animal row detected: {row['animal_id']} {row['animal_name']}")

            animal = {
                "animal_id": row["animal_id"].strip(),
                "animal_name": row["animal_name"].strip(),
                "scientific_name": row["scientific_name"].strip(),
                "primary_habitat": row["primary_habitat"].strip(),
                "world_region": row["world_region"].strip(),
                "space_first_animal_sq_units": parse_int(row, "space_first_animal_sq_units"),
                "space_each_additional_animal_sq_units": parse_int(row, "space_each_additional_animal_sq_units"),
                "minimum_family_group": parse_int(row, "minimum_family_group"),
                "minimum_group_space_sq_units": parse_int(row, "minimum_group_space_sq_units"),
                "cost_per_animal_usd": parse_int(row, "cost_per_animal_usd"),
                "minimum_group_cost_usd": parse_int(row, "minimum_group_cost_usd"),
                "swagg_revenue_equation": row["swagg_revenue_equation"].strip(),
                "suggested_enclosure_design_category": row["suggested_enclosure_design_category"].strip(),
                "suggested_physical_model_feature": row["suggested_physical_model_feature"].strip(),
                "curriculum_connections": row["curriculum_connections"].strip(),
                "data_note": row["data_note"].strip(),
                "animal_image_path": "",
                "image_alt": f"{row['animal_name'].strip()} image placeholder",
                "image_credit": "",
                "image_source": "",
            }
            animals.append(animal)

    animals.sort(key=lambda item: (str(item["animal_name"]).lower(), str(item["primary_habitat"]).lower(), str(item["animal_id"])))
    return animals


def copy_habitat_assets() -> dict[str, str]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for existing in ASSET_DIR.glob("*.png"):
        existing.unlink()

    habitat_files = sorted(SOURCE_HABITATS.glob("*.png"))
    if len(habitat_files) != EXPECTED_HABITATS:
        raise SystemExit(f"Expected {EXPECTED_HABITATS} habitat PNGs, found {len(habitat_files)}")

    label_to_file: dict[str, str] = {}
    for source in habitat_files:
        target = ASSET_DIR / source.name
        shutil.copy2(source, target)
        label_to_file[normalize(label_from_habitat_file(source))] = source.name

    return label_to_file


def build_habitats(animals: list[dict[str, object]], label_to_file: dict[str, str]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for animal in animals:
        grouped[str(animal["primary_habitat"])].append(animal)

    habitats: list[dict[str, object]] = []
    for name in sorted(grouped):
        override_key = normalize(name)
        override_file = None
        for override_name, filename in HABITAT_IMAGE_OVERRIDES.items():
            if normalize(override_name) == override_key:
                override_file = filename
                break

        filename = override_file or label_to_file.get(normalize(name))
        if not filename:
            raise SystemExit(f"No habitat image mapping found for {name}")

        rows = grouped[name]
        habitats.append(
            {
                "name": name,
                "image_path": f"assets/habitats/{filename}",
                "animal_count": len(rows),
                "region_count": len({str(row["world_region"]) for row in rows}),
                "design_categories": sorted({str(row["suggested_enclosure_design_category"]) for row in rows}),
                "cost_min": min(int(row["cost_per_animal_usd"]) for row in rows),
                "cost_max": max(int(row["cost_per_animal_usd"]) for row in rows),
                "space_min": min(int(row["space_first_animal_sq_units"]) for row in rows),
                "space_max": max(int(row["space_first_animal_sq_units"]) for row in rows),
            }
        )

    return habitats


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audit_markdown(animals: list[dict[str, object]], habitats: list[dict[str, object]]) -> str:
    animal_names = [str(row["animal_name"]) for row in animals]
    duplicate_names = [name for name, count in Counter(animal_names).items() if count > 1]
    not_specified = sum(1 for row in animals if row["scientific_name"] == "Not specified")
    regions = {str(row["world_region"]) for row in animals}
    designs = Counter(str(row["suggested_enclosure_design_category"]) for row in animals)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    override_lines = [
        f"- {name} -> assets/habitats/{filename}"
        for name, filename in sorted(HABITAT_IMAGE_OVERRIDES.items())
    ]
    design_lines = [f"- {name}: {count}" for name, count in designs.most_common()]

    return f"""# Design a Zoo Public Student Website Audit

Generated: {generated_at}

## Source of Truth

- Primary source CSV: `{SOURCE_CSV.relative_to(PROJECT_ROOT)}`
- Public animal entries: {len(animals):,}
- Unique animal names: {len(set(animal_names)):,}
- Duplicate animal names kept as separate habitat choices: {len(duplicate_names):,}
- Habitats: {len(habitats):,}
- World/region labels: {len(regions):,}
- Rows with `scientific_name = "Not specified"`: {not_specified:,}

## Published Files

- `index.html`, `styles.css`, and `app.js` provide the student-facing database.
- `data/animals.json` contains the public animal-choice data plus Phase 2 image fields.
- `data/habitats.json` contains habitat summaries and habitat image paths.
- `assets/habitats/` contains the 50 copied habitat PNG assets.
- `scripts/validate_site.py` verifies the public site package before deployment.

## Excluded From Public Repo

- Raw Genspark conversation exports and tool activity logs.
- Teacher guides, answer materials, archives, and generated packet workspaces.
- The contaminated larger CSVs: `all_animals.csv`, `all_animals_final.csv`, and `all_animals_comprehensive.csv`.
- The polluted `animals/` markdown folder, which includes generated CSS/JavaScript fragments and extra non-student records.

## Data Quality Notes

- Duplicate animal names are valid because some animals appear as choices in multiple habitats.
- Classroom values are simplified for math modeling and are not real animal-care standards.
- Individual animal images are not published yet. Every animal row includes `animal_image_path`, `image_alt`, `image_credit`, and `image_source` for the Phase 2 image pipeline.
- Habitat images are available now. Some student habitat labels needed explicit mapping to the closest existing habitat asset.

## Explicit Habitat Image Mappings

{chr(10).join(override_lines)}

## Enclosure Design Categories

{chr(10).join(design_lines)}
"""


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    animals = load_rows()
    if len(animals) != EXPECTED_ROWS:
        raise SystemExit(f"Expected {EXPECTED_ROWS} animal rows, found {len(animals)}")

    label_to_file = copy_habitat_assets()
    habitats = build_habitats(animals, label_to_file)
    if len(habitats) != EXPECTED_HABITATS:
        raise SystemExit(f"Expected {EXPECTED_HABITATS} habitats, found {len(habitats)}")

    write_json(DATA_DIR / "animals.json", animals)
    write_json(DATA_DIR / "habitats.json", habitats)
    (DOCS_DIR / "AUDIT.md").write_text(audit_markdown(animals, habitats), encoding="utf-8")
    print(f"Built {len(animals):,} animal entries and {len(habitats):,} habitats.")


if __name__ == "__main__":
    main()
