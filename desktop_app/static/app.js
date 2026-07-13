const analysisForm = document.getElementById("analysis-form");
const submitButton = document.getElementById("analysis-submit");
const parametroInput = document.getElementById("parametro");
const parametroDate = document.getElementById("parametro-date");
const parametroAdvanced = document.getElementById("parametro-advanced");
const parametroDateMode = document.querySelector('input[name="parametro_mode"][value="date"]');
const parametroAdvancedMode = document.querySelector('input[name="parametro_mode"][value="advanced"]');
const progressPanel = document.getElementById("progress-panel");
const progressBarFill = document.getElementById("progress-bar-fill");
const progressPercent = document.getElementById("progress-percent");
const progressMessage = document.getElementById("progress-message");
const messageBox = document.getElementById("message-box");
const messageText = document.getElementById("message-text");
const summaryPanel = document.getElementById("summary-panel");
const metricGrid = document.getElementById("metric-grid");
const boletinLabel = document.getElementById("boletin-label");
const resultsPanel = document.getElementById("results-panel");
const resultsCount = document.getElementById("results-count");
const primaryResultsBody = document.getElementById("primary-results-body");
const noRelevantBody = document.getElementById("no-relevant-body");
const discardedBody = document.getElementById("discarded-body");
const noRelevantCount = document.getElementById("no-relevant-count");
const discardedCount = document.getElementById("discarded-count");
const noRelevantFalseNegatives = document.getElementById("no-relevant-fn");
const discardedFalseNegatives = document.getElementById("discarded-fn");
const bulletinReviewPanel = document.getElementById("bulletin-review-panel");
const bulletinReviewForm = document.getElementById("bulletin-review-form");
const bulletinControl = document.getElementById("bulletin-control");
const bulletinSaveStatus = document.getElementById("bulletin-save-status");
const indicatorWeek = document.getElementById("indicator-week");
const indicatorVolumeGrid = document.getElementById("indicator-volume-grid");
const indicatorPerformanceGrid = document.getElementById("indicator-performance-grid");
const indicatorPeriod = document.getElementById("indicator-period");
const indicatorBulletinsBody = document.getElementById("indicator-bulletins-body");

let currentAnalysis = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setMessage(text, kind = "info") {
  messageText.textContent = text;
  messageBox.hidden = false;
  messageBox.className = `message message--${kind}`;
}

function getSelectedParametroMode() {
  const selected = document.querySelector('input[name="parametro_mode"]:checked');
  return selected ? selected.value : "latest";
}

function selectParametroMode(modeInput) {
  if (modeInput) {
    modeInput.checked = true;
  }
}

function formatApiDate(value) {
  const [year, month, day] = value.split("-");
  return `${day}-${month}-${year}`;
}

function formatDisplayDate(value) {
  const parts = String(value || "").split("-");
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : value || "-";
}

function resolveParametro() {
  const mode = getSelectedParametroMode();
  if (mode === "latest") {
    return "0";
  }
  if (mode === "date") {
    if (!parametroDate.value) {
      throw new Error("Seleccione una fecha para consultar un boletín retrospectivo.");
    }
    return formatApiDate(parametroDate.value);
  }
  const value = parametroAdvanced.value.trim();
  if (!value) {
    throw new Error("Ingrese un número de boletín o parámetro admitido por la API.");
  }
  return value;
}

function setupTabs() {
  document.querySelectorAll("[data-tab-target]").forEach((button) => {
    button.addEventListener("click", async () => {
      const target = button.dataset.tabTarget;
      document.querySelectorAll("[data-tab-target]").forEach((item) => {
        const active = item.dataset.tabTarget === target;
        item.classList.toggle("app-tabs__button--active", active);
        item.setAttribute("aria-selected", String(active));
      });
      document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
        panel.hidden = panel.dataset.tabPanel !== target;
      });
      if (target === "indicators") {
        await loadWeeks();
        await loadIndicators();
      }
    });
  });
}

function updateProgress(job) {
  progressPanel.hidden = false;
  progressBarFill.style.width = `${job.progress_percent || 0}%`;
  progressPercent.textContent = `${job.progress_percent || 0}%`;
  progressMessage.textContent = job.message || "Procesando...";
}

function clearPanels() {
  currentAnalysis = null;
  primaryResultsBody.innerHTML = "";
  noRelevantBody.innerHTML = "";
  discardedBody.innerHTML = "";
  resultsCount.textContent = "0 normas";
  resultsPanel.hidden = true;
  summaryPanel.hidden = true;
  bulletinReviewPanel.hidden = true;
}

