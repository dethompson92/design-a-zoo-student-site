const PROJECT_BUDGET = 2500000;
const STORAGE_KEY = "designAZooLabState.v1";
const SPACE_REFERENCES = [
  { label: "middle school classrooms", area: 70 },
  { label: "basketball courts", area: 420 },
  { label: "American football fields", area: 5350 },
  { label: "small city blocks", area: 8000 },
];

const state = {
  animals: [],
  habitats: [],
  presets: { chance_models: [], sample_survey: { rows: [] } },
  activeTool: "probability",
  probability: {
    modelId: "visitor_habitat_choice",
    outcomes: [],
    lastResults: null,
  },
  surveyRows: [],
  samplingMethod: "Class-created sample",
  surveyLimitation: "The sample is useful for a model, but it may not represent every zoo visitor.",
  budgetRoster: [],
  budgetAdjustment: "0",
  customAdjustment: 0,
  constraint: {
    animalId: "",
    quantity: 1,
    shape: "rectangle",
    scale: 1,
    rectLength: 100,
    rectWidth: 80,
    triBase: 140,
    triHeight: 100,
    circleRadius: 55,
  },
};

const els = {
  labAnimalCount: document.getElementById("labAnimalCount"),
  labHabitatCount: document.getElementById("labHabitatCount"),
  labPhotoCount: document.getElementById("labPhotoCount"),
  labBudgetLeft: document.getElementById("labBudgetLeft"),
  probabilityModel: document.getElementById("probabilityModel"),
  trialCount: document.getElementById("trialCount"),
  runProbability: document.getElementById("runProbability"),
  addOutcome: document.getElementById("addOutcome"),
  outcomeRows: document.getElementById("outcomeRows"),
  sampleSpace: document.getElementById("sampleSpace"),
  probabilityChart: document.getElementById("probabilityChart"),
  probabilityStatus: document.getElementById("probabilityStatus"),
  probabilitySummary: document.getElementById("probabilitySummary"),
  copyProbabilitySummary: document.getElementById("copyProbabilitySummary"),
  samplingMethod: document.getElementById("samplingMethod"),
  surveyLimitation: document.getElementById("surveyLimitation"),
  loadSampleSurvey: document.getElementById("loadSampleSurvey"),
  addSurveyRow: document.getElementById("addSurveyRow"),
  surveyRows: document.getElementById("surveyRows"),
  surveyTotal: document.getElementById("surveyTotal"),
  surveyLargest: document.getElementById("surveyLargest"),
  surveyChart: document.getElementById("surveyChart"),
  surveySummary: document.getElementById("surveySummary"),
  copySurveySummary: document.getElementById("copySurveySummary"),
  animalSearch: document.getElementById("animalSearch"),
  budgetAdjustment: document.getElementById("budgetAdjustment"),
  customAdjustment: document.getElementById("customAdjustment"),
  animalSearchResults: document.getElementById("animalSearchResults"),
  budgetRows: document.getElementById("budgetRows"),
  animalCostTotal: document.getElementById("animalCostTotal"),
  adjustedCostTotal: document.getElementById("adjustedCostTotal"),
  revenueTotal: document.getElementById("revenueTotal"),
  budgetLeft: document.getElementById("budgetLeft"),
  budgetStatus: document.getElementById("budgetStatus"),
  budgetSummary: document.getElementById("budgetSummary"),
  copyBudgetSummary: document.getElementById("copyBudgetSummary"),
  constraintAnimal: document.getElementById("constraintAnimal"),
  constraintQuantity: document.getElementById("constraintQuantity"),
  shapeType: document.getElementById("shapeType"),
  scaleFactor: document.getElementById("scaleFactor"),
  rectangleFields: document.getElementById("rectangleFields"),
  triangleFields: document.getElementById("triangleFields"),
  circleFields: document.getElementById("circleFields"),
  rectLength: document.getElementById("rectLength"),
  rectWidth: document.getElementById("rectWidth"),
  triBase: document.getElementById("triBase"),
  triHeight: document.getElementById("triHeight"),
  circleRadius: document.getElementById("circleRadius"),
  requiredArea: document.getElementById("requiredArea"),
  studentArea: document.getElementById("studentArea"),
  areaDifference: document.getElementById("areaDifference"),
  constraintStatus: document.getElementById("constraintStatus"),
  constraintScale: document.getElementById("constraintScale"),
  constraintSummary: document.getElementById("constraintSummary"),
  copyConstraintSummary: document.getElementById("copyConstraintSummary"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatNumber(value, digits = 0) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: digits });
}

