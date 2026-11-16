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
const pendingWarning = document.getElementById("pending-warning");
const pendingWarningTitle = document.getElementById("pending-warning-title");
const pendingWarningList = document.getElementById("pending-warning-list");
const pendingReviewAgain = document.getElementById("pending-review-again");
const pendingSaveAnyway = document.getElementById("pending-save-anyway");
const indicatorWeek = document.getElementById("indicator-week");
const indicatorMainGrid = document.getElementById("indicator-main-grid");
const indicatorSecondaryGrid = document.getElementById("indicator-secondary-grid");
const indicatorExtraGrid = document.getElementById("indicator-extra-grid");
const indicatorConsistency = document.getElementById("indicator-consistency");
const indicatorPeriod = document.getElementById("indicator-period");
const indicatorBulletinsBody = document.getElementById("indicator-bulletins-body");
const indicatorWeekScope = document.getElementById("indicator-week-scope");
const indicatorPeriodForm = document.getElementById("indicator-period-form");
const indicatorStart = document.getElementById("indicator-start");
const indicatorEnd = document.getElementById("indicator-end");
const indicatorAllHistory = document.getElementById("indicator-all-history");
const indicatorCoverage = document.getElementById("indicator-coverage");

let currentAnalysis = null;
let dataRange = null;

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
  hidePendingWarning();
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
  ].filter(Boolean).join("");
  const searchable = [
    result.nombre,
    result.organismo,
    result.sumario,
    result.tipo_norma,
  ].join(" ").toLocaleLowerCase("es");
  const falseNegative = hiddenCategory && result.decision_manual === "RELEVANTE_CONFIRMADA";

  return `
    <article data-result-key="${escapeHtml(result.clave_registro)}" data-search="${escapeHtml(searchable)}" class="review-card ${falseNegative ? "review-card--false-negative" : ""}">
      <div class="norm-content">
        <div class="norm-top">
          <span class="category-badge category-${escapeHtml(result.categoria_automatica_original)}">
            ${escapeHtml(result.categoria_original_label)}
          </span>
          <div class="norm-heading">
            <strong>${escapeHtml(result.nombre)}</strong>
            <small>${escapeHtml(result.poder)} / ${escapeHtml(result.tipo_norma)}</small>
          </div>
          <span class="agency">${escapeHtml(result.organismo)}</span>
          <div class="links-cell">${links || "<span>Sin enlace</span>"}</div>
        </div>
        <div class="norm-detail">
          <p class="sumario">${escapeHtml(result.sumario)}</p>
          <p class="motivo"><strong>Detección:</strong> ${escapeHtml(result.motivo_label || "Sin motivo informado")}</p>
        </div>
      </div>
      <div class="review-cell">
        <span class="decision-label">Decisión profesional</span>
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
      </div>
    </article>
  `;
}

