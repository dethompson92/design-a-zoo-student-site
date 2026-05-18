#!/usr/bin/env python3
"""Deduplicate and verify animal names for the public student database."""

from __future__ import annotations

import csv
import json
import ssl
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    import certifi  # type: ignore
except ImportError:  # pragma: no cover - fallback for unusual local Python setups
    certifi = None


SITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SITE_ROOT.parent
SOURCE_CSV = PROJECT_ROOT / "Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package" / "zoo_animals_student_database_final.csv"
OUTPUT_PATH = SITE_ROOT / "data" / "animal_verification.json"
REPORT_PATH = SITE_ROOT / "docs" / "ANIMAL_DATA_AUDIT.md"
REVIEW_ROOT = SITE_ROOT / ".image-review" / "taxonomy-audit"
CACHE_PATH = REVIEW_ROOT / "taxonomy_cache.json"

USER_AGENT = "DesignAZooStudentSite/1.0 educational taxonomy audit"

MANUAL_NAME_FIXES = {
    "Ozark Blind Cavefish": {
        "verified_scientific_name": "Troglichthys rosae",
        "common_name": "Ozark Cavefish",
        "notes": "Source common name normalized from Ozark Blind Cavefish to the commonly used Ozark Cavefish.",
    },
}


def ssl_context() -> ssl.SSLContext | None:
    if certifi is None:
        return None
    return ssl.create_default_context(cafile=certifi.where())


SSL_CONTEXT = ssl_context()


