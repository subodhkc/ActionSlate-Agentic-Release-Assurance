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
const diffTable = document.querySelector("#diff-table");
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
  actionList.innerHTML = actions.map((action, index) => `
    <div class="action-row">
      <span class="action-index">0${index + 1}</span>
      <div>
        <div class="action-title">${escapeHtml(action.description)}</div>
        <div class="action-desc">${escapeHtml(Object.entries(action.arguments || {}).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`).join(" · "))}</div>
      </div>
      <span class="action-type">${escapeHtml(action.action_type)}</span>
    </div>
  `).join("");
}

function renderDiff(evaluations) {
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
  overallStatus.textContent = evaluations.some((item) => item.status === "BLOCK") ? "REVIEW" : "ALLOW";
  overallStatus.className = `decision-pill ${overallStatus.textContent.toLowerCase()}`;
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
    renderDiff(payload.evaluations);
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