const DEFAULT_REQUEST =
  "Launch the Eclipse Protocol trailer worldwide tonight. Localize it for France and Spain using Ava's voice, then maximize paid reach.";

const requestField = document.querySelector("#producer-request");
const assureButton = document.querySelector("#assure-button");
const applyButton = document.querySelector("#apply-button");
const resetButton = document.querySelector("#reset-request");
const charCount = document.querySelector("#char-count");
const errorBanner = document.querySelector("#error-banner");
const runStatus = document.querySelector("#run-status");
const runtimeState = document.querySelector("#runtime-state");
const interpretationState = document.querySelector("#interpretation-state");
const requestSummary = document.querySelector("#request-summary");
const actionList = document.querySelector("#action-list");
const evidenceGrid = document.querySelector("#evidence-grid");
const evidenceState = document.querySelector("#evidence-state");
const diffTable = document.querySelector("#diff-table");
const frontierContent = document.querySelector("#frontier-content");
const capabilityStatus = document.querySelector("#capability-status");
const capabilityProposed = document.querySelector("#capability-proposed");
const capabilityEvidence = document.querySelector("#capability-evidence");
const capabilityConclusion = document.querySelector("#capability-conclusion");
const overallStatus = document.querySelector("#overall-status");
const safeTitle = document.querySelector("#safe-title");
const safeSummary = document.querySelector("#safe-summary");
const spendCeiling = document.querySelector("#spend-ceiling");
const safeSteps = document.querySelector("#safe-steps");
const receiptSection = document.querySelector("#receipt-section");
const receiptContent = document.querySelector("#receipt-content");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  }[char]));
}

function updateCount() {
  charCount.textContent = `${requestField.value.length} chars`;
}

function setLoading(loading) {
  assureButton.disabled = loading;
  runStatus.textContent = loading ? "LIVE INTERPRETATION…" : "READY TO ASSURE";
  runtimeState.textContent = loading ? "running" : "awaiting";
  assureButton.querySelector("span:last-child").textContent = loading ? "Interpreting…" : "Run assurance";
}

function renderActions(actions) {
  actionList.innerHTML = actions.map((action, index) => {
    const inferredArguments = Object.keys(action.arguments || {})
      .filter((key) => action.argument_provenance?.[key] === "AGENT_INFERRED");
    const inferenceCallout = inferredArguments.length
      ? `<div class="inference-callout"><b>WHAT DID THE AGENT INFER?</b><span>${escapeHtml(inferredArguments.join(", "))} <strong>AGENT_INFERRED</strong></span></div>`
      : "";
    return `
      <div class="action-row">
        <span class="action-index">0${index + 1}</span>
        <div>
          <div class="action-title">${escapeHtml(action.description)}</div>
          <div class="action-arguments">${Object.entries(action.arguments || {}).map(([key, value]) => `
            <div class="argument">
              <span><b>${escapeHtml(key)}</b> ${escapeHtml(Array.isArray(value) ? value.join(", ") : value)}</span>
              <span class="provenance ${String(action.argument_provenance?.[key] || "UNKNOWN").toLowerCase()}">${escapeHtml(action.argument_provenance?.[key] || "UNKNOWN")}</span>
            </div>
          `).join("")}</div>
          ${inferenceCallout}
        </div>
        <span class="action-type">${escapeHtml(action.action_type)}</span>
      </div>
    `;
  }).join("");
}

function renderEvidence(evidence) {
  evidenceState.textContent = `${evidence.length} FACTS · DETERMINISTIC`;
  evidenceGrid.innerHTML = evidence.map((item) => `
    <article class="evidence-item ${item.status.toLowerCase()}">
      <div class="evidence-top"><span class="evidence-id">${escapeHtml(item.id)}</span><span class="evidence-status">${escapeHtml(item.status)}</span></div>
      <h3>${escapeHtml(item.label)}</h3>
      <p>${escapeHtml(item.value)}</p>
      <small>${escapeHtml(item.source)}</small>
    </article>
  `).join("");
}

function renderFrontier(evidence, evaluations) {
  const ava = evidence.find((item) => item.id === "ava-voice");
  const voiceBoundary = evaluations.find((item) => item.id === "voice-gap");
  if (!ava || !voiceBoundary) {
    frontierContent.innerHTML = '<div class="empty-state">No unresolved proof boundary was returned.</div>';
    return;
  }
  const established = evidence.filter((item) => item.status === "VERIFIED").map((item) => item.label);
  frontierContent.innerHTML = `
    <div class="frontier-column">
      <span class="mini-label">Established evidence</span>
      <ul>${established.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
    <div class="frontier-column frontier-gap">
      <span class="mini-label">Unresolved boundary</span>
      <strong>${escapeHtml(voiceBoundary.dimension)}</strong>
      <p>${escapeHtml(voiceBoundary.evidence)}</p>
      <span class="decision-pill ${voiceBoundary.status.toLowerCase()}">${escapeHtml(voiceBoundary.status)}</span>
    </div>
    <div class="frontier-column">
      <span class="mini-label">Next evidence required</span>
      <ul>
        <li>${escapeHtml(voiceBoundary.consequence)}</li>
        <li>Required source: ${escapeHtml(ava.source)}</li>
      </ul>
    </div>
  `;
}