function renderSummary(summary) {
  const numero = summary.numero_boletin || "";
  boletinLabel.textContent = numero ? `BO ${numero}` : "BO";
  metricGrid.innerHTML = [
    ["Fecha", summary.fecha_publicacion || "-"],
    ["Normas procesadas", summary.total_normas ?? 0],
    ["Relevantes", summary.relevantes ?? 0],
    ["Revisión manual", summary.revision_manual ?? 0],
    ["No relevantes", summary.no_relevantes ?? 0],
    ["Descartadas", summary.descartadas ?? 0],
  ].map(([label, value]) => `
    <article class="metric-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </article>
  `).join("");
  summaryPanel.hidden = false;
}

function decisionChoices(result, hiddenCategory) {
  const choices = hiddenCategory
    ? [
        ["RELEVANTE_CONFIRMADA", "Es relevante"],
      ]
    : [
        ["RELEVANTE_CONFIRMADA", "Relevante"],
        ["NO_RELEVANTE_CONFIRMADA", "No relevante"],
      ];
  return choices.map(([value, label]) => `
    <label class="decision-choice">
      <input type="checkbox" data-review-decision value="${value}" ${result.decision_manual === value ? "checked" : ""}>
      <span>${label}</span>
    </label>
  `).join("");
}

function resultRow(result, hiddenCategory = false) {
  const anexos = (result.anexos || []).map((anexo) => `
    <a href="${escapeHtml(anexo.url)}" target="_blank" rel="noopener">${escapeHtml(anexo.nombre_anexo || "Anexo")}</a>
  `).join("");
  const links = [
    result.url_norma ? `<a href="${escapeHtml(result.url_norma)}" target="_blank" rel="noopener">Texto oficial</a>` : "",
    anexos,
  ].filter(Boolean).join("<br>");
  const searchable = [
    result.nombre,
    result.organismo,
    result.sumario,
    result.tipo_norma,
  ].join(" ").toLocaleLowerCase("es");
  const falseNegative = hiddenCategory && result.decision_manual === "RELEVANTE_CONFIRMADA";

  return `
    <tr data-result-key="${escapeHtml(result.clave_registro)}" data-search="${escapeHtml(searchable)}" class="${falseNegative ? "row--false-negative" : ""}">
      <td>
        <span class="category-badge category-${escapeHtml(result.categoria_automatica_original)}">
          ${escapeHtml(result.categoria_original_label)}
        </span>
      </td>
      <td>
        <strong>${escapeHtml(result.nombre)}</strong>
        <small>${escapeHtml(result.poder)} / ${escapeHtml(result.tipo_norma)}</small>
      </td>
      <td>${escapeHtml(result.organismo)}</td>
      <td>
        <p class="sumario">${escapeHtml(result.sumario)}</p>
        <p class="motivo">${escapeHtml(result.motivo_label || "Sin motivo informado")}</p>
      </td>
      <td class="review-cell">
        <div class="decision-options">
          ${decisionChoices(result, hiddenCategory)}
        </div>
        ${hiddenCategory ? `
        <label class="fn-evidence" ${falseNegative ? "" : "hidden"}>
          <span>Evidencia breve obligatoria</span>
          <textarea data-review-observation rows="2">${escapeHtml(result.observacion_revision || "")}</textarea>
        </label>` : ""}
        <button type="button" class="button-secondary save-review">Guardar decisión</button>
        <small class="save-status" aria-live="polite"></small>
      </td>
      <td class="links-cell">${links || "<span>Sin enlace</span>"}</td>
    </tr>
  `;
}

function renderCategoryBody(body, results, hiddenCategory) {
  if (!results.length) {
    body.innerHTML = '<tr><td colspan="6" class="empty-state">No hay registros en esta categoría.</td></tr>';
    return;
  }
  body.innerHTML = results.map((result) => resultRow(result, hiddenCategory)).join("");
}