function formatMoney(value) {
  return `$${Math.round(Number(value || 0)).toLocaleString()}`;
}

function formatPercent(value) {
  return `${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
}

function clampNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function getAnimal(animalId) {
  return state.animals.find((animal) => animal.animal_id === animalId);
}

function getHabitat(name) {
  return state.habitats.find((habitat) => habitat.name === name);
}

function animalImageData(animal) {
  const habitat = getHabitat(animal.primary_habitat);
  return {
    path: animal.animal_image_path || (habitat && habitat.image_path) || "assets/habitats/habitat_06_african_savanna.png",
    alt: animal.animal_image_path ? animal.image_alt : `${animal.primary_habitat} habitat placeholder for ${animal.animal_name}`,
  };
}

function saveState() {
  const payload = {
    activeTool: state.activeTool,
    probability: {
      modelId: state.probability.modelId,
      outcomes: state.probability.outcomes,
    },
    surveyRows: state.surveyRows,
    samplingMethod: state.samplingMethod,
    surveyLimitation: state.surveyLimitation,
    budgetRoster: state.budgetRoster,
    budgetAdjustment: state.budgetAdjustment,
    customAdjustment: state.customAdjustment,
    constraint: state.constraint,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function loadSavedState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (saved.activeTool) state.activeTool = saved.activeTool;
    if (saved.probability) state.probability = { ...state.probability, ...saved.probability, lastResults: null };
    if (Array.isArray(saved.surveyRows)) state.surveyRows = saved.surveyRows;
    if (saved.samplingMethod) state.samplingMethod = saved.samplingMethod;
    if (saved.surveyLimitation) state.surveyLimitation = saved.surveyLimitation;
    if (Array.isArray(saved.budgetRoster)) state.budgetRoster = saved.budgetRoster;
    if (saved.budgetAdjustment) state.budgetAdjustment = saved.budgetAdjustment;
    if (typeof saved.customAdjustment !== "undefined") state.customAdjustment = saved.customAdjustment;
    if (saved.constraint) state.constraint = { ...state.constraint, ...saved.constraint };
  } catch (error) {
    console.warn("Saved Zoo Lab state could not be read.", error);
  }
}

function copyText(text, button) {
  if (!text.trim()) return;
  const finish = () => {
    const original = button.textContent;
    button.textContent = "Copied";
    window.setTimeout(() => {
      button.textContent = original;
    }, 1200);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(finish).catch(() => {
      fallbackCopy(text);
      finish();
    });
    return;
  }
  fallbackCopy(text);
  finish();
}

function fallbackCopy(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.append(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

function setupTabs() {
  document.querySelectorAll("[data-tool-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeTool = button.dataset.toolTab;
      renderTabs();
      saveState();
    });
  });
}

function renderTabs() {
  document.querySelectorAll("[data-tool-tab]").forEach((button) => {
    const active = button.dataset.toolTab === state.activeTool;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
  document.querySelectorAll(".tool-panel").forEach((panel) => {
    panel.classList.toggle("hidden", panel.id !== `${state.activeTool}Panel`);
  });
}

function setupProbability() {
  els.probabilityModel.innerHTML = state.presets.chance_models
    .map((model) => `<option value="${escapeHtml(model.id)}">${escapeHtml(model.name)}</option>`)
    .join("");
  els.probabilityModel.insertAdjacentHTML("beforeend", '<option value="custom">Custom model</option>');
  if (!state.probability.outcomes.length) {
    loadProbabilityModel(state.probability.modelId);
  }
  els.probabilityModel.value = state.probability.modelId;

  els.probabilityModel.addEventListener("change", () => {
    loadProbabilityModel(els.probabilityModel.value);
    state.probability.lastResults = null;
    renderProbability();
    saveState();
  });

  els.runProbability.addEventListener("click", runProbability);
  els.addOutcome.addEventListener("click", () => {
    state.probability.modelId = "custom";
    els.probabilityModel.value = "custom";
    state.probability.outcomes.push({ label: "New outcome", weight: 1 });
    renderProbability();
    saveState();
  });

  document.querySelectorAll("[data-trial-count]").forEach((button) => {
    button.addEventListener("click", () => {
      els.trialCount.value = button.dataset.trialCount;
      runProbability();
    });
  });

  els.outcomeRows.addEventListener("input", (event) => {
    const input = event.target.closest("[data-outcome-index]");
    if (!input) return;
    const index = Number(input.dataset.outcomeIndex);
    const field = input.dataset.outcomeField;
    state.probability.modelId = "custom";
    els.probabilityModel.value = "custom";
    state.probability.outcomes[index][field] = field === "weight" ? clampNumber(input.value, 0) : input.value;
    state.probability.lastResults = null;
    renderProbability();
    saveState();
  });

  els.outcomeRows.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove-outcome]");
    if (!button) return;
    state.probability.outcomes.splice(Number(button.dataset.removeOutcome), 1);
    state.probability.modelId = "custom";
    els.probabilityModel.value = "custom";
    state.probability.lastResults = null;
    renderProbability();
    saveState();
  });

  els.copyProbabilitySummary.addEventListener("click", () => {
    copyText(els.probabilitySummary.value, els.copyProbabilitySummary);
  });
}

function loadProbabilityModel(modelId) {
  const model = state.presets.chance_models.find((item) => item.id === modelId);
  state.probability.modelId = model ? model.id : "custom";
  if (model) {
    state.probability.outcomes = model.outcomes.map((outcome) => ({ ...outcome }));
  } else if (!state.probability.outcomes.length) {
    state.probability.outcomes = [
      { label: "Outcome A", weight: 1 },
      { label: "Outcome B", weight: 1 },
    ];
  }
}

function probabilityContext() {
  const model = state.presets.chance_models.find((item) => item.id === state.probability.modelId);
  return model ? model.context : "A custom zoo chance situation is modeled with weighted outcomes.";
}

function validOutcomes() {
  return state.probability.outcomes
    .map((outcome) => ({ label: String(outcome.label || "").trim(), weight: clampNumber(outcome.weight, 0) }))
    .filter((outcome) => outcome.label && outcome.weight > 0);
}

function renderProbability() {
  const outcomes = state.probability.outcomes;
  els.outcomeRows.innerHTML = outcomes
    .map(
      (outcome, index) => `
        <tr>
          <td><input aria-label="Outcome ${index + 1}" data-outcome-index="${index}" data-outcome-field="label" value="${escapeHtml(outcome.label)}"></td>
          <td><input aria-label="Weight for ${escapeHtml(outcome.label)}" type="number" min="0" step="1" data-outcome-index="${index}" data-outcome-field="weight" value="${escapeHtml(outcome.weight)}"></td>
          <td><button class="icon-button" type="button" data-remove-outcome="${index}" aria-label="Remove ${escapeHtml(outcome.label)}">x</button></td>
        </tr>
      `
    )
    .join("");

  const usable = validOutcomes();
  const totalWeight = usable.reduce((sum, outcome) => sum + outcome.weight, 0);
  els.sampleSpace.innerHTML = usable.length
    ? `<strong>Sample space:</strong> ${usable.map((outcome) => escapeHtml(outcome.label)).join(", ")}<br><strong>Total weight:</strong> ${formatNumber(totalWeight)}`
    : "Add at least one outcome with a positive weight.";

  if (!state.probability.lastResults) {
    els.probabilityChart.innerHTML = "";
    els.probabilityStatus.textContent = "Run trials to compare experimental and theoretical probability.";
    els.probabilitySummary.value = `Chance situation: ${probabilityContext()}\nSample space: ${usable.map((outcome) => outcome.label).join(", ")}\n`;
    return;
  }

  const results = state.probability.lastResults;
  els.probabilityStatus.textContent =
    results.trials >= 30
      ? `${formatNumber(results.trials)} trials completed.`
      : `${formatNumber(results.trials)} trials completed. The project target is at least 30 trials.`;
  els.probabilityChart.innerHTML = probabilityResultMarkup(results);
  els.probabilitySummary.value = probabilitySummaryText(results);
}

function runProbability() {
  const outcomes = validOutcomes();
  if (!outcomes.length) {
    els.probabilityStatus.textContent = "Add outcomes with positive weights before running the model.";
    return;
  }
  const trials = Math.max(1, Math.min(5000, Math.round(clampNumber(els.trialCount.value, 30))));
  els.trialCount.value = trials;
  const totalWeight = outcomes.reduce((sum, outcome) => sum + outcome.weight, 0);
  const counts = Object.fromEntries(outcomes.map((outcome) => [outcome.label, 0]));
  for (let index = 0; index < trials; index += 1) {
    const pick = Math.random() * totalWeight;
    let running = 0;
    for (const outcome of outcomes) {
      running += outcome.weight;
      if (pick <= running) {
        counts[outcome.label] += 1;
        break;
      }
    }
  }
  state.probability.lastResults = { outcomes, counts, trials, totalWeight, context: probabilityContext() };
  renderProbability();
  saveState();
}

function probabilityResultMarkup(results) {
  return results.outcomes
    .map((outcome) => {
      const count = results.counts[outcome.label] || 0;
      const experimental = (count / results.trials) * 100;
      const theoretical = (outcome.weight / results.totalWeight) * 100;
      return `
        <div class="chart-row">
          <div class="chart-label">
            <strong>${escapeHtml(outcome.label)}</strong>
            <span>${formatNumber(count)} trials | experimental ${formatPercent(experimental)} | theoretical ${formatPercent(theoretical)}</span>
          </div>
          <div class="bar-track" aria-hidden="true"><span style="width: ${Math.min(100, experimental)}%"></span></div>
        </div>
      `;
    })
    .join("");
}

function probabilitySummaryText(results) {
  const lines = [
    `Chance situation: ${results.context}`,
    `Trials: ${results.trials}`,
    `Sample space: ${results.outcomes.map((outcome) => outcome.label).join(", ")}`,
    "Results:",
  ];
  results.outcomes.forEach((outcome) => {
    const count = results.counts[outcome.label] || 0;
    lines.push(
      `- ${outcome.label}: ${count}/${results.trials} = ${formatPercent((count / results.trials) * 100)} experimental; ${formatPercent((outcome.weight / results.totalWeight) * 100)} theoretical`
    );
  });
  lines.push("Claim: The simulation suggests ____ because ____.");
  lines.push("Limitation: The model uses classroom weights, so ____.");
  return lines.join("\n");
}

function setupSurvey() {
  if (!state.surveyRows.length) {
    loadSampleSurvey();
  }
  els.samplingMethod.value = state.samplingMethod;
  els.surveyLimitation.value = state.surveyLimitation;

  els.samplingMethod.addEventListener("change", () => {
    state.samplingMethod = els.samplingMethod.value;
    renderSurvey();
    saveState();
  });
  els.surveyLimitation.addEventListener("input", () => {
    state.surveyLimitation = els.surveyLimitation.value;
    renderSurvey();
    saveState();
  });
  els.loadSampleSurvey.addEventListener("click", () => {
    loadSampleSurvey();
    renderSurvey();
    saveState();
  });
  els.addSurveyRow.addEventListener("click", () => {
    state.surveyRows.push({ category: "New category", count: 0 });
    renderSurvey();
    saveState();
  });
  els.surveyRows.addEventListener("input", (event) => {
    const input = event.target.closest("[data-survey-index]");
    if (!input) return;
    const index = Number(input.dataset.surveyIndex);
    const field = input.dataset.surveyField;
    state.surveyRows[index][field] = field === "count" ? Math.max(0, Math.round(clampNumber(input.value, 0))) : input.value;
    renderSurvey();
    saveState();
  });
  els.surveyRows.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove-survey]");
    if (!button) return;
    state.surveyRows.splice(Number(button.dataset.removeSurvey), 1);
    renderSurvey();
    saveState();
  });
  els.copySurveySummary.addEventListener("click", () => {
    copyText(els.surveySummary.value, els.copySurveySummary);
  });
}

function loadSampleSurvey() {
  const sample = state.presets.sample_survey || { rows: [] };
  state.surveyRows = sample.rows.map((row) => ({ ...row }));
  state.samplingMethod = sample.sampling_method || "Class-created sample";
  state.surveyLimitation = sample.limitation || "The sample may not represent every visitor.";
  if (els.samplingMethod) els.samplingMethod.value = state.samplingMethod;
  if (els.surveyLimitation) els.surveyLimitation.value = state.surveyLimitation;
}

function renderSurvey() {
  els.surveyRows.innerHTML = state.surveyRows
    .map(
      (row, index) => `
        <tr>
          <td><input aria-label="Survey category ${index + 1}" data-survey-index="${index}" data-survey-field="category" value="${escapeHtml(row.category)}"></td>
          <td><input aria-label="Survey count for ${escapeHtml(row.category)}" type="number" min="0" step="1" data-survey-index="${index}" data-survey-field="count" value="${escapeHtml(row.count)}"></td>
          <td><button class="icon-button" type="button" data-remove-survey="${index}" aria-label="Remove ${escapeHtml(row.category)}">x</button></td>
        </tr>
      `
    )
    .join("");

  const rows = state.surveyRows
    .map((row) => ({ category: String(row.category || "").trim(), count: Math.max(0, Math.round(clampNumber(row.count, 0))) }))
    .filter((row) => row.category);
  const total = rows.reduce((sum, row) => sum + row.count, 0);
  const largest = rows.reduce((best, row) => (row.count > (best?.count || -1) ? row : best), null);
  els.surveyTotal.textContent = formatNumber(total);
  els.surveyLargest.textContent = largest ? largest.category : "None";
  els.surveyChart.innerHTML = rows
    .map((row) => {
      const percent = total ? (row.count / total) * 100 : 0;
      return `
        <div class="chart-row">
          <div class="chart-label">
            <strong>${escapeHtml(row.category)}</strong>
            <span>${formatNumber(row.count)} responses | ${formatPercent(percent)} | relative frequency ${(percent / 100).toFixed(3)}</span>
          </div>
          <div class="bar-track" aria-hidden="true"><span style="width: ${Math.min(100, percent)}%"></span></div>
        </div>
      `;
    })
    .join("");
  els.surveySummary.value = surveySummaryText(rows, total, largest);
}

function surveySummaryText(rows, total, largest) {
  const lines = [
    `Survey question: Which zoo area would visitors most want to visit?`,
    `Sampling method: ${state.samplingMethod}`,
    `Total responses: ${total}`,
    "Data:",
  ];
  rows.forEach((row) => {
    const percent = total ? (row.count / total) * 100 : 0;
    lines.push(`- ${row.category}: ${row.count}/${total || 1} = ${formatPercent(percent)}; relative frequency ${(percent / 100).toFixed(3)}`);
  });
  lines.push(`Claim: The strongest category is ${largest ? largest.category : "____"}, so our zoo should consider ____.`);
  lines.push(`Limitation: ${state.surveyLimitation || "The sample may not represent every visitor."}`);
  return lines.join("\n");
}

function setupBudget() {
  els.budgetAdjustment.value = state.budgetAdjustment;
  els.customAdjustment.value = state.customAdjustment;
  els.animalSearch.addEventListener("input", renderAnimalSearch);
  els.budgetAdjustment.addEventListener("change", () => {
    state.budgetAdjustment = els.budgetAdjustment.value;
    renderBudget();
    saveState();
  });
  els.customAdjustment.addEventListener("input", () => {
    state.customAdjustment = clampNumber(els.customAdjustment.value, 0);
    renderBudget();
    saveState();
  });
  els.animalSearchResults.addEventListener("click", (event) => {
    const button = event.target.closest("[data-add-animal]");
    if (!button) return;
    addAnimalToRoster(button.dataset.addAnimal);
  });
  els.budgetRows.addEventListener("input", (event) => {
    const input = event.target.closest("[data-roster-index]");
    if (!input) return;
    const index = Number(input.dataset.rosterIndex);
    state.budgetRoster[index].quantity = Math.max(1, Math.round(clampNumber(input.value, 1)));
    renderBudget();
    saveState();
  });
  els.budgetRows.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove-roster]");
    if (!button) return;
    state.budgetRoster.splice(Number(button.dataset.removeRoster), 1);
    renderBudget();
    saveState();
  });
  els.copyBudgetSummary.addEventListener("click", () => {
    copyText(els.budgetSummary.value, els.copyBudgetSummary);
  });
}

function addAnimalToRoster(animalId) {
  const animal = getAnimal(animalId);
  if (!animal) return;
  const existing = state.budgetRoster.find((entry) => entry.animalId === animalId);
  if (existing) {
    existing.quantity = Math.max(existing.quantity + 1, animal.minimum_family_group);
  } else {
    state.budgetRoster.push({ animalId, quantity: animal.minimum_family_group });
  }
  renderBudget();
  saveState();
}

function renderAnimalSearch() {
  const query = els.animalSearch.value.trim().toLowerCase();
  const results = state.animals
    .filter((animal) => {
      const text = `${animal.animal_name} ${animal.primary_habitat} ${animal.world_region}`.toLowerCase();
      return !query || text.includes(query);
    })
    .slice(0, 10);

  els.animalSearchResults.innerHTML = results
    .map((animal) => {
      const image = animalImageData(animal);
      return `
        <article class="search-result-card">
          <img src="${escapeHtml(image.path)}" alt="${escapeHtml(image.alt)}" loading="lazy">
          <div>
            <strong>${escapeHtml(animal.animal_name)}</strong>
            <span>${escapeHtml(animal.primary_habitat)} | min group ${formatNumber(animal.minimum_family_group)}</span>
          </div>
          <button class="ghost-button" type="button" data-add-animal="${escapeHtml(animal.animal_id)}">Add</button>
        </article>
      `;
    })
    .join("");
}

function requiredSpace(animal, quantity) {
  const q = Math.max(1, Math.round(quantity));
  return animal.space_first_animal_sq_units + animal.space_each_additional_animal_sq_units * Math.max(0, q - 1);
}

function animalCost(animal, quantity) {
  return animal.cost_per_animal_usd * Math.max(1, Math.round(quantity));
}

function getBudgetAdjustmentPercent() {
  return state.budgetAdjustment === "custom" ? clampNumber(state.customAdjustment, 0) : clampNumber(state.budgetAdjustment, 0);
}

function renderBudget() {
  const rows = state.budgetRoster
    .map((entry) => ({ ...entry, animal: getAnimal(entry.animalId), quantity: Math.max(1, Math.round(clampNumber(entry.quantity, 1))) }))
    .filter((entry) => entry.animal);
  state.budgetRoster = rows.map((entry) => ({ animalId: entry.animalId, quantity: entry.quantity }));

  let costTotal = 0;
  let spaceTotal = 0;
  let revenueTotal = 0;
  const warnings = [];

  els.budgetRows.innerHTML = rows
    .map((entry, index) => {
      const animal = entry.animal;
      const q = entry.quantity;
      const rowCost = animalCost(animal, q);
      const rowSpace = requiredSpace(animal, q);
      const rowRevenue = evaluateSwagg(animal.swagg_revenue_equation, q);
      costTotal += rowCost;
      spaceTotal += rowSpace;
      if (Number.isFinite(rowRevenue)) revenueTotal += rowRevenue;
      if (q < animal.minimum_family_group) {
        warnings.push(`${animal.animal_name} needs at least ${animal.minimum_family_group}.`);
      }
      return `
        <tr class="${q < animal.minimum_family_group ? "warning-row" : ""}">
          <td><strong>${escapeHtml(animal.animal_name)}</strong><br><span class="table-note">${escapeHtml(animal.primary_habitat)}</span></td>
          <td><input class="quantity-input" aria-label="Quantity for ${escapeHtml(animal.animal_name)}" type="number" min="1" step="1" data-roster-index="${index}" value="${q}"></td>
          <td>${formatNumber(animal.minimum_family_group)}</td>
          <td>${formatNumber(rowSpace)} sq m</td>
          <td>${formatMoney(rowCost)}</td>
          <td><code>${escapeHtml(animal.swagg_revenue_equation)}</code></td>
          <td>${Number.isFinite(rowRevenue) ? formatMoney(rowRevenue) : "Check equation"}</td>
          <td><button class="icon-button" type="button" data-remove-roster="${index}" aria-label="Remove ${escapeHtml(animal.animal_name)}">x</button></td>
        </tr>
      `;
    })
    .join("");

  const percent = getBudgetAdjustmentPercent();
  const adjustedCost = costTotal * (1 + percent / 100);
  const budgetLeft = PROJECT_BUDGET - adjustedCost;
  const profitLoss = revenueTotal - adjustedCost;
  els.animalCostTotal.textContent = formatMoney(costTotal);
  els.adjustedCostTotal.textContent = formatMoney(adjustedCost);
  els.revenueTotal.textContent = formatMoney(revenueTotal);
  els.budgetLeft.textContent = formatMoney(budgetLeft);
  els.labBudgetLeft.textContent = formatMoney(budgetLeft);
  els.budgetStatus.textContent = warnings.length
    ? warnings.join(" ")
    : rows.length
      ? budgetLeft >= 0
        ? "Roster is within the classroom budget."
        : "Roster is over the classroom budget."
      : "Add animals to start a budget model.";
  els.budgetStatus.classList.toggle("danger-text", budgetLeft < 0 || warnings.length > 0);
  els.budgetSummary.value = budgetSummaryText(rows, costTotal, adjustedCost, budgetLeft, revenueTotal, profitLoss, spaceTotal, percent, warnings);
  updateLabMetrics(budgetLeft);
}

function safeMathExpression(expression, q) {
  let math = String(expression || "").split("=").pop();
  math = math.replace(/\s+/g, "").replace(/q/gi, `(${q})`);
  math = math.replace(/(\d|\))(?=\()/g, "$1*");
  math = math.replace(/\)(?=\d)/g, ")*");
  if (!/^[0-9+\-*/().]+$/.test(math)) return "";
  return math;
}

function evaluateSwagg(equation, q) {
  const math = safeMathExpression(equation, q);
  if (!math) return NaN;
  try {
    const value = Function(`"use strict"; return (${math});`)();
    return Number.isFinite(value) ? value : NaN;
  } catch {
    return NaN;
  }
}

function budgetSummaryText(rows, costTotal, adjustedCost, budgetLeft, revenueTotal, profitLoss, spaceTotal, percent, warnings) {
  const lines = [
    `Project budget: ${formatMoney(PROJECT_BUDGET)}`,
    `Animal roster entries: ${rows.length}`,
    `Animal cost before percent event: ${formatMoney(costTotal)}`,
    `Percent event: ${formatPercent(percent)}`,
    `Adjusted animal cost: ${formatMoney(adjustedCost)}`,
    `Budget left: ${formatMoney(budgetLeft)}`,
    `Total selected animal space: ${formatNumber(spaceTotal)} sq m`,
    `Year 1 SWAGG revenue estimate: ${formatMoney(revenueTotal)}`,
    `Revenue minus adjusted animal cost: ${formatMoney(profitLoss)}`,
    "Animals:",
  ];
  rows.forEach((entry) => {
    const animal = entry.animal;
    lines.push(
      `- ${animal.animal_name}: q=${entry.quantity}, min group=${animal.minimum_family_group}, cost=${formatMoney(animalCost(animal, entry.quantity))}, space=${formatNumber(requiredSpace(animal, entry.quantity))} sq m, SWAGG ${animal.swagg_revenue_equation}`
    );
  });
  if (warnings.length) lines.push(`Warnings: ${warnings.join(" ")}`);
  lines.push("Claim: Our zoo budget is ____ because ____.");
  return lines.join("\n");
}

function setupConstraint() {
  els.constraintAnimal.innerHTML = state.animals
    .map((animal) => `<option value="${escapeHtml(animal.animal_id)}">${escapeHtml(animal.animal_name)} - ${escapeHtml(animal.primary_habitat)}</option>`)
    .join("");
  if (!state.constraint.animalId) {
    state.constraint.animalId = state.animals[0]?.animal_id || "";
    const firstAnimal = getAnimal(state.constraint.animalId);
    state.constraint.quantity = firstAnimal ? firstAnimal.minimum_family_group : 1;
  }
  syncConstraintInputs();

  [
    els.constraintAnimal,
    els.constraintQuantity,
    els.shapeType,
    els.scaleFactor,
    els.rectLength,
    els.rectWidth,
    els.triBase,
    els.triHeight,
    els.circleRadius,
  ].forEach((input) => {
    input.addEventListener("input", () => {
      readConstraintInputs();
      renderConstraint();
      saveState();
    });
  });

  els.constraintAnimal.addEventListener("change", () => {
    state.constraint.animalId = els.constraintAnimal.value;
    const animal = getAnimal(state.constraint.animalId);
    if (animal) {
      state.constraint.quantity = Math.max(state.constraint.quantity, animal.minimum_family_group);
      els.constraintQuantity.value = state.constraint.quantity;
    }
    renderConstraint();
    saveState();
  });

  els.copyConstraintSummary.addEventListener("click", () => {
    copyText(els.constraintSummary.value, els.copyConstraintSummary);
  });
}

function syncConstraintInputs() {
  els.constraintAnimal.value = state.constraint.animalId;
  els.constraintQuantity.value = state.constraint.quantity;
  els.shapeType.value = state.constraint.shape;
  els.scaleFactor.value = state.constraint.scale;
  els.rectLength.value = state.constraint.rectLength;
  els.rectWidth.value = state.constraint.rectWidth;
  els.triBase.value = state.constraint.triBase;
  els.triHeight.value = state.constraint.triHeight;
  els.circleRadius.value = state.constraint.circleRadius;
}

function readConstraintInputs() {
  state.constraint = {
    animalId: els.constraintAnimal.value,
    quantity: Math.max(1, Math.round(clampNumber(els.constraintQuantity.value, 1))),
    shape: els.shapeType.value,
    scale: clampNumber(els.scaleFactor.value, 1),
    rectLength: clampNumber(els.rectLength.value, 0),
    rectWidth: clampNumber(els.rectWidth.value, 0),
    triBase: clampNumber(els.triBase.value, 0),
    triHeight: clampNumber(els.triHeight.value, 0),
    circleRadius: clampNumber(els.circleRadius.value, 0),
  };
}

function studentArea() {
  const scale = state.constraint.scale;
  if (state.constraint.shape === "triangle") {
    return ((state.constraint.triBase * scale) * (state.constraint.triHeight * scale)) / 2;
  }
  if (state.constraint.shape === "circle") {
    return Math.PI * (state.constraint.circleRadius * scale) ** 2;
  }
  return (state.constraint.rectLength * scale) * (state.constraint.rectWidth * scale);
}

function renderConstraint() {
  els.rectangleFields.classList.toggle("hidden", state.constraint.shape !== "rectangle");
  els.triangleFields.classList.toggle("hidden", state.constraint.shape !== "triangle");
  els.circleFields.classList.toggle("hidden", state.constraint.shape !== "circle");

  const animal = getAnimal(state.constraint.animalId);
  if (!animal) return;
  const quantity = Math.max(1, Math.round(state.constraint.quantity));
  const required = requiredSpace(animal, quantity);
  const actual = studentArea();
  const difference = actual - required;
  const minGroupOk = quantity >= animal.minimum_family_group;
  const fits = difference >= 0 && minGroupOk;
  els.requiredArea.textContent = `${formatNumber(required)} sq m`;
  els.studentArea.textContent = `${formatNumber(actual, 1)} sq m`;
  els.areaDifference.textContent = `${difference >= 0 ? "+" : ""}${formatNumber(difference, 1)} sq m`;
  els.constraintStatus.textContent = fits
    ? "This design meets the classroom area and minimum group checks."
    : !minGroupOk
      ? `Quantity is below the minimum group of ${animal.minimum_family_group}.`
      : "This design needs more area for the selected animal group.";
  els.constraintStatus.classList.toggle("danger-text", !fits);
  els.constraintScale.innerHTML = scaleCards(actual);
  els.constraintSummary.value = constraintSummaryText(animal, quantity, required, actual, difference, fits);
}

function scaleCards(area) {
  return SPACE_REFERENCES.map((reference) => {
    const count = area / reference.area;
    return `
      <div class="scale-card">
        <strong>${formatNumber(count, count >= 10 ? 1 : 2)}x</strong>
        <span>${escapeHtml(reference.label)}</span>
      </div>
    `;
  }).join("");
}

function constraintSummaryText(animal, quantity, required, actual, difference, fits) {
  return [
    `Animal: ${animal.animal_name}`,
    `Habitat: ${animal.primary_habitat}`,
    `Quantity: ${quantity}`,
    `Minimum group size: ${animal.minimum_family_group}`,
    `Required classroom area: ${formatNumber(required)} sq m`,
    `Student design area: ${formatNumber(actual, 1)} sq m`,
    `Difference: ${difference >= 0 ? "+" : ""}${formatNumber(difference, 1)} sq m`,
    `Result: ${fits ? "Meets the classroom checks" : "Needs revision"}`,
    `Space formula: first animal ${formatNumber(animal.space_first_animal_sq_units)} sq m + ${formatNumber(animal.space_each_additional_animal_sq_units)} sq m for each additional animal.`,
  ].join("\n");
}

function updateLabMetrics(budgetLeft = PROJECT_BUDGET) {
  els.labAnimalCount.textContent = formatNumber(state.animals.length);
  els.labHabitatCount.textContent = formatNumber(state.habitats.length);
  els.labPhotoCount.textContent = formatNumber(state.animals.filter((animal) => animal.animal_image_path).length);
  els.labBudgetLeft.textContent = formatMoney(budgetLeft);
}

async function init() {
  try {
    const [animalsResponse, habitatsResponse, presetsResponse] = await Promise.all([
      fetch("data/animals.json"),
      fetch("data/habitats.json"),
      fetch("data/zoo_lab_presets.json"),
    ]);
    if (!animalsResponse.ok || !habitatsResponse.ok || !presetsResponse.ok) {
      throw new Error("Unable to load Zoo Lab data.");
    }
    state.animals = await animalsResponse.json();
    state.habitats = await habitatsResponse.json();
    state.presets = await presetsResponse.json();
    loadSavedState();
    setupTabs();
    setupProbability();
    setupSurvey();
    setupBudget();
    setupConstraint();
    renderTabs();
    renderProbability();
    renderSurvey();
    renderAnimalSearch();
    renderBudget();
    renderConstraint();
  } catch (error) {
    document.querySelector(".lab-panels").innerHTML = '<section class="notice">Zoo Lab data could not be loaded.</section>';
    console.error(error);
  }
}

init();