function renderCategoryBody(body, results, hiddenCategory) {
  if (!results.length) {
    body.innerHTML = '<p class="empty-state">No hay registros en esta categoría.</p>';
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
  noRelevantFalseNegatives.textContent = `${countFor("NO_RELEVANTE")} omisiones identificadas`;
  discardedFalseNegatives.textContent = `${countFor("DESCARTADA_FILTRO_ESTRUCTURAL")} omisiones identificadas`;
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
    row.classList.toggle("review-card--false-negative", payload.es_falso_negativo);
    updateFalseNegativeBadges(currentAnalysis.results);
    status.classList.remove("save-status--error");
    status.textContent = payload.es_falso_negativo ? "Omisión identificada registrada." : "Decisión guardada.";
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
  dataRange = payload.rango_datos || null;
  if (dataRange && !indicatorStart.value && !indicatorEnd.value) {
    indicatorStart.value = dataRange.desde;
    indicatorEnd.value = dataRange.hasta;
  }
}

function getIndicatorMode() {
  const selected = document.querySelector('input[name="indicator_mode"]:checked');
  return selected ? selected.value : "week";
}

function indicatorsUrl() {
  if (getIndicatorMode() === "period") {
    if (!indicatorStart.value || !indicatorEnd.value) {
      return null;
    }
    return `/api/indicators?desde=${encodeURIComponent(indicatorStart.value)}&hasta=${encodeURIComponent(indicatorEnd.value)}`;
  }
  return indicatorWeek.value ? `/api/indicators?week=${encodeURIComponent(indicatorWeek.value)}` : null;
}

function renderCoverage(data) {
  const coverage = data.cobertura;
  const lines = [];
  if (coverage && coverage.sin_registros) {
    lines.push("Sin registros en el período seleccionado. No se informan valores en cero.");
  }
  if (coverage && coverage.avisos) {
    lines.push(...coverage.avisos);
  }
  indicatorCoverage.innerHTML = lines.map((line) => `<p>${escapeHtml(line)}</p>`).join("");
  indicatorCoverage.hidden = !lines.length;
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
  const url = indicatorsUrl();
  if (!url) {
    return;
  }
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    setMessage(data.message || "No se pudieron cargar los indicadores.", "error");
    return;
  }
  const period = data.periodo || {};
  const range = `${formatDisplayDate(period.desde)} a ${formatDisplayDate(period.hasta)}`;
  indicatorPeriod.textContent = data.cobertura
    ? `${range} · ${data.cobertura.boletines} boletines · ${data.normas_procesadas.toLocaleString("es-AR")} normas distintas`
    : range;
  renderCoverage(data);
  if (data.cobertura && data.cobertura.sin_registros) {
    const empty = '<p class="empty-state">Sin registros en el período seleccionado.</p>';
    indicatorMainGrid.innerHTML = empty;
    indicatorSecondaryGrid.innerHTML = empty;
    indicatorExtraGrid.innerHTML = empty;
    indicatorConsistency.hidden = true;
    indicatorBulletinsBody.innerHTML = '<tr><td colspan="6" class="empty-state">Sin registros en el período seleccionado.</td></tr>';
    return;
  }
  renderConsistency(data.avisos_consistencia || {});

  const bases = data.bases_desempeno || {};
  const omissionValue = typeof data.porcentaje_omisiones === "number"
    ? formatPercentageIndicator(data.porcentaje_omisiones) + (data.omisiones_provisional ? " (provisional)" : "")
    : data.porcentaje_omisiones;
  const omissionDetail = [
    "Base: " + data.omisiones_identificadas + " de " + (bases.relevantes_confirmadas || 0) + " relevantes confirmadas",
    ...(data.motivos_provisional || []),
  ].join(" · ");

  renderMetricCards(indicatorMainGrid, [
    [
      "Relevantes confirmadas",
      data.relevantes_confirmadas_total,
      "Normas confirmadas como relevantes, cualquiera sea su categoría automática original.",
      "",
    ],
    [
      "Omisiones identificadas",
      data.omisiones_identificadas,
      "Normas no relevantes o descartadas por el detector que se confirmaron como relevantes.",
      data.omisiones_provisional ? "Provisional: " + data.motivos_provisional.join(" ") : "",
    ],
    [
      "% de omisiones identificadas",
      omissionValue,
      "Omisiones identificadas entre las normas que ingresaron a la aplicación. No mide normas que nunca ingresaron.",
      omissionDetail,
    ],
    [
      "% de alertas automáticas descartadas",
      formatPercentageIndicator(data.tasa_falsos_positivos),
      "Alertas automáticas que la validación profesional descartó.",
      "Base: " + (bases.alertas_automaticas_validadas || 0) + " alertas automáticas con decisión",
    ],
  ], true);

  renderMetricCards(indicatorSecondaryGrid, [
    [
      "Normas procesadas",
      data.normas_procesadas,
      "Normas distintas incorporadas al registro.",
      "",
    ],
    [
      "Normas con decisión registrada",
      formatPercentageIndicator(data.cobertura_validacion),
      "Normas procesadas con una decisión profesional guardada. No equivale al porcentaje del boletín leído.",
      "Base: " + (bases.normas_validadas || 0) + " de " + data.normas_procesadas + " normas procesadas",
    ],
    [
      "Derivación a revisión manual",
      formatPercentageIndicator(data.tasa_revision_manual),
      "Normas procesadas que el detector derivó a revisión humana.",
      "Base: " + data.normas_procesadas + " normas procesadas",
    ],
    [
      "Rendimiento de la revisión manual",
      formatPercentageIndicator(data.rendimiento_revision_manual),
      "Casos de revisión manual resueltos que resultaron relevantes.",
      "Base: " + (bases.casos_revision_manual_validados || 0) + " casos resueltos",
    ],
  ], true);

  renderMetricCards(indicatorExtraGrid, [
    ["Días de uso", data.dias_uso, "", ""],
    ["Alertas automáticas", data.relevantes, "", ""],
    ["Casos de revisión manual", data.revision_manual, "", ""],
    ["Relevantes desde revisión manual", data.relevantes_desde_revision_manual, "", ""],
    [
      "Precisión automática",
      formatPercentageIndicator(data.precision_automatica),
      "Complemento del porcentaje de alertas descartadas, sobre la misma base.",
      "Base: " + (bases.alertas_automaticas_validadas || 0) + " alertas automáticas con decisión",
    ],
    [
      "Normas excluidas de la selección principal",
      formatPercentageIndicator(data.reduccion_lectura),
      "Normas no relevantes o descartadas por el filtro estructural. No mide ahorro efectivo de lectura.",
      "Base: " + data.normas_procesadas + " normas procesadas",
    ],
    ["Control complementario", data.control_complementario, "", ""],
  ]);

  indicatorBulletinsBody.innerHTML = data.boletines.length
    ? data.boletines.map((bulletin) => `
        <tr>
          <td>${escapeHtml(bulletin.numero_boletin || "-")}</td>
          <td>${escapeHtml(formatDisplayDate(bulletin.fecha_publicacion))}</td>
          <td>${escapeHtml(bulletin.normas_procesadas)}</td>
          <td>${escapeHtml(bulletin.relevantes_confirmadas)}</td>
          <td>${escapeHtml(bulletin.omisiones_identificadas)}</td>
          <td>${escapeHtml(bulletin.control_complementario)}</td>
        </tr>
      `).join("")
    : '<tr><td colspan="6" class="empty-state">No utilizado durante este período.</td></tr>';
}

