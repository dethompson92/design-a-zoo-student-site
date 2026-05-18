#!/usr/bin/env python3
"""Build the student geometry example gallery from the local worksheet image set."""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = (
    SITE_ROOT.parent
    / "Zoo"
    / "Zoo_Geometry_Worksheets_100_Images_Final_20260514_031256"
)
ASSET_ROOT = SITE_ROOT / "assets" / "geometry"
DATA_PATH = SITE_ROOT / "data" / "geometry_examples.json"
CATEGORY_DIR = SITE_ROOT / "geometry"

MAX_IMAGE_EDGE = 1200
WEBP_QUALITY = 84


CATEGORIES = [
    {
        "slug": "savanna-hoofstock-yards",
        "name": "Savanna & Hoofstock Yards",
        "description": "Paddocks, ranges, and feeding areas for grazing or large hoofed animals.",
    },
    {
        "slug": "big-cats-bears-predators",
        "name": "Big Cats, Bears & Predators",
        "description": "Examples for carnivore runs, predator habitats, and secure retreat areas.",
    },
    {
        "slug": "primates-small-mammals",
        "name": "Primates & Small Mammals",
        "description": "Yards, pavilions, islands, crossings, and villages for social mammals.",
    },
    {
        "slug": "birds-aviaries",
        "name": "Birds & Aviaries",
        "description": "Aviaries, raptor yards, bird sanctuaries, and flight-focused layouts.",
    },
    {
        "slug": "aquatic-wetland-exhibits",
        "name": "Aquatic & Wetland Exhibits",
        "description": "Pools, lagoons, coasts, marshes, marine spaces, and water-focused exhibits.",
    },
    {
        "slug": "reptiles-amphibians-insects",
        "name": "Reptiles, Amphibians & Insects",
        "description": "Terraces, corridors, care buildings, insectariums, and pollinator spaces.",
    },
    {
        "slug": "habitat-buildings-mixed-biomes",
        "name": "Habitat Buildings & Mixed Biomes",
        "description": "General habitat footprints, domes, themed buildings, and biome concepts.",
    },
    {
        "slug": "visitor-spaces-amenities",
        "name": "Visitor Spaces & Amenities",
        "description": "Plazas, cafes, gift shops, amphitheaters, decks, playgrounds, and guest spaces.",
    },
    {
        "slug": "education-research-conservation",
        "name": "Education, Research & Conservation",
        "description": "Learning centers, labs, conservation hubs, and public discovery spaces.",
    },
    {
        "slug": "care-staff-operations",
        "name": "Care, Staff & Operations",
        "description": "Veterinary, keeper, service, security, and backstage support buildings.",
    },
]

CATEGORY_LOOKUP = {item["slug"]: item for item in CATEGORIES}

CATEGORY_RULES = [
    ("care-staff-operations", [
        "veterinary",
        "quarantine",
        "keeper",
        "nutrition",
        "staff",
        "security",
        "service",
        "filtration",
        "gatehouse",
        "clinic",
        "medical",
        "workstation",
        "incubation",
        "conference",
        "tram",
    ]),
    ("education-research-conservation", [
        "education",
        "research",
        "conservation",
        "lab",
        "discovery",
        "training",
    ]),
    ("visitor-spaces-amenities", [
        "restroom",
        "concession",
        "gift",
        "shop",
        "cafe",
        "picnic",
        "playground",
        "welcome",
        "plaza",
        "amphitheater",
        "deck",
        "water_play",
        "directional",
        "visitor",
        "petting_zoo",
        "snack_bar",
    ]),
    ("reptiles-amphibians-insects", [
        "reptile",
        "amphibian",
        "crocodile",
        "butterfly",
        "insectarium",
        "pollinator",
    ]),
    ("aquatic-wetland-exhibits", [
        "walrus",
        "seal",
        "sea_lion",
        "otter",
        "penguin",
        "lagoon",
        "pool",
        "wetland",
        "marsh",
        "hippo",
        "aquarium",
        "sea_turtle",
        "marine",
        "coast",
    ]),
    ("birds-aviaries", [
        "owl",
        "aviary",
        "bird",
        "eagle",
        "raptor",
        "flamingo",
        "macaw",
        "ostrich",
    ]),
    ("primates-small-mammals", [
        "chimpanzee",
        "primate",
        "lemur",
        "meerkat",
        "small_mammal",
        "panda",
    ]),
    ("savanna-hoofstock-yards", [
        "rhino",
        "giraffe",
        "elephant",
        "zebra",
        "kangaroo",
        "moose",
        "hoofstock",
        "antelope",
        "mountain_goat",
        "goat",
        "savanna",
        "grassland",
    ]),
    ("big-cats-bears-predators", [
        "predator",
        "big_cat",
        "lion",
        "bear",
        "snow_leopard",
        "fox",
    ]),
]