function renderCapability(evaluations, capabilityExceedsGreenlight) {
  const campaignBoundary = evaluations.find((item) => item.id === "spend-boundary");
  if (!campaignBoundary) return;
  capabilityProposed.textContent = campaignBoundary.proposed;
  capabilityEvidence.textContent = campaignBoundary.evidence;
  capabilityConclusion.textContent = campaignBoundary.consequence;
  capabilityStatus.textContent = capabilityExceedsGreenlight
    ? "CAPABILITY EXCEEDS GREENLIGHT"
    : "WITHIN GREENLIGHT";
  capabilityStatus.className = `decision-pill ${capabilityExceedsGreenlight ? "review" : "allow"}`;
}

function renderDiff(evaluations, authoritativeStatus) {
  diffTable.innerHTML = `
    <div class="diff-head">
      <span>Consequential dimension</span>
      <span>Proposed by agent</span>
      <span>Available evidence</span>
      <span>Decision</span>
    </div>
    ${evaluations.map((item) => `
      <div class="diff-row">
        <span class="diff-dimension">${escapeHtml(item.dimension)}</span>
        <span class="diff-proposed">${escapeHtml(item.proposed)}</span>
        <span class="diff-evidence">${escapeHtml(item.evidence)}</span>
        <span class="decision-pill ${item.status.toLowerCase()}">${escapeHtml(item.status)}</span>
      </div>
    `).join("")}
  `;
  overallStatus.textContent = authoritativeStatus;
  overallStatus.className = `decision-pill ${authoritativeStatus.toLowerCase()}`;
}

function renderSafePlan(plan) {
  safeTitle.textContent = plan.title;
  safeSummary.textContent = plan.summary;
  spendCeiling.textContent = plan.spend_ceiling;
  safeSteps.innerHTML = plan.steps.map((step) => `
    <div class="safe-step ${step.status === "BLOCKED" ? "blocked" : ""}">
      <span class="step-check">${step.status === "BLOCKED" ? "×" : "✓"}</span>
      <div>
        <div class="safe-step-title">${escapeHtml(step.title)}</div>
        <div class="safe-step-detail">${escapeHtml(step.detail)} <span>(${escapeHtml(step.guardrail)})</span></div>
      </div>
      <span class="step-status">${escapeHtml(step.status)}</span>
    </div>
  `).join("");
  applyButton.disabled = false;
}

function renderReceipt(receipt) {
  receiptSection.hidden = false;
  receiptContent.innerHTML = `
    <div class="receipt-top">
      <span class="receipt-id">${escapeHtml(receipt.receipt_id)} · ${escapeHtml(receipt.status)}</span>
      <span class="receipt-time">${escapeHtml(receipt.created_at)}</span>
    </div>
    <div class="receipt-grid">
      <div class="receipt-col"><h4>Simulated action</h4><p>${escapeHtml(receipt.action)}</p></div>
      <div class="receipt-col"><h4>Executed subset</h4><ul>${receipt.executed_subset.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>
      <div class="receipt-col"><h4>Guardrails</h4><ul>${receipt.guardrails_applied.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>
    </div>
    <div class="runtime-strip" style="margin-top:24px"><span class="runtime-chip"><i class="chip-dot green"></i> External side effects <b>${escapeHtml(receipt.external_side_effects)}</b></span></div>
  `;
  receiptSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function runAssurance() {
  const producerRequest = requestField.value.trim();
  if (producerRequest.length < 10) return;
  errorBanner.hidden = true;
  receiptSection.hidden = true;
  setLoading(true);
  interpretationState.textContent = "LIVE INTERPRETATION";
  try {
    const response = await fetch("/api/assure", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ producer_request: producerRequest }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Assurance run failed.");
    requestSummary.textContent = payload.interpretation.request_summary;
    renderActions(payload.interpretation.consequential_actions);
    renderEvidence(payload.evidence);
    renderDiff(payload.evaluations, payload.overall_status);
    renderFrontier(payload.evidence, payload.evaluations);
    renderCapability(payload.evaluations, payload.capability_exceeds_greenlight);
    renderSafePlan(payload.safe_plan);
    document.querySelector("#runtime-model").textContent = `${payload.runtime.model} · ${payload.runtime.location}`;
    runtimeState.textContent = "verified";
    interpretationState.textContent = "VERIFIED BY GOOGLE";
    runStatus.textContent = "ASSURANCE COMPLETE";
    window.latestPlan = payload.safe_plan;
  } catch (error) {
    errorBanner.textContent = error.message;
    errorBanner.hidden = false;
    interpretationState.textContent = "RUNTIME ERROR";
    runtimeState.textContent = "error";
  } finally {
    assureButton.disabled = false;
    assureButton.querySelector("span:last-child").textContent = "Run assurance";
  }
}

async function applySafePlan() {
  applyButton.disabled = true;
  applyButton.querySelector("span:last-child").textContent = "Simulating…";
  try {
    const response = await fetch("/api/execute", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ plan_id: "eclipse-safe-plan" }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Simulation failed.");
    renderReceipt(payload);
  } catch (error) {
    errorBanner.textContent = error.message;
    errorBanner.hidden = false;
  } finally {
    applyButton.disabled = false;
    applyButton.querySelector("span:last-child").textContent = "Apply safe plan";
  }
}

requestField.addEventListener("input", updateCount);
assureButton.addEventListener("click", runAssurance);
applyButton.addEventListener("click", applySafePlan);
resetButton.addEventListener("click", () => {
  requestField.value = DEFAULT_REQUEST;
  updateCount();
});
updateCount();
runAssurance();