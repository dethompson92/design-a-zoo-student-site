# Design a Zoo Public Student Website Audit

Generated: 2026-05-18 01:20:52

## Source of Truth

- Primary source CSV: `Design_a_Zoo_Exhibition_Capstone_Project_Packet_Package/zoo_animals_student_database_final.csv`
- Public animal entries: 1,844
- Unique animal names: 1,717
- Duplicate animal names kept as separate habitat choices: 124
- Habitats: 50
- World/region labels: 223
- Rows with `scientific_name = "Not specified"`: 296
- Animal rows with approved images: 0
- Unique approved animal image files: 0

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
- Individual animal images are only published after batch approval. Every animal row includes `animal_image_path`, `image_alt`, `image_credit`, and `image_source` for the Phase 2 image pipeline.
- Approved image records also include `image_license_name`, `image_license_url`, and `image_provider`.
- Habitat images are available now. Some student habitat labels needed explicit mapping to the closest existing habitat asset.

## Explicit Habitat Image Mappings

- Amphibian House -> assets/habitats/habitat_36_steaming_jungle_floor.png
- Flooded Forests (Varzea/Igapo) -> assets/habitats/habitat_45_flooded_forests.png
- Freshwater Swamp/Wetlands -> assets/habitats/habitat_15_freshwater_swamp.png
- Insectarium -> assets/habitats/habitat_39_micro_jungle_forest_floor.png
- Invertebrate House -> assets/habitats/habitat_40_tide_pool_micro_ecosystem.png
- Nocturnal House -> assets/habitats/habitat_33_nocturnal_forest.png
- Reptile House - Desert -> assets/habitats/habitat_37_deep_desert_dunes.png
- Reptile House - Tropical -> assets/habitats/habitat_38_wet_rainforest_understory.png
- South American Grasslands (Pampas) -> assets/habitats/habitat_08_south_american_pampas.png
- Temperate Aviary -> assets/habitats/habitat_34_temperate_forest_canopy.png
- Tropical Aviary -> assets/habitats/habitat_35_deep_tropical_jungle.png
- Tropical Coastal/Beach -> assets/habitats/habitat_20_tropical_coastal.png
- Urban/City Wildlife -> assets/habitats/habitat_43_reclaimed_abandoned_city.png

## Enclosure Design Categories

- Forest habitat with irregular polygon and canopy/branch zone: 305
- Water-and-land exhibit with rectangle plus semicircle/quarter-circle: 296
- Aquatic tank or lagoon composite with curved edge: 251
- Indoor habitat pod with composite rectangles and viewing window: 243
- Aviary or bird yard using regular polygon/apothem design: 226
- Themed building with irregular room layout: 169
- Rocky irregular polygon with triangular climbing zones: 140
- Large open paddock using trapezoid, pentagon, or composite polygon: 121
- Cold-climate yard with semicircle pool and polygon ice zone: 93
