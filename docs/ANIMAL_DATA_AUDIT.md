# Animal Data Audit

Generated: 2026-05-18 02:11:01

## Summary

- Source animal rows reviewed: 1,844
- Public rows after duplicate-name cleanup: 1,711
- Duplicate rows removed from public JSON: 133
- Duplicate-name groups reviewed: 129
- Kept rows still missing source scientific names: 191
- Confirmed fictional/made-up animals removed: 0

## Verification Status

- needs_review: 30
- verified: 1,681

## Verification Methods

- gbif_common_name_search: 30
- gbif_scientific_name: 1,466
- inaturalist_common_name: 188
- inaturalist_scientific_name: 24
- manual_review: 2
- manual_verified_name_fix: 1

## Duplicate Cleanup Policy

- One public row is kept per normalized animal name.
- Rows with a scientific name are preferred over rows marked `Not specified`.
- More specific regions are preferred over `Global`.
- The public row keeps the classroom math fields from the selected source row.
- Two ambiguous duplicate-name groups remain collapsed for student simplicity: `Fiddler Crab` and `Three-toed Woodpecker`.

## Duplicate Examples

- Kept ZA-0015 `Caracal` (African Savanna, Caracal caracal); removed duplicate rows: ZA-0973 (Nocturnal House, Caracal caracal)
- Kept ZA-0040 `Puff Adder` (African Savanna, Bitis arietans); removed duplicate rows: ZA-1767 (Tropical Rainforest - Floor, Bitis arietans)
- Kept ZA-0047 `Serval` (African Savanna, Leptailurus serval); removed duplicate rows: ZA-0988 (Nocturnal House, Leptailurus serval)
- Kept ZA-0094 `Alpine Accentor` (Alpine/Mountain, Prunella collaris); removed duplicate rows: ZA-0063 (Alpine Tundra, Not specified)
- Kept ZA-0095 `Alpine Chough` (Alpine/Mountain, Pyrrhocorax graculus); removed duplicate rows: ZA-0064 (Alpine Tundra, Not specified)
- Kept ZA-0096 `Alpine Ibex` (Alpine/Mountain, Capra ibex); removed duplicate rows: ZA-0065 (Alpine Tundra, Not specified)
- Kept ZA-0211 `Arctic Hare` (Arctic Tundra, Lepus arcticus); removed duplicate rows: ZA-0066 (Alpine Tundra, Not specified)
- Kept ZA-0102 `Argali` (Alpine/Mountain, Ovis ammon); removed duplicate rows: ZA-0067 (Alpine Tundra, Not specified)
- Kept ZA-1473 `Eurasian Lynx` (Temperate Coniferous Forest, Lynx lynx); removed duplicate rows: ZA-0071 (Alpine Tundra, Not specified)
- Kept ZA-0109 `Golden Eagle` (Alpine/Mountain, Aquila chrysaetos); removed duplicate rows: ZA-0072 (Alpine Tundra, Not specified), ZA-1528 (Temperate Deciduous Forest, Aquila chrysaetos)
- Kept ZA-0111 `Himalayan Tahr` (Alpine/Mountain, Hemitragus jemlahicus); removed duplicate rows: ZA-0077 (Alpine Tundra, Not specified)
- Kept ZA-0378 `Snow Leopard` (Cold Desert, Panthera uncia); removed duplicate rows: ZA-0083 (Alpine Tundra, Not specified)
- Kept ZA-1496 `Snowshoe Hare` (Temperate Coniferous Forest, Lepus americanus); removed duplicate rows: ZA-0085 (Alpine Tundra, Not specified)
- Kept ZA-1503 `Wolverine` (Temperate Coniferous Forest, Gulo gulo); removed duplicate rows: ZA-0091 (Alpine Tundra, Not specified)
- Kept ZA-0093 `Alpaca` (Alpine/Mountain, Vicugna pacos); removed duplicate rows: ZA-1042 (Páramo, Not specified)

## Student Research Links

- Each public animal row now includes BioKIDS, Animal Diversity Web, GBIF, and iNaturalist links where possible.
- GBIF is used for scientific taxonomy and accepted-name checking.
- BioKIDS and Animal Diversity Web are used as student-facing research starting points.
- iNaturalist is used for taxon pages, observations, and location context when available.

## Caveats

- This audit checks names against public taxonomy/search sources; it does not turn classroom space/cost values into real animal-care standards.
- Some common names map to subspecies or broad groups, so the verification status is a launch-quality filter, not a formal biological authority decision.
- Space and cost should be interpreted as classroom project values for the minimum group unless a row explicitly says otherwise.