ANIMAL_GROUP_RULES = [
    ("Primates", ["chimpanzee", "primate", "lemur"]),
    ("Small mammals", ["small_mammal", "meerkat", "panda"]),
    ("Hoofstock and large grazers", ["rhino", "giraffe", "elephant", "zebra", "kangaroo", "moose", "hoofstock", "antelope", "goat"]),
    ("Birds", ["owl", "aviary", "bird", "eagle", "raptor", "flamingo", "macaw", "ostrich"]),
    ("Aquatic animals", ["walrus", "seal", "sea_lion", "otter", "penguin", "sea_turtle", "hippo"]),
    ("Reptiles and amphibians", ["reptile", "crocodile", "amphibian"]),
    ("Insects and pollinators", ["butterfly", "insectarium", "pollinator"]),
    ("Predators", ["predator", "big_cat", "lion", "bear", "snow_leopard", "fox"]),
    ("Mixed species", ["mixed_species", "petting_zoo"]),
]

HABITAT_RULES = [
    ("Savanna or grassland", ["savanna", "grassland", "paddock", "range", "yard", "field"]),
    ("Rainforest or tropical", ["rainforest", "bamboo", "greenhouse"]),
    ("Aquatic or marine", ["pool", "lagoon", "marine", "aquarium", "coast", "cove", "otter", "seal", "walrus", "penguin"]),
    ("Wetland or marsh", ["wetland", "marsh", "crocodile", "hippo"]),
    ("Arctic or cold climate", ["arctic", "polar", "penguin", "snow"]),
    ("Desert or dry habitat", ["desert"]),
    ("Mountain or cliffs", ["mountain", "cliffs", "goat"]),
    ("Nocturnal or indoor habitat", ["nocturnal", "house", "building", "pavilion"]),
    ("Bird or aviary habitat", ["aviary", "bird", "raptor", "eagle", "macaw", "flamingo", "owl"]),
    ("Visitor or support area", ["plaza", "cafe", "gift", "shop", "clinic", "service", "staff", "keeper", "education", "research"]),
]

GEOMETRY_RULES = [
    ("Right triangle", ["right_triangle"]),
    ("Triangle composite", ["triangle_rectangle", "trapezoid_plus_triangle", "trapezoid_triangle", "nested_triangles"]),
    ("Trapezoid", ["trapezoid"]),
    ("Regular polygon", ["regular_pentagon", "regular_hexagon", "regular_octagon", "regular_decagon"]),
    ("Polygon", ["pentagon", "hexagon", "octagon", "decagon", "half_hexagon", "semi_octagon"]),
    ("Parallelogram", ["parallelogram"]),
    ("Circle and semicircle", ["semicircle", "circle", "circular", "quarter_circle", "double_semicircle", "concentric_circles", "triple_circle"]),
    ("Composite rectangles", ["l_shaped", "h_shaped", "t_shaped", "u_shaped", "e_shaped", "rectangle", "rectangular", "three_rectangle", "offset_rectangle", "nested_rectangles"]),
    ("Composite or mixed shape", ["composite", "mixed_species", "split_level", "split_diamond", "double_courtyard", "three_pod", "twin_dome"]),
    ("Irregular or organic", ["irregular", "notched", "asymmetric", "boomerang", "zigzag", "zig_zag", "maze", "wave", "canyon", "claw", "forked", "staggered"]),
    ("Radial or star-like", ["star", "starburst", "clover", "pinwheel", "honeycomb", "crown", "gemstone"]),
    ("Directional or path shape", ["arrow", "arrowhead", "chevron", "horseshoe", "crescent", "ring", "arch", "keyhole", "boat", "shield", "lightning", "herringbone", "sawtooth", "teardrop", "kite", "diamond", "bowtie", "fan"]),
]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def title_from_stem(stem: str) -> str:
    cleaned = re.sub(r"^\d+_", "", stem)
    return cleaned.replace("_", " ").title()


