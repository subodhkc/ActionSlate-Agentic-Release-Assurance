const requestField = document.querySelector("#producer-request");
const assureButton = document.querySelector("#assure-button");
const applyButton = document.querySelector("#apply-button");
const errorBanner = document.querySelector("#error-banner");
const runStatus = document.querySelector("#run-status");
const runtimeState = document.querySelector("#runtime-state");
const runtimeDot = document.querySelector("#runtime-dot");
const topbarRuntimeDot = document.querySelector("#topbar-runtime-dot");
const evidenceRuntime = document.querySelector("#evidence-runtime");
const actionCount = document.querySelector("#action-count");
const actionCountDetail = document.querySelector("#action-count-detail");
const runSequence = document.querySelector("#run-sequence");
const runtimeProof = document.querySelector("#runtime-proof");
const proofModel = document.querySelector("#proof-model");
const proofLocation = document.querySelector("#proof-location");
const proofProject = document.querySelector("#proof-project");
const interpretationState = document.querySelector("#interpretation-state");
const geminiVerification = document.querySelector("#gemini-verification");
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
const safeState = document.querySelector("#safe-state");
const safeIntro = document.querySelector("#safe-intro");
const safeIcon = document.querySelector("#safe-icon");
const receiptSection = document.querySelector("#receipt-section");
const receiptContent = document.querySelector("#receipt-content");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  }[char]));
}

async function postJson(url, body, timeoutMs) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const rawBody = await response.text();
    let payload;
    try {
      payload = JSON.parse(rawBody);
    } catch {
      throw new Error("The server returned an unreadable response. Please retry.");
    }
    if (!response.ok) {
      throw new Error(payload.detail || "The request could not be completed.");
    }
    return payload;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The live request timed out. Please retry.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

function requireAssurancePayload(payload) {
  const isValid =
    payload &&
    payload.interpretation &&
    Array.isArray(payload.interpretation.consequential_actions) &&
    Array.isArray(payload.evidence) &&
    Array.isArray(payload.evaluations) &&
    payload.safe_plan &&
    Array.isArray(payload.safe_plan.steps) &&
    typeof payload.execution_token === "string" &&
    payload.runtime &&
    typeof payload.runtime.model === "string";
  if (!isValid) {
    throw new Error("The assurance response was incomplete. Please retry.");
  }
}

function requireReceiptPayload(payload) {
  if (
    !payload ||
    typeof payload.receipt_id !== "string" ||
    payload.status !== "SIMULATED" ||
    typeof payload.created_at !== "string" ||
    !Array.isArray(payload.executed_subset) ||
    !Array.isArray(payload.guardrails_applied)
  ) {
    throw new Error("The simulation receipt was incomplete. Please retry.");
  }
}

function setLoading(loading) {
  assureButton.disabled = loading;
  runStatus.textContent = loading ? "LIVE ASSURANCE RUNNING…" : "AWAITING RUN";
  assureButton.querySelector("span:last-child").textContent = loading ? "Assuring…" : "Run live assurance";
}

function setRunStage(stage) {
  runSequence.hidden = false;
  const stages = [...runSequence.querySelectorAll("[data-stage]")];
  const currentIndex = stages.findIndex((item) => item.dataset.stage === stage);
  stages.forEach((item, index) => {
    item.classList.toggle("complete", index < currentIndex || stage === "complete");
    item.classList.toggle("current", item.dataset.stage === stage);
  });
}

function nextPaint() {
  return new Promise((resolve) => window.requestAnimationFrame(resolve));
}

