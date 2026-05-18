const PAGE_SIZE = 48;
const DEFAULT_SPOTLIGHT_IMAGE = "assets/habitats/habitat_06_african_savanna.png";

const state = {
  animals: [],
  habitats: [],
  filtered: [],
  visibleCount: PAGE_SIZE,
  view: "cards",
  sortKey: "animal_name",
};

const els = {
  totalEntries: document.getElementById("totalEntries"),
  totalHabitats: document.getElementById("totalHabitats"),
  visibleChoices: document.getElementById("visibleChoices"),
  uniqueAnimals: document.getElementById("uniqueAnimals"),
  searchInput: document.getElementById("searchInput"),
  habitatFilter: document.getElementById("habitatFilter"),
  regionFilter: document.getElementById("regionFilter"),
  designFilter: document.getElementById("designFilter"),
  maxCost: document.getElementById("maxCost"),
  maxSpace: document.getElementById("maxSpace"),
  resetFilters: document.getElementById("resetFilters"),
  sortSelect: document.getElementById("sortSelect"),
  cardViewButton: document.getElementById("cardViewButton"),
  tableViewButton: document.getElementById("tableViewButton"),
  cardResults: document.getElementById("cardResults"),
  tableResults: document.getElementById("tableResults"),
  animalTableBody: document.getElementById("animalTableBody"),
  loadMoreButton: document.getElementById("loadMoreButton"),
  pageMeta: document.getElementById("pageMeta"),
  resultsMeta: document.getElementById("resultsMeta"),
  statusMessage: document.getElementById("statusMessage"),
  habitatSpotlightImage: document.getElementById("habitatSpotlightImage"),
  habitatSpotlightTitle: document.getElementById("habitatSpotlightTitle"),
  habitatSpotlightMeta: document.getElementById("habitatSpotlightMeta"),
};

function formatNumber(value) {
  return Number(value).toLocaleString();
}