function renderResults(results) {
  const grouped = {
    RELEVANTE: [],
    REVISION_MANUAL: [],
    NO_RELEVANTE: [],
    DESCARTADA_FILTRO_ESTRUCTURAL: [],
  };
  results.forEach((result) => {
    const category = result.categoria_automatica_original || result.categoria_salida;
    if (grouped[category]) {
      grouped[category].push(result);
    }
  });

  const primary = [...grouped.RELEVANTE, ...grouped.REVISION_MANUAL];
  renderCategoryBody(primaryResultsBody, primary, false);
  renderCategoryBody(noRelevantBody, grouped.NO_RELEVANTE, true);
  renderCategoryBody(discardedBody, grouped.DESCARTADA_FILTRO_ESTRUCTURAL, true);

  resultsCount.textContent = primary.length === 1 ? "1 norma" : `${primary.length} normas`;
  noRelevantCount.textContent = String(grouped.NO_RELEVANTE.length);
  discardedCount.textContent = String(grouped.DESCARTADA_FILTRO_ESTRUCTURAL.length);
  updateFalseNegativeBadges(results);
  resultsPanel.hidden = false;
}

function updateFalseNegativeBadges(results) {
  const countFor = (category) => results.filter((result) =>
    result.categoria_automatica_original === category &&
    result.decision_manual === "RELEVANTE_CONFIRMADA"
  ).length;
  noRelevantFalseNegatives.textContent = `${countFor("NO_RELEVANTE")} falsos negativos`;
  discardedFalseNegatives.textContent = `${countFor("DESCARTADA_FILTRO_ESTRUCTURAL")} falsos negativos`;
}

async function saveNormReview(button) {
  const row = button.closest("[data-result-key]");
  const key = row.dataset.resultKey;
  const selectedDecision = row.querySelector("[data-review-decision]:checked");
  const decision = selectedDecision ? selectedDecision.value : "SIN_REVISAR";
  const evidenceField = row.querySelector("[data-review-observation]");
  const observation = decision === "RELEVANTE_CONFIRMADA" && evidenceField ? evidenceField.value.trim() : "";
  const status = row.querySelector(".save-status");

  status.classList.remove("save-status--error");
  if (evidenceField && decision === "RELEVANTE_CONFIRMADA" && !observation) {
    status.textContent = "Ingrese una evidencia breve antes de guardar.";
    status.classList.add("save-status--error");
    return;
  }

  button.disabled = true;
  status.textContent = "Guardando...";

  try {
    const response = await fetch("/api/review/norma", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        semana: currentAnalysis.summary.semana,
        boletin_clave: currentAnalysis.summary.boletin_clave,
        clave_registro: key,
        decision_manual: decision,
        observacion: observation,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.message || "No se pudo guardar la decisión.");
    }
    const result = currentAnalysis.results.find((item) => item.clave_registro === key);
    result.decision_manual = payload.decision_manual;
    result.observacion_revision = payload.observacion_revision;
    row.classList.toggle("row--false-negative", payload.es_falso_negativo);
    updateFalseNegativeBadges(currentAnalysis.results);
    status.classList.remove("save-status--error");
    status.textContent = payload.es_falso_negativo ? "Falso negativo registrado." : "Decisión guardada.";
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("save-status--error");
  } finally {
    button.disabled = false;
  }
}

function setBulletinControl(value) {
  const normalizedValue = value || "PENDIENTE";
  const inputs = [...bulletinControl.querySelectorAll('input[type="checkbox"]')];
  inputs.forEach((input) => {
    input.checked = input.value === normalizedValue;
  });
  if (!inputs.some((input) => input.checked) && inputs.length) {
    inputs[0].checked = true;
  }
}

function getBulletinControl() {
  const selected = bulletinControl.querySelector('input[type="checkbox"]:checked');
  return selected ? selected.value : "PENDIENTE";
}

async function pollJob(jobId) {
  while (true) {
    const response = await fetch(`/api/analyze/${jobId}`);
    const job = await response.json();
    updateProgress(job);

    if (job.status === "completed") {
      currentAnalysis = job;
      renderSummary(job.summary || {});
      renderResults(job.results || []);
      setBulletinControl(job.summary.control_complementario || "PENDIENTE");
      bulletinSaveStatus.textContent = "";
      bulletinSaveStatus.classList.remove("save-status--error");
      bulletinReviewPanel.hidden = false;
      setMessage(job.message || "Análisis finalizado.", "success");
      progressPanel.hidden = true;
      submitButton.disabled = false;
      return;
    }
    if (job.status === "error") {
      clearPanels();
      setMessage(job.message || "El análisis falló.", "error");
      progressPanel.hidden = true;
      submitButton.disabled = false;
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 700));
  }
}