function resetResultState() {
  applyButton.disabled = true;
  delete window.latestPlan;
  delete window.latestExecutionToken;
  receiptSection.hidden = true;
  runtimeProof.hidden = true;
  runtimeDot.classList.remove("green");
  topbarRuntimeDot.classList.add("idle");
  document.querySelector("#runtime-model").textContent = "CALL IN PROGRESS";
  geminiVerification.textContent = "○";
  geminiVerification.classList.remove("resolved");
  geminiVerification.setAttribute("aria-label", "Awaiting Gemini response");
  actionCount.textContent = "ASSURANCE RUNNING";
  actionCountDetail.textContent = "Pending Gemini interpretation";
  requestSummary.textContent = "Gemini is interpreting the fixed producer command.";
  actionList.innerHTML = '<div class="empty-state">Live interpretation in progress.</div>';
  evidenceState.textContent = "AWAITING EVALUATION";
  evidenceGrid.innerHTML = '<div class="empty-state">Evidence evaluation will follow interpretation.</div>';
  overallStatus.textContent = "AWAITING EVALUATION";
  overallStatus.className = "decision-pill neutral";
  diffTable.innerHTML = `
    <div class="diff-head">
      <span>Consequential dimension</span>
      <span>Scenario action</span>
      <span>Available evidence</span>
      <span>Decision</span>
    </div>
    <div class="empty-state">Evidence comparison is pending.</div>
  `;
  frontierContent.innerHTML = '<div class="empty-state">The proof frontier is pending.</div>';
  capabilityStatus.textContent = "AWAITING DECISION";
  capabilityStatus.className = "decision-pill neutral";
  capabilityProposed.textContent = "Awaiting proposed scope";
  capabilityEvidence.textContent = "Awaiting delegated authority";
  capabilityConclusion.textContent = "The deterministic comparison will establish the action boundary.";
  safeState.textContent = "AWAITING SAFE PLAN";
  safeState.classList.add("pending");
  safeIntro.classList.add("awaiting");
  safeIcon.textContent = "—";
  safeTitle.textContent = "Awaiting bounded plan";
  safeSummary.textContent = "Safe subset generated after assurance.";
  spendCeiling.textContent = "Awaiting authority boundary";
  safeSteps.innerHTML = '<div class="empty-state">Safe subset will appear after evaluation.</div>';
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
        <li>Ava trailer-specific digital voice authorization</li>
        <li>Expected source: ${escapeHtml(ava.source)}</li>
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
      <span>Scenario action</span>
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
  safeState.textContent = "SAFE SUBSET EXTRACTED";
  safeState.classList.remove("pending");
  safeIntro.classList.remove("awaiting");
  safeIcon.textContent = "✓";
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
    <div class="runtime-strip receipt-runtime-strip"><span class="runtime-chip"><i class="chip-dot green"></i> External side effects <b>${escapeHtml(receipt.external_side_effects)}</b></span></div>
  `;
  receiptSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function runAssurance() {
  const producerRequest = requestField.value.trim();
  if (producerRequest.length < 10) return;
  const startedAt = performance.now();
  errorBanner.hidden = true;
  resetResultState();
  setLoading(true);
  setRunStage("calling");
  interpretationState.textContent = "CALLING GEMINI";
  try {
    const payload = await postJson(
      "/api/assure",
      { producer_request: producerRequest },
      50000,
    );
    requireAssurancePayload(payload);
    setRunStage("interpreting");
    interpretationState.textContent = "INTERPRETING CONSEQUENCES";
    await nextPaint();
    requestSummary.textContent = payload.interpretation.request_summary;
    const actions = payload.interpretation.consequential_actions;
    actionCount.textContent = `${actions.length} consequential action${actions.length === 1 ? "" : "s"}`;
    actionCountDetail.textContent = "Returned by Gemini interpretation";
    renderActions(actions);
    setRunStage("matching");
    evidenceRuntime.textContent = `${payload.evidence.length} evidence facts evaluated`;
    await nextPaint();
    renderEvidence(payload.evidence);
    setRunStage("applying");
    await nextPaint();
    renderDiff(payload.evaluations, payload.overall_status);
    renderFrontier(payload.evidence, payload.evaluations);
    renderCapability(payload.evaluations, payload.capability_exceeds_greenlight);
    renderSafePlan(payload.safe_plan);
    const elapsedSeconds = (performance.now() - startedAt) / 1000;
    const latencyLabel = `${elapsedSeconds.toFixed(1)}s`;
    document.querySelector("#runtime-model").textContent = `${payload.runtime.model} · ${payload.runtime.location}`;
    proofModel.textContent = payload.runtime.model;
    proofLocation.textContent = `Vertex AI · ${payload.runtime.location}`;
    proofProject.textContent = payload.runtime.project;
    runtimeProof.hidden = false;
    runtimeState.textContent = `${payload.runtime.model} · Vertex AI`;
    runtimeDot.classList.add("green");
    topbarRuntimeDot.classList.remove("idle");
    geminiVerification.textContent = "✓";
    geminiVerification.classList.add("resolved");
    geminiVerification.setAttribute("aria-label", "Structured Gemini response received");
    interpretationState.textContent = "STRUCTURED RESPONSE RECEIVED";
    runStatus.textContent = `LIVE GOOGLE CALL VERIFIED · ${latencyLabel} END-TO-END`;
    setRunStage("complete");
    window.latestPlan = payload.safe_plan;
    window.latestExecutionToken = payload.execution_token;
  } catch (error) {
    applyButton.disabled = true;
    delete window.latestPlan;
    delete window.latestExecutionToken;
    errorBanner.textContent = error.message;
    errorBanner.hidden = false;
    interpretationState.textContent = "RUNTIME ERROR";
    document.querySelector("#runtime-model").textContent = "RUNTIME ERROR";
    runStatus.textContent = "ASSURANCE FAILED";
  } finally {
    assureButton.disabled = false;
    assureButton.querySelector("span:last-child").textContent = "Run live assurance";
  }
}

async function applySafePlan() {
  assureButton.disabled = true;
  applyButton.disabled = true;
  applyButton.querySelector("span:last-child").textContent = "Simulating…";
  try {
    const payload = await postJson(
      "/api/execute",
      {
        plan_id: "eclipse-safe-plan",
        execution_token: window.latestExecutionToken,
      },
      15000,
    );
    requireReceiptPayload(payload);
    renderReceipt(payload);
  } catch (error) {
    errorBanner.textContent = error.message;
    errorBanner.hidden = false;
  } finally {
    assureButton.disabled = false;
    applyButton.disabled = false;
    applyButton.querySelector("span:last-child").textContent = "Apply safe plan";
  }
}

assureButton.addEventListener("click", runAssurance);
applyButton.addEventListener("click", applySafePlan);