function renderConsistency(checks) {
  const pending = checks.pendientes || [];
  const completeWithPending = checks.completos_con_pendientes || [];
  const contradictions = checks.contradicciones || [];
  const blocks = [];

  if (pending.length) {
    blocks.push(
      `<p class="consistency-notice__title">${pending.length === 1 ? "Hay 1 alerta sin decisión" : `Hay ${pending.length} alertas sin decisión`}:</p>` +
      "<ul>" + pending.map((item) => {
        const label = `${escapeHtml(item.nombre)} — BO ${escapeHtml(item.numero_boletin || "-")}, ${escapeHtml(formatDisplayDate(item.fecha_publicacion))}`;
        return item.url_norma
          ? `<li><a href="${escapeHtml(item.url_norma)}" target="_blank" rel="noopener">${label}</a></li>`
          : `<li>${label}</li>`;
      }).join("") + "</ul>"
    );
  }
  if (completeWithPending.length) {
    blocks.push(
      '<p class="consistency-notice__title">Boletines marcados como completos que tienen alertas sin decisión:</p>' +
      "<ul>" + completeWithPending.map((item) =>
        `<li>BO ${escapeHtml(item.numero_boletin || "-")}, ${escapeHtml(formatDisplayDate(item.fecha_publicacion))}: ${escapeHtml(item.pendientes)} pendiente(s)</li>`
      ).join("") + "</ul>"
    );
  }
  if (contradictions.length) {
    blocks.push(
      '<p class="consistency-notice__title">Normas con decisiones distintas en distintos boletines (se usa la más reciente):</p>' +
      "<ul>" + contradictions.map((item) =>
        `<li>${escapeHtml(item.nombre)}: ` + item.decisiones.map((entry) =>
          `BO ${escapeHtml(entry.numero_boletin || "-")} ${escapeHtml(entry.decision_manual === "RELEVANTE_CONFIRMADA" ? "relevante" : "no relevante")}`
        ).join("; ") + "</li>"
      ).join("") + "</ul>"
    );
  }
  indicatorConsistency.innerHTML = blocks.join("");
  indicatorConsistency.hidden = !blocks.length;
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
    hidePendingWarning();
    bulletinSaveStatus.textContent = "";
    bulletinSaveStatus.classList.remove("save-status--error");
  }
});