async function loadWeeks() {
  const response = await fetch("/api/indicators/weeks");
  const payload = await response.json();
  const previous = indicatorWeek.value;
  indicatorWeek.innerHTML = payload.weeks.map((week) =>
    `<option value="${escapeHtml(week)}">${escapeHtml(week)}</option>`
  ).join("");
  indicatorWeek.value = payload.weeks.includes(previous) ? previous : payload.current_week;
}

function formatPercentageIndicator(value) {
  return typeof value === "number"
    ? value.toLocaleString("es-AR", {maximumFractionDigits: 1}) + " %"
    : value;
}

function renderMetricCards(container, items, performance = false) {
  container.innerHTML = items.map(([label, value, description, detail]) => (
    '<article class="metric-card' + (performance ? ' metric-card--performance' : '') + '">' +
      '<span>' + escapeHtml(label) + '</span>' +
      '<strong>' + escapeHtml(value) + '</strong>' +
      (description ? '<p class="metric-card__description">' + escapeHtml(description) + '</p>' : '') +
      (detail ? '<small class="metric-card__detail">' + escapeHtml(detail) + '</small>' : '') +
    '</article>'
  )).join("");
}

async function loadIndicators() {
  if (!indicatorWeek.value) {
    return;
  }
  const response = await fetch(`/api/indicators?week=${encodeURIComponent(indicatorWeek.value)}`);
  const data = await response.json();
  if (!response.ok) {
    setMessage(data.message || "No se pudieron cargar los indicadores.", "error");
    return;
  }
  const period = data.periodo || {};
  indicatorPeriod.textContent = `${formatDisplayDate(period.desde)} a ${formatDisplayDate(period.hasta)}`;
  renderMetricCards(indicatorVolumeGrid, [
    ["Días de uso", data.dias_uso],
    ["Normas procesadas", data.normas_procesadas],
    ["Relevantes automáticas", data.relevantes],
    ["Revisión manual", data.revision_manual],
    ["Relevantes confirmadas", data.relevantes_confirmadas_total],
    ["Desde revisión manual", data.relevantes_desde_revision_manual],
    ["Falsos negativos", data.falsos_negativos],
    ["Control complementario", data.control_complementario],
  ]);

  const bases = data.bases_desempeno || {};
  renderMetricCards(indicatorPerformanceGrid, [
    [
      "Cobertura de validación",
      formatPercentageIndicator(data.cobertura_validacion),
      "Porcentaje de normas procesadas que ya tienen una decisión profesional.",
      "Base: " + (bases.normas_validadas || 0) + " normas con decisión",
    ],
    [
      "Precisión automática",
      formatPercentageIndicator(data.precision_automatica),
      "Proporción de alertas automáticas validadas que resultaron relevantes.",
      "Base: " + (bases.alertas_automaticas_validadas || 0) + " alertas validadas",
    ],
    [
      "Falsos positivos",
      formatPercentageIndicator(data.tasa_falsos_positivos),
      "Proporción de alertas automáticas validadas que se descartaron.",
      "Base: " + (bases.alertas_automaticas_validadas || 0) + " alertas validadas",
    ],
    [
      "Tasa de revisión manual",
      formatPercentageIndicator(data.tasa_revision_manual),
      "Parte de las normas procesadas que el detector derivó a revisión humana.",
      "Base: " + data.normas_procesadas + " normas procesadas",
    ],
    [
      "Rendimiento de revisión",
      formatPercentageIndicator(data.rendimiento_revision_manual),
      "Proporción de los casos revisados manualmente que resultaron relevantes.",
      "Base: " + (bases.casos_revision_manual_validados || 0) + " casos resueltos",
    ],
    [
      "Reducción de lectura",
      formatPercentageIndicator(data.reduccion_lectura),
      "Porcentaje del boletín que quedó fuera de la lectura principal por las reglas automáticas.",
      "Base: " + data.normas_procesadas + " normas procesadas",
    ],
  ], true);
  indicatorBulletinsBody.innerHTML = data.boletines.length
    ? data.boletines.map((bulletin) => `
        <tr>
          <td>${escapeHtml(bulletin.numero_boletin || "-")}</td>
          <td>${escapeHtml(formatDisplayDate(bulletin.fecha_publicacion))}</td>
          <td>${escapeHtml(bulletin.normas_procesadas)}</td>
          <td>${escapeHtml(bulletin.relevantes_confirmadas)}</td>
          <td>${escapeHtml(bulletin.falsos_negativos)}</td>
          <td>${escapeHtml(bulletin.control_complementario)}</td>
        </tr>
      `).join("")
    : '<tr><td colspan="6" class="empty-state">No utilizado durante este período.</td></tr>';
}