function formatMoney(value) {
  return `$${Number(value).toLocaleString()}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setOptions(select, values) {
  const first = select.querySelector("option");
  select.innerHTML = "";
  select.append(first);
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  });
}

function getHabitat(name) {
  return state.habitats.find((habitat) => habitat.name === name);
}

function setupFilters() {
  const regions = [...new Set(state.animals.map((animal) => animal.world_region))].sort();
  const designs = [...new Set(state.animals.map((animal) => animal.suggested_enclosure_design_category))].sort();
  setOptions(els.habitatFilter, state.habitats.map((habitat) => habitat.name));
  setOptions(els.regionFilter, regions);
  setOptions(els.designFilter, designs);
}

function applyFilters() {
  const query = els.searchInput.value.trim().toLowerCase();
  const habitat = els.habitatFilter.value;
  const region = els.regionFilter.value;
  const design = els.designFilter.value;
  const maxCost = els.maxCost.value ? Number(els.maxCost.value) : Infinity;
  const maxSpace = els.maxSpace.value ? Number(els.maxSpace.value) : Infinity;

  state.filtered = state.animals.filter((animal) => {
    const searchText = [
      animal.animal_id,
      animal.animal_name,
      animal.scientific_name,
      animal.primary_habitat,
      animal.world_region,
      animal.suggested_enclosure_design_category,
      animal.suggested_physical_model_feature,
    ]
      .join(" ")
      .toLowerCase();

    return (
      (!query || searchText.includes(query)) &&
      (!habitat || animal.primary_habitat === habitat) &&
      (!region || animal.world_region === region) &&
      (!design || animal.suggested_enclosure_design_category === design) &&
      Number(animal.cost_per_animal_usd) <= maxCost &&
      Number(animal.space_first_animal_sq_units) <= maxSpace
    );
  });

  sortAnimals();
  state.visibleCount = PAGE_SIZE;
  render();
}

function sortAnimals() {
  const key = state.sortKey;
  state.filtered.sort((a, b) => {
    const av = a[key];
    const bv = b[key];
    if (typeof av === "number" && typeof bv === "number") {
      return av - bv;
    }
    return String(av).localeCompare(String(bv));
  });
}

function renderMetrics() {
  els.totalEntries.textContent = formatNumber(state.animals.length);
  els.totalHabitats.textContent = formatNumber(state.habitats.length);
  els.visibleChoices.textContent = formatNumber(state.filtered.length);
  els.uniqueAnimals.textContent = formatNumber(new Set(state.animals.map((animal) => animal.animal_name)).size);
}

function renderSpotlight() {
  const selectedHabitat = els.habitatFilter.value;
  const habitat = selectedHabitat ? getHabitat(selectedHabitat) : null;

  if (!habitat) {
    els.habitatSpotlightImage.src = DEFAULT_SPOTLIGHT_IMAGE;
    els.habitatSpotlightImage.alt = "African savanna habitat preview";
    els.habitatSpotlightTitle.textContent = "All habitats";
    els.habitatSpotlightMeta.textContent = `${state.habitats.length} habitat choices are available for student zoo planning.`;
    return;
  }

  els.habitatSpotlightImage.src = habitat.image_path;
  els.habitatSpotlightImage.alt = `${habitat.name} habitat preview`;
  els.habitatSpotlightTitle.textContent = habitat.name;
  els.habitatSpotlightMeta.textContent =
    `${formatNumber(habitat.animal_count)} animal entries, ${formatNumber(habitat.region_count)} regions, ` +
    `${formatMoney(habitat.cost_min)} to ${formatMoney(habitat.cost_max)} per animal.`;
}

function animalImageMarkup(animal) {
  const habitat = getHabitat(animal.primary_habitat);
  const imagePath = animal.animal_image_path || (habitat ? habitat.image_path : DEFAULT_SPOTLIGHT_IMAGE);
  const alt = animal.animal_image_path
    ? animal.image_alt
    : `${animal.primary_habitat} habitat preview for ${animal.animal_name}`;
  const status = animal.animal_image_path ? "" : '<span class="image-status">Image pending</span>';
  const image = `<img src="${escapeHtml(imagePath)}" alt="${escapeHtml(alt)}" loading="lazy">`;
  const linkedImage = animal.animal_image_path && animal.image_source
    ? `<a class="animal-media-link" href="${escapeHtml(animal.image_source)}" target="_blank" rel="noopener noreferrer">${image}</a>`
    : image;
  return `
    <div class="animal-media">
      ${linkedImage}
      ${status}
    </div>
  `;
}

function imageCreditMarkup(animal) {
  if (!animal.animal_image_path) {
    return '<p class="photo-credit">Habitat placeholder shown until an animal photo is approved.</p>';
  }
  const credit = animal.image_credit || "Image credit";
  const license = animal.image_license_name ? ` · ${animal.image_license_name}` : "";
  const provider = animal.image_provider ? ` · ${animal.image_provider}` : "";
  return `
    <p class="photo-credit">
      Photo: <a href="${escapeHtml(animal.image_source)}" target="_blank" rel="noopener noreferrer">${escapeHtml(credit)}</a>${escapeHtml(license)}${escapeHtml(provider)}
    </p>
  `;
}

function cardTemplate(animal) {
  return `
    <article class="animal-card">
      ${animalImageMarkup(animal)}
      <div class="animal-body">
        <div class="animal-title-row">
          <h3>${escapeHtml(animal.animal_name)}</h3>
          <span class="animal-id">${escapeHtml(animal.animal_id)}</span>
        </div>
        <p class="species">${escapeHtml(animal.scientific_name)}</p>
        <div class="pill-row">
          <span class="pill">${escapeHtml(animal.primary_habitat)}</span>
          <span class="pill">${escapeHtml(animal.world_region)}</span>
        </div>
        <div class="quick-stats">
          <div><span>Space</span><strong>${formatNumber(animal.space_first_animal_sq_units)}</strong></div>
          <div><span>Group</span><strong>${formatNumber(animal.minimum_family_group)}</strong></div>
          <div><span>Cost</span><strong>${formatMoney(animal.cost_per_animal_usd)}</strong></div>
        </div>
        <p class="design-hint">${escapeHtml(animal.suggested_enclosure_design_category)}</p>
        <p class="equation">${escapeHtml(animal.swagg_revenue_equation)}</p>
        ${imageCreditMarkup(animal)}
      </div>
    </article>
  `;
}

function tableRowTemplate(animal) {
  const habitat = getHabitat(animal.primary_habitat);
  const imagePath = animal.animal_image_path || (habitat ? habitat.image_path : DEFAULT_SPOTLIGHT_IMAGE);
  const alt = animal.animal_image_path
    ? animal.image_alt
    : `${animal.primary_habitat} habitat preview for ${animal.animal_name}`;
  const creditHref = animal.animal_image_path && animal.image_source ? animal.image_source : "";
  return `
    <tr>
      <td>
        <img class="table-photo" src="${escapeHtml(imagePath)}" alt="${escapeHtml(alt)}" loading="lazy">
        ${
          creditHref
            ? `<a class="table-credit" href="${escapeHtml(creditHref)}" target="_blank" rel="noopener noreferrer">Credit</a>`
            : '<span class="table-credit">Pending</span>'
        }
      </td>
      <td><strong>${escapeHtml(animal.animal_name)}</strong><br><span class="species">${escapeHtml(animal.scientific_name)}</span></td>
      <td>${escapeHtml(animal.primary_habitat)}</td>
      <td>${escapeHtml(animal.world_region)}</td>
      <td>${formatNumber(animal.space_first_animal_sq_units)}</td>
      <td>${formatNumber(animal.minimum_family_group)}</td>
      <td>${formatMoney(animal.cost_per_animal_usd)}</td>
      <td>${escapeHtml(animal.suggested_enclosure_design_category)}</td>
    </tr>
  `;
}

function renderResults() {
  const visible = state.filtered.slice(0, state.visibleCount);
  els.cardResults.innerHTML = visible.map(cardTemplate).join("");
  els.animalTableBody.innerHTML = visible.map(tableRowTemplate).join("");

  const noun = state.filtered.length === 1 ? "choice" : "choices";
  els.resultsMeta.textContent = `${formatNumber(state.filtered.length)} ${noun} match the current filters.`;
  els.pageMeta.textContent = `Showing ${formatNumber(visible.length)} of ${formatNumber(state.filtered.length)}`;
  els.loadMoreButton.disabled = visible.length >= state.filtered.length;
  els.statusMessage.textContent = state.filtered.length ? "" : "No animals match the current filters.";
}

function renderView() {
  const cards = state.view === "cards";
  els.cardResults.classList.toggle("hidden", !cards);
  els.tableResults.classList.toggle("hidden", cards);
  els.cardViewButton.classList.toggle("active", cards);
  els.tableViewButton.classList.toggle("active", !cards);
}

function render() {
  renderMetrics();
  renderSpotlight();
  renderResults();
  renderView();
}

function resetFilters() {
  els.searchInput.value = "";
  els.habitatFilter.value = "";
  els.regionFilter.value = "";
  els.designFilter.value = "";
  els.maxCost.value = "";
  els.maxSpace.value = "";
  applyFilters();
}

function bindEvents() {
  [els.searchInput, els.habitatFilter, els.regionFilter, els.designFilter, els.maxCost, els.maxSpace].forEach((el) => {
    el.addEventListener("input", applyFilters);
  });

  els.resetFilters.addEventListener("click", resetFilters);
  els.sortSelect.addEventListener("change", () => {
    state.sortKey = els.sortSelect.value;
    sortAnimals();
    render();
  });

  els.cardViewButton.addEventListener("click", () => {
    state.view = "cards";
    renderView();
  });

  els.tableViewButton.addEventListener("click", () => {
    state.view = "table";
    renderView();
  });

  els.loadMoreButton.addEventListener("click", () => {
    state.visibleCount += PAGE_SIZE;
    renderResults();
  });
}

async function init() {
  try {
    const [animalsResponse, habitatsResponse] = await Promise.all([
      fetch("data/animals.json"),
      fetch("data/habitats.json"),
    ]);

    if (!animalsResponse.ok || !habitatsResponse.ok) {
      throw new Error("Unable to load site data.");
    }

    state.animals = await animalsResponse.json();
    state.habitats = await habitatsResponse.json();
    state.filtered = [...state.animals];
    setupFilters();
    bindEvents();
    applyFilters();
  } catch (error) {
    els.statusMessage.textContent = "The animal database could not be loaded.";
    console.error(error);
  }
}

init();