def request_json(url: str, *, timeout: int = 12) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_key(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def research_url(base: str, query: str, param: str = "q") -> str:
    return f"{base}?{urllib.parse.urlencode({param: query})}"


def load_cache() -> dict[str, dict]:
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        cache.setdefault("gbif_match", {})
        cache.setdefault("gbif_search", {})
        cache.setdefault("inat", {})
        cache.setdefault("inat_unranked", {})
        return cache
    return {"gbif_match": {}, "gbif_search": {}, "inat": {}, "inat_unranked": {}}


def save_cache(cache: dict[str, dict]) -> None:
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def gbif_match(cache: dict[str, dict], name: str) -> dict:
    if name not in cache["gbif_match"]:
        url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode(
            {"name": name, "kingdom": "Animalia", "verbose": "true"}
        )
        try:
            cache["gbif_match"][name] = request_json(url)
        except Exception as exc:  # noqa: BLE001 - audit should keep going
            cache["gbif_match"][name] = {"_error": repr(exc)}
        time.sleep(0.02)
    return cache["gbif_match"][name]


def gbif_search(cache: dict[str, dict], query: str) -> dict:
    if query not in cache["gbif_search"]:
        url = "https://api.gbif.org/v1/species/search?" + urllib.parse.urlencode(
            {"q": query, "kingdom": "Animalia", "limit": "5"}
        )
        try:
            cache["gbif_search"][query] = request_json(url)
        except Exception as exc:  # noqa: BLE001 - audit should keep going
            cache["gbif_search"][query] = {"_error": repr(exc)}
        time.sleep(0.02)
    return cache["gbif_search"][query]


def inaturalist_search(cache: dict[str, dict], query: str, *, ranked: bool = True) -> dict:
    cache_key = "inat" if ranked else "inat_unranked"
    if query not in cache[cache_key]:
        params = {"q": query, "per_page": "5"}
        if ranked:
            params["rank"] = "species"
        url = "https://api.inaturalist.org/v1/taxa/autocomplete?" + urllib.parse.urlencode(params)
        try:
            cache[cache_key][query] = request_json(url)
        except Exception as exc:  # noqa: BLE001 - audit should keep going
            cache[cache_key][query] = {"_error": repr(exc)}
        time.sleep(0.02)
    return cache[cache_key][query]


def read_source_rows() -> list[dict[str, str]]:
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def row_score(row: dict[str, str], source_index: int) -> float:
    score = 0.0
    scientific_name = row["scientific_name"].strip()
    scientific_lower = scientific_name.lower()
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


def select_deduped_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for index, row in enumerate(rows):
        row = dict(row)
        row["_source_index"] = str(index)
        grouped[normalize_key(row["animal_name"])].append(row)

    selected = [
        max(group, key=lambda row: row_score(row, int(row["_source_index"])))
        for group in grouped.values()
    ]
    selected.sort(key=lambda row: row["animal_name"].lower())
    duplicate_groups = {key: group for key, group in grouped.items() if len(group) > 1}
    return selected, duplicate_groups


def gbif_record_is_verified(record: dict) -> bool:
    if not record or record.get("_error"):
        return False
    match_type = record.get("matchType")
    confidence = int(record.get("confidence") or 0)
    return (
        record.get("kingdom") == "Animalia"
        and match_type not in {None, "NONE", "HIGHERRANK"}
        and confidence >= 80
        and record.get("status") != "DOUBTFUL"
    )


def first_matching_inat_result(data: dict, animal_name: str, scientific_name: str) -> dict | None:
    if not data or data.get("_error"):
        return None
    animal_key = normalize_key(animal_name)
    scientific_key = normalize_key(scientific_name)
    for result in data.get("results") or []:
        result_name = normalize_key(str(result.get("name", "")))
        common_name = normalize_key(str(result.get("preferred_common_name", "")))
        if result_name in {animal_key, scientific_key} or common_name == animal_key:
            return result
    results = data.get("results") or []
    return results[0] if results else None


def first_gbif_search_result(data: dict) -> dict | None:
    if not data or data.get("_error"):
        return None
    for result in data.get("results") or []:
        if result.get("rank") in {"SPECIES", "SUBSPECIES", "GENUS"} and result.get("key"):
            return result
    return None


def verify_row(cache: dict[str, dict], row: dict[str, str]) -> dict[str, object]:
    animal_name = row["animal_name"].strip()
    scientific_name = row["scientific_name"].strip()
    manual_fix = MANUAL_NAME_FIXES.get(animal_name)

    gbif = None
    gbif_search_result = None
    inat_result = None
    method = "manual_review"
    status = "needs_review"
    verified_scientific_name = "" if scientific_name == "Not specified" else scientific_name
    verified_common_name = animal_name
    notes = ""

    if manual_fix:
        scientific_name_for_lookup = str(manual_fix["verified_scientific_name"])
        gbif = gbif_match(cache, scientific_name_for_lookup)
        inat_result = first_matching_inat_result(
            inaturalist_search(cache, scientific_name_for_lookup, ranked=False),
            str(manual_fix["common_name"]),
            scientific_name_for_lookup,
        )
        status = "verified"
        method = "manual_verified_name_fix"
        verified_scientific_name = scientific_name_for_lookup
        verified_common_name = str(manual_fix["common_name"])
        notes = str(manual_fix["notes"])
    elif scientific_name != "Not specified":
        gbif = gbif_match(cache, scientific_name)
        if gbif_record_is_verified(gbif):
            status = "verified"
            method = "gbif_scientific_name"
            verified_scientific_name = str(gbif.get("canonicalName") or scientific_name)
        else:
            inat_result = first_matching_inat_result(
                inaturalist_search(cache, scientific_name, ranked=False),
                animal_name,
                scientific_name,
            )
            if inat_result:
                status = "verified"
                method = "inaturalist_scientific_name"
                verified_scientific_name = str(inat_result.get("name") or scientific_name)
            else:
                gbif_search_result = first_gbif_search_result(gbif_search(cache, animal_name))
                if gbif_search_result:
                    status = "needs_review"
                    method = "gbif_common_name_search"
                    verified_scientific_name = str(gbif_search_result.get("canonicalName") or scientific_name)
    else:
        inat_result = first_matching_inat_result(
            inaturalist_search(cache, animal_name, ranked=True),
            animal_name,
            scientific_name,
        )
        if not inat_result:
            inat_result = first_matching_inat_result(
                inaturalist_search(cache, animal_name, ranked=False),
                animal_name,
                scientific_name,
            )
        if inat_result:
            status = "verified"
            method = "inaturalist_common_name"
            verified_scientific_name = str(inat_result.get("name") or "")
            verified_common_name = str(inat_result.get("preferred_common_name") or animal_name)
        else:
            gbif_search_result = first_gbif_search_result(gbif_search(cache, animal_name))
            if gbif_search_result:
                status = "verified"
                method = "gbif_common_name_search"
                verified_scientific_name = str(gbif_search_result.get("canonicalName") or "")
            else:
                status = "needs_review"
                method = "no_taxonomy_match"
                notes = "No external taxonomy match found; keep out of public data if later determined fictional."

    gbif_key = ""
    if gbif and gbif.get("usageKey"):
        gbif_key = str(gbif["usageKey"])
    elif gbif_search_result and gbif_search_result.get("key"):
        gbif_key = str(gbif_search_result["key"])

    inat_id = str(inat_result.get("id")) if inat_result and inat_result.get("id") else ""
    research_query_value = verified_scientific_name or animal_name

    return {
        "animal_name": animal_name,
        "selected_animal_id": row["animal_id"].strip(),
        "source_scientific_name": scientific_name,
        "verified_common_name": verified_common_name,
        "verified_scientific_name": verified_scientific_name,
        "verification_status": status,
        "verification_method": method,
        "publish_status": "publish" if status in {"verified", "needs_review"} else "exclude_non_real",
        "gbif_taxon_key": gbif_key,
        "gbif_url": f"https://www.gbif.org/species/{gbif_key}" if gbif_key else research_url("https://www.gbif.org/species/search", research_query_value),
        "inaturalist_taxon_id": inat_id,
        "inaturalist_url": f"https://www.inaturalist.org/taxa/{inat_id}" if inat_id else research_url("https://www.inaturalist.org/search", animal_name),
        "student_info_url": research_url("https://biokids.umich.edu/critters/", research_query_value),
        "animal_diversity_web_url": research_url("https://animaldiversity.org/search/", research_query_value),
        "notes": notes,
    }


def write_report(
    rows: list[dict[str, str]],
    selected_rows: list[dict[str, str]],
    duplicate_groups: dict[str, list[dict[str, str]]],
    verification: dict[str, dict[str, object]],
) -> None:
    status_counts = Counter(str(item["verification_status"]) for item in verification.values())
    method_counts = Counter(str(item["verification_method"]) for item in verification.values())
    not_specified_selected = sum(1 for row in selected_rows if row["scientific_name"].strip() == "Not specified")
    removed_duplicate_rows = len(rows) - len(selected_rows)
    duplicate_examples = []
    for group in duplicate_groups.values():
        selected_ids = {str(item["selected_animal_id"]) for item in verification.values()}
        kept = [row for row in group if row["animal_id"] in selected_ids]
        removed = [row for row in group if row["animal_id"] not in selected_ids]
        if kept and removed:
            duplicate_examples.append((kept[0], removed))
        if len(duplicate_examples) >= 15:
            break

    lines = [
        "# Animal Data Audit",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- Source animal rows reviewed: {len(rows):,}",
        f"- Public rows after duplicate-name cleanup: {len(selected_rows):,}",
        f"- Duplicate rows removed from public JSON: {removed_duplicate_rows:,}",
        f"- Duplicate-name groups reviewed: {len(duplicate_groups):,}",
        f"- Kept rows still missing source scientific names: {not_specified_selected:,}",
        "- Confirmed fictional/made-up animals removed: 0",
        "",
        "## Verification Status",
        "",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count:,}")

    lines.extend(["", "## Verification Methods", ""])
    for method, count in sorted(method_counts.items()):
        lines.append(f"- {method}: {count:,}")

    lines.extend(
        [
            "",
            "## Duplicate Cleanup Policy",
            "",
            "- One public row is kept per normalized animal name.",
            "- Rows with a scientific name are preferred over rows marked `Not specified`.",
            "- More specific regions are preferred over `Global`.",
            "- The public row keeps the classroom math fields from the selected source row.",
            "- Two ambiguous duplicate-name groups remain collapsed for student simplicity: `Fiddler Crab` and `Three-toed Woodpecker`.",
            "",
            "## Duplicate Examples",
            "",
        ]
    )
    for kept, removed in duplicate_examples:
        removed_bits = ", ".join(
            f"{row['animal_id']} ({row['primary_habitat']}, {row['scientific_name']})" for row in removed
        )
        lines.append(
            f"- Kept {kept['animal_id']} `{kept['animal_name']}` ({kept['primary_habitat']}, {kept['scientific_name']}); removed duplicate rows: {removed_bits}"
        )

    lines.extend(
        [
            "",
            "## Student Research Links",
            "",
            "- Each public animal row now includes BioKIDS, Animal Diversity Web, GBIF, and iNaturalist links where possible.",
            "- GBIF is used for scientific taxonomy and accepted-name checking.",
            "- BioKIDS and Animal Diversity Web are used as student-facing research starting points.",
            "- iNaturalist is used for taxon pages, observations, and location context when available.",
            "",
            "## Caveats",
            "",
            "- This audit checks names against public taxonomy/search sources; it does not turn classroom space/cost values into real animal-care standards.",
            "- Some common names map to subspecies or broad groups, so the verification status is a launch-quality filter, not a formal biological authority decision.",
            "- Space and cost should be interpreted as classroom project values for the minimum group unless a row explicitly says otherwise.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = read_source_rows()
    selected_rows, duplicate_groups = select_deduped_rows(rows)
    cache = load_cache()
    verification = {}
    for index, row in enumerate(selected_rows, start=1):
        verification[row["animal_name"].strip()] = verify_row(cache, row)
        if index % 100 == 0:
            save_cache(cache)
            print(f"Verified {index:,} animal names...")
    save_cache(cache)
    OUTPUT_PATH.write_text(json.dumps(verification, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(rows, selected_rows, duplicate_groups, verification)
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
