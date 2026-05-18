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
from urllib.parse import urlencode


SITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SITE_ROOT.parent
SOURCE_CSV = PROJECT_ROOT / "Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package" / "zoo_animals_student_database_final.csv"
SOURCE_HABITATS = PROJECT_ROOT / "Wild_Ecosystem_Habitats_Collection"
DATA_DIR = SITE_ROOT / "data"
ASSET_DIR = SITE_ROOT / "assets" / "habitats"
DOCS_DIR = SITE_ROOT / "docs"
IMAGE_MANIFEST = DATA_DIR / "animal_image_manifest.json"
ANIMAL_VERIFICATION = DATA_DIR / "animal_verification.json"

EXPECTED_SOURCE_ROWS = 1844
EXPECTED_ROWS = 1713
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
    "source_scientific_name",
    "verified_scientific_name",
    "verification_status",
    "verification_method",
    "space_planning_sq_units",
    "space_planning_basis",
    "cost_planning_usd",
    "cost_planning_basis",
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


def research_url(base: str, query: str, param: str = "q") -> str:
    return f"{base}?{urlencode({param: query})}"


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


def load_image_manifest() -> dict[str, dict[str, object]]:
    if not IMAGE_MANIFEST.exists():
        return {}

    raw_manifest = json.loads(IMAGE_MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(raw_manifest, dict):
        raise SystemExit("data/animal_image_manifest.json must be an object keyed by animal name")
    return raw_manifest


def load_animal_verification() -> dict[str, dict[str, object]]:
    if not ANIMAL_VERIFICATION.exists():
        return {}

    raw = json.loads(ANIMAL_VERIFICATION.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("data/animal_verification.json must be an object keyed by animal name")
    return raw


def approved_image_for(manifest: dict[str, dict[str, object]], animal_name: str) -> dict[str, str]:
    record = manifest.get(animal_name)
    if not record or record.get("review_status") != "approved":
        return {}

    image_path = str(record.get("image_path") or "").strip()
    if not image_path:
        return {}

    return {
        "animal_image_path": image_path,
        "image_alt": str(record.get("alt_text") or f"{animal_name} photo").strip(),
        "image_credit": str(record.get("credit") or "").strip(),
        "image_source": str(record.get("source_url") or "").strip(),
        "image_license_name": str(record.get("license_name") or "").strip(),
        "image_license_url": str(record.get("license_url") or "").strip(),
        "image_provider": str(record.get("provider") or "").strip(),
    }


def source_row_score(row: dict[str, str], source_index: int) -> float:
    scientific_name = row["scientific_name"].strip()
    scientific_lower = scientific_name.lower()
    score = 0.0
    if scientific_name != "Not specified":
        score += 100
        if "spp" not in scientific_lower and " sp." not in scientific_lower and len(scientific_name.split()) >= 2:
            score += 30
    if row["world_region"].strip() != "Global":
        score += 20
    if row["primary_habitat"].strip() not in {"Urban/City Wildlife", "Subterranean/Underground"}:
        score += 5
    score -= source_index / 100000
    return score


def dedupe_source_rows(
    source_rows: list[dict[str, str]],
    verification: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
    verification_by_id = {
        str(record.get("selected_animal_id")): record
        for record in verification.values()
        if record.get("selected_animal_id") and record.get("publish_status") != "exclude_non_real"
    }
    if verification_by_id:
        selected = [row for row in source_rows if row.get("animal_id", "").strip() in verification_by_id]
        if len(selected) != len(verification_by_id):
            found = {row.get("animal_id", "").strip() for row in selected}
            missing = sorted(set(verification_by_id) - found)
            raise SystemExit(f"Verification file references missing animal IDs: {missing[:10]}")
        return selected

    grouped: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    for index, row in enumerate(source_rows):
        grouped[normalize(row["animal_name"])].append((index, row))
    return [
        max(group, key=lambda item: source_row_score(item[1], item[0]))[1]
        for group in grouped.values()
    ]


def verification_for(row: dict[str, str], verification: dict[str, dict[str, object]]) -> dict[str, object]:
    for record in verification.values():
        if str(record.get("selected_animal_id")) == row["animal_id"].strip():
            return record
    return {}


def load_rows() -> list[dict[str, object]]:
    image_manifest = load_image_manifest()
    animal_verification = load_animal_verification()

    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [column for column in REQUIRED_SOURCE_COLUMNS if column not in reader.fieldnames]
        if missing_columns:
            raise SystemExit(f"Source CSV is missing required columns: {missing_columns}")

        source_rows = list(reader)
        if len(source_rows) != EXPECTED_SOURCE_ROWS:
            raise SystemExit(f"Expected {EXPECTED_SOURCE_ROWS} source rows, found {len(source_rows)}")

        animals: list[dict[str, object]] = []
        for row in dedupe_source_rows(source_rows, animal_verification):
            if CONTAMINATION_PATTERN.search(row["animal_name"]):
                raise SystemExit(f"Contaminated animal row detected: {row['animal_id']} {row['animal_name']}")

            verification = verification_for(row, animal_verification)
            source_scientific_name = row["scientific_name"].strip()
            verified_scientific_name = str(verification.get("verified_scientific_name") or "").strip()
            public_scientific_name = (
                verified_scientific_name
                or ("" if source_scientific_name == "Not specified" else source_scientific_name)
                or "Not specified"
            )
            minimum_family_group = parse_int(row, "minimum_family_group")
            minimum_group_space = parse_int(row, "minimum_group_space_sq_units")
            minimum_group_cost = parse_int(row, "minimum_group_cost_usd")
            research_query = public_scientific_name if public_scientific_name != "Not specified" else row["animal_name"].strip()

            animal = {
                "animal_id": row["animal_id"].strip(),
                "animal_name": row["animal_name"].strip(),
                "scientific_name": public_scientific_name,
                "source_scientific_name": source_scientific_name,
                "verified_scientific_name": verified_scientific_name,
                "verification_status": str(verification.get("verification_status") or "needs_review"),
                "verification_method": str(verification.get("verification_method") or "not_checked"),
                "primary_habitat": row["primary_habitat"].strip(),
                "world_region": row["world_region"].strip(),
                "space_first_animal_sq_units": parse_int(row, "space_first_animal_sq_units"),
                "space_each_additional_animal_sq_units": parse_int(row, "space_each_additional_animal_sq_units"),
                "minimum_family_group": minimum_family_group,
                "minimum_group_space_sq_units": minimum_group_space,
                "space_planning_sq_units": minimum_group_space,
                "space_planning_basis": f"Minimum group of {minimum_family_group}",
                "cost_per_animal_usd": parse_int(row, "cost_per_animal_usd"),
                "minimum_group_cost_usd": minimum_group_cost,
                "cost_planning_usd": minimum_group_cost,
                "cost_planning_basis": f"Minimum group of {minimum_family_group}",
                "swagg_revenue_equation": row["swagg_revenue_equation"].strip(),
                "suggested_enclosure_design_category": row["suggested_enclosure_design_category"].strip(),
                "suggested_physical_model_feature": row["suggested_physical_model_feature"].strip(),
                "curriculum_connections": row["curriculum_connections"].strip(),
                "data_note": row["data_note"].strip(),
                "student_info_url": str(verification.get("student_info_url") or research_url("https://biokids.umich.edu/critters/", research_query)),
                "animal_diversity_web_url": str(verification.get("animal_diversity_web_url") or research_url("https://animaldiversity.org/search/", research_query)),
                "gbif_url": str(verification.get("gbif_url") or research_url("https://www.gbif.org/species/search", research_query)),
                "inaturalist_url": str(verification.get("inaturalist_url") or research_url("https://www.inaturalist.org/search", row["animal_name"].strip())),
                "habitat_research_url": research_url("https://www.britannica.com/search", row["primary_habitat"].strip(), "query"),
                "region_research_url": research_url("https://www.britannica.com/search", row["world_region"].strip(), "query"),
                "animal_image_path": "",
                "image_alt": f"{row['animal_name'].strip()} image placeholder",
                "image_credit": "",
                "image_source": "",
                "image_license_name": "",
                "image_license_url": "",
                "image_provider": "",
            }
            animal.update(approved_image_for(image_manifest, animal["animal_name"]))
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
                "cost_min": min(int(row["cost_planning_usd"]) for row in rows),
                "cost_max": max(int(row["cost_planning_usd"]) for row in rows),
                "space_min": min(int(row["space_planning_sq_units"]) for row in rows),
                "space_max": max(int(row["space_planning_sq_units"]) for row in rows),
            }
        )

    return habitats


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audit_markdown(animals: list[dict[str, object]], habitats: list[dict[str, object]]) -> str:
    animal_names = [str(row["animal_name"]) for row in animals]
    duplicate_names = [name for name, count in Counter(animal_names).items() if count > 1]
    not_specified = sum(1 for row in animals if row["source_scientific_name"] == "Not specified")
    rows_with_images = sum(1 for row in animals if row.get("animal_image_path"))
    unique_images = len({str(row["animal_image_path"]) for row in animals if row.get("animal_image_path")})
    regions = {str(row["world_region"]) for row in animals}
    designs = Counter(str(row["suggested_enclosure_design_category"]) for row in animals)
    verification_statuses = Counter(str(row["verification_status"]) for row in animals)
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
- Source CSV rows reviewed: {EXPECTED_SOURCE_ROWS:,}
- Public animal entries: {len(animals):,}
- Unique animal names: {len(set(animal_names)):,}
- Duplicate animal names remaining: {len(duplicate_names):,}
- Duplicate source rows removed from public JSON: {EXPECTED_SOURCE_ROWS - len(animals):,}
- Habitats: {len(habitats):,}
- World/region labels: {len(regions):,}
- Kept rows whose source `scientific_name` was `Not specified`: {not_specified:,}
- Animal rows with approved images: {rows_with_images:,}
- Unique approved animal image files: {unique_images:,}

## Animal Verification

{chr(10).join(f"- {status}: {count:,}" for status, count in sorted(verification_statuses.items()))}

## Published Files

- `index.html`, `styles.css`, and `app.js` provide the student-facing database.
- `data/animals.json` contains the public animal-choice data plus Phase 2 image fields.
- `data/animal_verification.json` records duplicate cleanup, taxonomy status, and research links.
- `data/habitats.json` contains habitat summaries and habitat image paths.
- `assets/habitats/` contains the 50 copied habitat PNG assets.
- `scripts/validate_site.py` verifies the public site package before deployment.

## Excluded From Public Repo

- Raw Genspark conversation exports and tool activity logs.
- Teacher guides, answer materials, archives, and generated packet workspaces.
- The contaminated larger CSVs: `all_animals.csv`, `all_animals_final.csv`, and `all_animals_comprehensive.csv`.
- The polluted `animals/` markdown folder, which includes generated CSS/JavaScript fragments and extra non-student records.

## Data Quality Notes

- Duplicate animal-name rows were collapsed to one public row per normalized animal name.
- Space and cost planning columns use the minimum family/group size. First-animal and each-additional-animal values remain available for comparison.
- Classroom values are simplified for math modeling and are not real animal-care standards.
- Individual animal images are only published after batch approval. Every animal row includes `animal_image_path`, `image_alt`, `image_credit`, and `image_source` for the Phase 2 image pipeline.
- Approved image records also include `image_license_name`, `image_license_url`, and `image_provider`.
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