document.addEventListener("click", (event) => {
  const saveButton = event.target.closest(".save-review");
  if (saveButton) {
    saveNormReview(saveButton);
  }
});

document.addEventListener("change", (event) => {
  const reviewInput = event.target.closest("[data-review-decision]");
  if (reviewInput) {
    const row = reviewInput.closest("[data-result-key]");
    if (reviewInput.checked) {
      row.querySelectorAll("[data-review-decision]").forEach((input) => {
        if (input !== reviewInput) {
          input.checked = false;
        }
      });
    }
    const evidence = row.querySelector(".fn-evidence");
    if (evidence) {
      const relevantSelected = Boolean(row.querySelector('[data-review-decision][value="RELEVANTE_CONFIRMADA"]:checked'));
      evidence.hidden = !relevantSelected;
    }
    const status = row.querySelector(".save-status");
    status.textContent = "";
    status.classList.remove("save-status--error");
  }

  const bulletinInput = event.target.closest('#bulletin-control input[type="checkbox"]');
  if (bulletinInput) {
    const inputs = [...bulletinControl.querySelectorAll('input[type="checkbox"]')];
    if (bulletinInput.checked) {
      inputs.forEach((input) => {
        if (input !== bulletinInput) {
          input.checked = false;
        }
      });
    } else if (!inputs.some((input) => input.checked)) {
      bulletinInput.checked = true;
    }
    bulletinSaveStatus.textContent = "";
    bulletinSaveStatus.classList.remove("save-status--error");
  }
});

document.querySelectorAll("[data-accordion-search]").forEach((input) => {
  input.addEventListener("input", () => {
    const query = input.value.trim().toLocaleLowerCase("es");
    const body = document.getElementById(input.dataset.accordionSearch);
    body.querySelectorAll("tr[data-search]").forEach((row) => {
      row.hidden = Boolean(query) && !row.dataset.search.includes(query);
    });
  });
});

parametroDate.addEventListener("focus", () => selectParametroMode(parametroDateMode));
parametroDate.addEventListener("input", () => selectParametroMode(parametroDateMode));
parametroAdvanced.addEventListener("focus", () => selectParametroMode(parametroAdvancedMode));
parametroAdvanced.addEventListener("input", () => selectParametroMode(parametroAdvancedMode));

analysisForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  clearPanels();
  setMessage("Iniciando análisis...", "info");
  updateProgress({progress_percent: 2, message: "Preparando análisis..."});

  try {
    parametroInput.value = resolveParametro();
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: new FormData(analysisForm),
    });
    const payload = await response.json();
    if (!response.ok || !payload.job_id) {
      throw new Error(payload.message || "No se pudo iniciar el análisis.");
    }
    await pollJob(payload.job_id);
  } catch (error) {
    progressPanel.hidden = true;
    submitButton.disabled = false;
    clearPanels();
    setMessage(error.message || "No se pudo iniciar el análisis.", "error");
  }
});

bulletinReviewForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!currentAnalysis) {
    return;
  }

  const saveButton = bulletinReviewForm.querySelector('button[type="submit"]');
  saveButton.disabled = true;
  bulletinSaveStatus.textContent = "Guardando...";
  bulletinSaveStatus.classList.remove("save-status--error");

  try {
    const response = await fetch("/api/review/boletin", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        semana: currentAnalysis.summary.semana,
        boletin_clave: currentAnalysis.summary.boletin_clave,
        control_complementario: getBulletinControl(),
        observaciones: "",
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.message || "No se pudo guardar el control complementario.");
    }
    currentAnalysis.summary.control_complementario = payload.control_complementario;
    setBulletinControl(payload.control_complementario);
    bulletinSaveStatus.textContent = "Decisión guardada.";
    setMessage("Control complementario guardado.", "success");
  } catch (error) {
    bulletinSaveStatus.textContent = error.message;
    bulletinSaveStatus.classList.add("save-status--error");
    setMessage(error.message, "error");
  } finally {
    saveButton.disabled = false;
  }
});

indicatorWeek.addEventListener("change", loadIndicators);

document.querySelector("main").prepend(messageBox);
setupTabs();
loadWeeks();