def first_match(stem: str, rules: list[tuple[str, list[str]]], default: str) -> str:
    for label, tokens in rules:
        if any(token in stem for token in tokens):
            return label
    return default


def category_for(stem: str) -> str:
    for slug, tokens in CATEGORY_RULES:
        if any(token in stem for token in tokens):
            return slug
    return "habitat-buildings-mixed-biomes"


def design_use_for(category_slug: str) -> str:
    if category_slug in {"visitor-spaces-amenities", "education-research-conservation", "care-staff-operations"}:
        return "Zoo building or support space"
    return "Animal enclosure or habitat concept"


def keywords_for(stem: str, *labels: str) -> list[str]:
    words = [word for word in stem.split("_") if word and not word.isdigit()]
    words.extend(label.lower() for label in labels)
    return sorted(set(words))


def relative(path: Path) -> str:
    return path.relative_to(SITE_ROOT).as_posix()


def clean_html_output(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.splitlines()) + "\n"


def optimize_image(source: Path, target: Path) -> tuple[int, int]:
    try:
        from PIL import Image  # type: ignore
    except ImportError as error:
        raise SystemExit("Pillow is required. Install it with: python3 -m pip install Pillow") from error

    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
        rgb = image.convert("RGB")
        rgb.save(target, "WEBP", quality=WEBP_QUALITY, method=6)
        return rgb.size


def card_html(entry: dict[str, object]) -> str:
    return f"""
      <article class="resource-card">
        <a class="resource-image-link" href="../{entry['asset_path']}" target="_blank" rel="noopener noreferrer">
          <img src="../{entry['asset_path']}" alt="{entry['title']} geometry example" loading="lazy">
        </a>
        <div class="resource-card-body">
          <p class="eyebrow">{entry['id']}</p>
          <h3>{entry['title']}</h3>
          <p>{entry['design_use']}</p>
          <div class="resource-meta">
            <span>{entry['animal_group']}</span>
            <span>{entry['habitat_theme']}</span>
            <span>{entry['geometry_type']}</span>
          </div>
          <a class="table-credit" href="../{entry['asset_path']}" target="_blank" rel="noopener noreferrer">Open image</a>
        </div>
      </article>
    """


def page_shell(title: str, active: str, body: str, prefix: str = "") -> str:
    nav = f"""
      <nav class="site-nav" aria-label="Student pages">
        <a class="{active == 'animals' and 'active' or ''}" href="{prefix}index.html">Animal Choices</a>
        <a class="{active == 'geometry' and 'active' or ''}" href="{prefix}geometry.html">Geometry Examples</a>
        <a class="{active == 'sizes' and 'active' or ''}" href="{prefix}enclosure-examples.html">Enclosure Sizes</a>
      </nav>
    """
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="Student-facing Design a Zoo geometry examples.">
    <link rel="stylesheet" href="{prefix}styles.css">
  </head>
  <body>
    <div class="app-shell student-page">
      <header class="topbar">
        <div>
          <p class="eyebrow">Student resources</p>
          <h1>{title}</h1>
        </div>
      </header>
      {nav}
      {body}
    </div>
  </body>
