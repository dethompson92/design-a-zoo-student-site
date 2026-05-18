const SIZE_PAGE_SIZE = 48;
const SIZE_PROJECT_BUDGET = 2500000;
const SIZE_REFERENCES = [
  { label: "classrooms", area: 70 },
  { label: "basketball courts", area: 420 },
  { label: "football fields", area: 5350 },
];

const sizeState = {
  animals: [],
  filtered: [],
  visibleCount: SIZE_PAGE_SIZE,
};

const sizeEls = {
  search: document.getElementById("sizeSearch"),
  band: document.getElementById("sizeBandFilter"),
  habitat: document.getElementById("sizeHabitatFilter"),
  sort: document.getElementById("sizeSort"),
  examples: document.getElementById("sizeExamples"),
  meta: document.getElementById("sizeResultsMeta"),
  loadMore: document.getElementById("sizeLoadMore"),
};

function sizeEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function number(value) {
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function money(value) {
  return `$${Number(value).toLocaleString()}`;
}

function compactPercent(value) {
  const percent = Number(value);
  if (percent > 0 && percent < 0.1) {
    return "<0.1%";
  }
  return `${percent.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
}

function budgetPercent(animal) {
  return compactPercent((Number(animal.cost_planning_usd) / SIZE_PROJECT_BUDGET) * 100);
}

function sizeBand(area) {
  if (area <= 15000) return "compact";
  if (area <= 35000) return "medium";
  if (area <= 70000) return "large";
  return "campus";
}

function sizeBandLabel(area) {
  return {
    compact: "Compact",
    medium: "Medium",
    large: "Large",
    campus: "Campus-scale",
  }[sizeBand(area)];
}

function dimensionOptions(area) {
  const square = Math.sqrt(area);
  const twoToOneLong = Math.sqrt(area * 2);
  const twoToOneShort = area / twoToOneLong;
  const threeToTwoLong = Math.sqrt(area * 1.5);
  const threeToTwoShort = area / threeToTwoLong;
  return [
    { label: "Square", value: `${number(square)} m x ${number(square)} m` },
    { label: "Long rectangle", value: `${number(twoToOneLong)} m x ${number(twoToOneShort)} m` },
    { label: "Wide rectangle", value: `${number(threeToTwoLong)} m x ${number(threeToTwoShort)} m` },
  ];
}

function scaleLine(area) {
  return SIZE_REFERENCES.map((reference) => `${number(area / reference.area)} ${reference.label}`).join(" · ");
}

function setHabitatOptions() {
  const habitats = [...new Set(sizeState.animals.map((animal) => animal.primary_habitat))].sort();
  habitats.forEach((habitat) => {
    const option = document.createElement("option");
    option.value = habitat;
    option.textContent = habitat;
    sizeEls.habitat.append(option);
  });
}

function sortSizeExamples() {
  const key = sizeEls.sort.value;
  sizeState.filtered.sort((a, b) => {
    if (key === "space_desc") return Number(b.space_planning_sq_units) - Number(a.space_planning_sq_units);
    if (key === "animal_name") return a.animal_name.localeCompare(b.animal_name);
    return Number(a[key]) - Number(b[key]);
  });
}

function dimensionCard(animal) {
  const area = Number(animal.space_planning_sq_units);
  const options = dimensionOptions(area)
    .map((option) => `<div><span>${sizeEscape(option.label)}</span><strong>${sizeEscape(option.value)}</strong></div>`)
    .join("");
  return `
    <article class="dimension-card">
      <div class="dimension-head">
        <div>
          <p class="eyebrow">${sizeEscape(sizeBandLabel(area))}</p>
          <h3>${sizeEscape(animal.animal_name)}</h3>
          <p class="species">${sizeEscape(animal.scientific_name)}</p>
        </div>
        <span class="animal-id">${sizeEscape(animal.animal_id)}</span>
      </div>
      <div class="pill-row">
        <span class="pill">${sizeEscape(animal.primary_habitat)}</span>
        <span class="pill">${sizeEscape(animal.world_region)}</span>
      </div>
      <div class="modal-stat-row dimension-stats">
        <div><span>Minimum group area</span><strong>${number(area)} sq m</strong></div>
        <div><span>Minimum group</span><strong>${number(animal.minimum_family_group)}</strong></div>
        <div><span>Minimum group cost</span><strong>${money(animal.cost_planning_usd)}<span class="stat-subline">${budgetPercent(animal)} of budget</span></strong></div>
      </div>
      <div class="dimension-options">
        ${options}
      </div>
      <p class="basis-note">Scale: ${sizeEscape(scaleLine(area))}.</p>
      <p class="basis-note">Planning basis: ${sizeEscape(animal.space_planning_basis)}. First animal: ${number(animal.space_first_animal_sq_units)} sq m. Each additional: ${number(animal.space_each_additional_animal_sq_units)} sq m.</p>
      <p class="design-hint">${sizeEscape(animal.suggested_enclosure_design_category)}</p>
    </article>
  `;
}

function applySizeFilters() {
  const query = sizeEls.search.value.trim().toLowerCase();
  const band = sizeEls.band.value;
  const habitat = sizeEls.habitat.value;

  sizeState.filtered = sizeState.animals.filter((animal) => {
    const area = Number(animal.space_planning_sq_units);
    const text = [
      animal.animal_name,
      animal.scientific_name,
      animal.primary_habitat,
      animal.world_region,
      animal.suggested_enclosure_design_category,
    ]
      .join(" ")
      .toLowerCase();
    return (
      (!query || text.includes(query)) &&
      (!band || sizeBand(area) === band) &&
      (!habitat || animal.primary_habitat === habitat)
    );
  });

  sortSizeExamples();
  sizeState.visibleCount = SIZE_PAGE_SIZE;
  renderSizeExamples();
}

function renderSizeExamples() {
  const visible = sizeState.filtered.slice(0, sizeState.visibleCount);
  sizeEls.examples.innerHTML = visible.map(dimensionCard).join("");
  sizeEls.meta.textContent = `${visible.length.toLocaleString()} of ${sizeState.filtered.length.toLocaleString()} enclosure examples shown.`;
  sizeEls.loadMore.disabled = visible.length >= sizeState.filtered.length;
}

async function initSizeExamples() {
  const response = await fetch("data/animals.json");
  if (!response.ok) {
    sizeEls.meta.textContent = "The enclosure examples could not be loaded.";
    return;
  }
  sizeState.animals = await response.json();
  sizeState.filtered = [...sizeState.animals];
  setHabitatOptions();
  [sizeEls.search, sizeEls.band, sizeEls.habitat, sizeEls.sort].forEach((element) => {
    element.addEventListener("input", applySizeFilters);
  });
  sizeEls.loadMore.addEventListener("click", () => {
    sizeState.visibleCount += SIZE_PAGE_SIZE;
    renderSizeExamples();
  });
  applySizeFilters();
}

initSizeExamples();