document.querySelectorAll("[data-accordion-search]").forEach((input) => {
  input.addEventListener("input", () => {
    const query = input.value.trim().toLocaleLowerCase("es");
    const body = document.getElementById(input.dataset.accordionSearch);
    body.querySelectorAll("[data-search]").forEach((row) => {
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

const categoryLabels = {
  RELEVANTE: "relevante automática",
  REVISION_MANUAL: "revisión manual",
};

function hidePendingWarning() {
  pendingWarning.hidden = true;
  pendingWarningList.innerHTML = "";
}

function showPendingWarning(pending) {
  const count = pending.length;
  pendingWarningTitle.textContent = count === 1
    ? "Queda 1 norma sin decisión en este boletín:"
    : `Quedan ${count} normas sin decisión en este boletín:`;
  pendingWarningList.innerHTML = pending.map((item) =>
    `<li>${escapeHtml(item.nombre)} (${escapeHtml(categoryLabels[item.categoria_automatica_original] || item.categoria_automatica_original)})</li>`
  ).join("");
  pendingWarning.hidden = false;
}

async function saveBulletinControl(confirmPending = false) {
  if (!currentAnalysis) {
    return;
  }

  const saveButton = bulletinReviewForm.querySelector('button[type="submit"]');
  saveButton.disabled = true;
  pendingSaveAnyway.disabled = true;
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
        confirmar_pendientes: confirmPending,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.message || "No se pudo guardar el control complementario.");
    }
    if (payload.status === "pendientes") {
      showPendingWarning(payload.pendientes || []);
      bulletinSaveStatus.textContent = "No se guardó: hay normas sin decisión.";
      bulletinSaveStatus.classList.add("save-status--error");
      return;
    }
    hidePendingWarning();
    currentAnalysis.summary.control_complementario = payload.control_complementario;
    setBulletinControl(payload.control_complementario);
    bulletinSaveStatus.textContent = "Decisión guardada.";
    const pendingCount = (payload.pendientes || []).length;
    setMessage(
      pendingCount
        ? `Control complementario guardado como completo con ${pendingCount === 1 ? "1 norma" : `${pendingCount} normas`} sin decisión.`
        : "Control complementario guardado.",
      "success",
    );
  } catch (error) {
    bulletinSaveStatus.textContent = error.message;
    bulletinSaveStatus.classList.add("save-status--error");
    setMessage(error.message, "error");
  } finally {
    saveButton.disabled = false;
    pendingSaveAnyway.disabled = false;
  }
}

bulletinReviewForm.addEventListener("submit", (event) => {
  event.preventDefault();
  saveBulletinControl(false);
});

pendingSaveAnyway.addEventListener("click", () => saveBulletinControl(true));

pendingReviewAgain.addEventListener("click", () => {
  hidePendingWarning();
  setBulletinControl(currentAnalysis ? currentAnalysis.summary.control_complementario : "PENDIENTE");
  bulletinSaveStatus.textContent = "";
  bulletinSaveStatus.classList.remove("save-status--error");
  resultsPanel.scrollIntoView({behavior: "smooth", block: "start"});
});

indicatorWeek.addEventListener("change", loadIndicators);

document.querySelectorAll('input[name="indicator_mode"]').forEach((input) => {
  input.addEventListener("change", () => {
    const periodMode = getIndicatorMode() === "period";
    indicatorWeekScope.hidden = periodMode;
    indicatorPeriodForm.hidden = !periodMode;
    loadIndicators();
  });
});

indicatorPeriodForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (indicatorStart.value > indicatorEnd.value) {
    setMessage("La fecha inicial no puede ser posterior a la fecha final.", "error");
    return;
  }
  loadIndicators();
});

indicatorAllHistory.addEventListener("click", () => {
  if (!dataRange) {
    setMessage("Todavía no hay registros guardados.", "info");
    return;
  }
  indicatorStart.value = dataRange.desde;
  indicatorEnd.value = dataRange.hasta;
  loadIndicators();
});

document.querySelector("main").prepend(messageBox);
setupTabs();
loadWeeks();

