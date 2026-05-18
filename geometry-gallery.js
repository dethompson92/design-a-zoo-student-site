const galleryState = {
  categories: [],
  examples: [],
  filtered: [],
};

const galleryEls = {
  search: document.getElementById("geometrySearch"),
  category: document.getElementById("geometryCategoryFilter"),
  animal: document.getElementById("geometryAnimalFilter"),
  habitat: document.getElementById("geometryHabitatFilter"),
  shape: document.getElementById("geometryShapeFilter"),
  gallery: document.getElementById("geometryGallery"),
  meta: document.getElementById("geometryResultsMeta"),
};

function geometryEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setGalleryOptions(select, label, values) {
  select.innerHTML = "";
  const first = document.createElement("option");
  first.value = "";
  first.textContent = label;
  select.append(first);
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  });
}

function galleryCard(example) {
  return `
    <article class="resource-card">
      <a class="resource-image-link" href="${geometryEscape(example.asset_path)}" target="_blank" rel="noopener noreferrer">
        <img src="${geometryEscape(example.asset_path)}" alt="${geometryEscape(example.title)} geometry example" loading="lazy">
      </a>
      <div class="resource-card-body">
        <p class="eyebrow">${geometryEscape(example.id)}</p>
        <h3>${geometryEscape(example.title)}</h3>
        <p>${geometryEscape(example.design_use)}</p>
        <div class="resource-meta">
          <span>${geometryEscape(example.category)}</span>
          <span>${geometryEscape(example.animal_group)}</span>
          <span>${geometryEscape(example.geometry_type)}</span>
        </div>
        <div class="resource-actions">
          <a class="table-credit" href="geometry/${geometryEscape(example.category_slug)}.html">Theme page</a>
          <a class="table-credit" href="${geometryEscape(example.asset_path)}" target="_blank" rel="noopener noreferrer">Open image</a>
        </div>
      </div>
    </article>
  `;
}

function applyGalleryFilters() {
  const query = galleryEls.search.value.trim().toLowerCase();
  const category = galleryEls.category.value;
  const animal = galleryEls.animal.value;
  const habitat = galleryEls.habitat.value;
  const shape = galleryEls.shape.value;

  galleryState.filtered = galleryState.examples.filter((example) => {
    const text = [
      example.id,
      example.title,
      example.category,
      example.animal_group,
      example.habitat_theme,
      example.geometry_type,
      example.design_use,
      ...(example.keywords || []),
    ]
      .join(" ")
      .toLowerCase();

    return (
      (!query || text.includes(query)) &&
      (!category || example.category === category) &&
      (!animal || example.animal_group === animal) &&
      (!habitat || example.habitat_theme === habitat) &&
      (!shape || example.geometry_type === shape)
    );
  });

  galleryEls.gallery.innerHTML = galleryState.filtered.map(galleryCard).join("");
  galleryEls.meta.textContent = `${galleryState.filtered.length.toLocaleString()} of ${galleryState.examples.length.toLocaleString()} geometry examples shown.`;
}

async function initGeometryGallery() {
  const response = await fetch("data/geometry_examples.json");
  if (!response.ok) {
    galleryEls.meta.textContent = "The geometry gallery could not be loaded.";
    return;
  }
  const data = await response.json();
  galleryState.categories = data.categories;
  galleryState.examples = data.examples;
  galleryState.filtered = [...galleryState.examples];

  setGalleryOptions(galleryEls.category, "All themes", galleryState.categories.map((category) => category.name));
  setGalleryOptions(galleryEls.animal, "All animal types", [...new Set(galleryState.examples.map((item) => item.animal_group))].sort());
  setGalleryOptions(galleryEls.habitat, "All habitat ideas", [...new Set(galleryState.examples.map((item) => item.habitat_theme))].sort());
  setGalleryOptions(galleryEls.shape, "All geometry types", [...new Set(galleryState.examples.map((item) => item.geometry_type))].sort());

  [galleryEls.search, galleryEls.category, galleryEls.animal, galleryEls.habitat, galleryEls.shape].forEach((element) => {
    element.addEventListener("input", applyGalleryFilters);
  });
  applyGalleryFilters();
}

initGeometryGallery();