</html>
"""


def build_gallery_page(entries: list[dict[str, object]], counts: Counter[str]) -> None:
    category_cards = "\n".join(
        f"""
        <a class="category-link-card" href="geometry/{category['slug']}.html">
          <strong>{category['name']}</strong>
          <span>{counts[category['slug']]} examples</span>
          <p>{category['description']}</p>
        </a>
        """
        for category in CATEGORIES
    )
    body = f"""
      <section class="page-intro">
        <p>
          Browse 125 project-design images grouped by enclosure theme, animal type, habitat idea, and geometry shape.
          These are classroom planning examples for drawing zoo layouts, not real construction plans.
        </p>
      </section>

      <section class="category-list" aria-label="Geometry example categories">
        {category_cards}
      </section>

      <section class="resource-tools" aria-label="Find geometry examples">
        <div class="resource-field">
          <label for="geometrySearch">Search</label>
          <input id="geometrySearch" type="search" placeholder="Try penguin, rectangle, aviary, visitor, clinic">
        </div>
        <div class="resource-field">
          <label for="geometryCategoryFilter">Theme</label>
          <select id="geometryCategoryFilter"></select>
        </div>
        <div class="resource-field">
          <label for="geometryAnimalFilter">Animal type</label>
          <select id="geometryAnimalFilter"></select>
        </div>
        <div class="resource-field">
          <label for="geometryHabitatFilter">Habitat idea</label>
          <select id="geometryHabitatFilter"></select>
        </div>
        <div class="resource-field">
          <label for="geometryShapeFilter">Geometry type</label>
          <select id="geometryShapeFilter"></select>
        </div>
      </section>

      <p id="geometryResultsMeta" class="status-message" role="status"></p>
      <section id="geometryGallery" class="resource-grid" aria-label="Geometry example gallery"></section>
    """
    html = page_shell("Geometry Example Gallery", "geometry", body)
    html = html.replace("</body>", '    <script src="geometry-gallery.js"></script>\n  </body>')
    (SITE_ROOT / "geometry.html").write_text(clean_html_output(html), encoding="utf-8")


def build_category_pages(entries: list[dict[str, object]]) -> None:
    CATEGORY_DIR.mkdir(exist_ok=True)
    entries_by_category: dict[str, list[dict[str, object]]] = {category["slug"]: [] for category in CATEGORIES}
    for entry in entries:
        entries_by_category[str(entry["category_slug"])].append(entry)

    for category in CATEGORIES:
        category_entries = entries_by_category[category["slug"]]
        cards = "\n".join(card_html(entry) for entry in category_entries)
        body = f"""
          <section class="page-intro">
            <p>{category['description']}</p>
            <p>{len(category_entries)} examples are available in this theme.</p>
            <a class="ghost-button nav-button" href="../geometry.html">Back to all geometry examples</a>
          </section>
          <section class="resource-grid" aria-label="{category['name']} examples">
            {cards}
          </section>
        """
        html = page_shell(category["name"], "geometry", body, prefix="../")
        (CATEGORY_DIR / f"{category['slug']}.html").write_text(clean_html_output(html), encoding="utf-8")


def main() -> None:
    if not SOURCE_DIR.exists():
        raise SystemExit(f"Missing source directory: {SOURCE_DIR}")

    pngs = sorted(SOURCE_DIR.glob("*.png"))
    if len(pngs) != 125:
        raise SystemExit(f"Expected 125 PNG files, found {len(pngs)}")

    if ASSET_ROOT.exists():
        shutil.rmtree(ASSET_ROOT)
    entries: list[dict[str, object]] = []
    for source in pngs:
        stem = source.stem
        item_id = stem.split("_", 1)[0]
        title = title_from_stem(stem)
        category_slug = category_for(stem)
        category = CATEGORY_LOOKUP[category_slug]
        animal_group = first_match(stem, ANIMAL_GROUP_RULES, "Zoo facility or habitat")
        habitat_theme = first_match(stem, HABITAT_RULES, "General zoo design")
        geometry_type = first_match(stem, GEOMETRY_RULES, "Mixed geometry")
        slug = slugify(re.sub(r"^\d+_", "", stem))
        asset_path = ASSET_ROOT / category_slug / f"{item_id}_{slug}.webp"
        width, height = optimize_image(source, asset_path)
        entry = {
            "id": item_id,
            "title": title,
            "slug": slug,
            "source_filename": source.name,
            "asset_path": relative(asset_path),
            "category_slug": category_slug,
            "category": category["name"],
            "category_description": category["description"],
            "animal_group": animal_group,
            "habitat_theme": habitat_theme,
            "geometry_type": geometry_type,
            "design_use": design_use_for(category_slug),
            "keywords": keywords_for(stem, animal_group, habitat_theme, geometry_type, category["name"]),
            "width": width,
            "height": height,
        }
        entries.append(entry)

    DATA_PATH.write_text(json.dumps({"categories": CATEGORIES, "examples": entries}, indent=2) + "\n", encoding="utf-8")
    counts = Counter(str(entry["category_slug"]) for entry in entries)
    build_gallery_page(entries, counts)
    build_category_pages(entries)

    print(f"Built {len(entries):,} geometry examples across {len(CATEGORIES):,} categories.")
    for category in CATEGORIES:
        print(f"- {category['name']}: {counts[category['slug']]}")


if __name__ == "__main__":
    main()
