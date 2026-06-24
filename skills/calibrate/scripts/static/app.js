"use strict";
const $ = (id) => document.getElementById(id);
document.getElementById("rubric-version-label").textContent = window.__RUBRIC_VERSION__;
const Q = window.__QUEUE__ || [];

const INDUSTRY_PALETTE = {
  "consulting": "#7ab8ff", "bank": "#27c281", "hedge-fund": "#f6b73c",
  "asset-mgmt": "#b388ff", "pharma": "#ff8a65", "biotech": "#ffab40",
  "ai-lab": "#80d8ff", "climate-tech": "#69f0ae", "govt": "#9aa3b2",
  "industrial": "#ce93d8", "health-tech": "#80cbc4", "unknown": "#616975",
};
function colorFor(industry){ return INDUSTRY_PALETTE[industry] || "#616975"; }

async function refreshBatchHeader(){
  try {
    const r = await fetch("/batch/current");
    if (!r.ok) return;
    const d = await r.json();
    document.getElementById("batch-id-label").textContent = d.batch_id;
    document.getElementById("batch-count-label").textContent = d.verdicts_in_batch;
  } catch(e){}
}
refreshBatchHeader();

// #scout-fresh: not yet implemented (T8). Disable to prevent silent no-ops.
(function(){
  const btn = document.getElementById("scout-fresh");
  if (!btn) return;
  btn.disabled = true;
  btn.title = "Scout fresh — coming soon (not yet implemented)";
})();

document.getElementById("load-batch").addEventListener("click", async () => {
  const r = await fetch("/queue/preview");
  if (!r.ok) return;
  const p = await r.json();
  document.getElementById("preview").hidden = false;
  document.getElementById("preview-batch-id").textContent = p.batch_id;
  document.getElementById("preview-n-roles").textContent = p.n_roles;
  document.getElementById("preview-industry-count").textContent = p.industries.length;
  const bar = document.getElementById("mix-bar"); bar.innerHTML = "";
  p.industries.forEach(i => {
    const seg = document.createElement("div");
    seg.className = "mix-seg";
    seg.style.width = i.pct + "%";
    seg.style.background = colorFor(i.industry);
    seg.title = i.industry + " — " + i.count + " (" + i.pct + "%)";
    bar.appendChild(seg);
  });
  const legend = document.getElementById("mix-legend"); legend.innerHTML = "";
  p.industries.forEach(i => {
    const li = document.createElement("li");
    li.innerHTML = '<span class="dot" style="background:' + colorFor(i.industry) + '"></span> '
      + escapeHtml(i.industry) + ' — ' + i.count + ' (' + i.pct + '%)';
    legend.appendChild(li);
  });
});

document.getElementById("start-labelling").addEventListener("click", () => {
  document.getElementById("preview").hidden = true;
  if (Q.length > 0) selectRole(Q[0].key);
});
let activeKey = window.__FIRST_KEY__;
let chosenVerdict = null;
let lastVerdictId = null;
const rubricChanged = ($("rubric-banner").dataset.changed === "true");

function pillClass(screen){return "pill pill-" + ({pass:"pass",flag:"flag",reject:"reject"}[screen] || "null");}

function renderQueue(){
  const list = $("queue"); list.innerHTML = "";
  Q.forEach(r=>{
    const row = document.createElement("div");
    row.className = "row" + (r.key === activeKey ? " active" : "");
    row.dataset.key = r.key;
    row.innerHTML =
      `<div class="title">${escapeHtml(r.company)} — ${escapeHtml(r.title)}</div>
       <div class="meta"><span class="${pillClass(r.screen)}">${escapeHtml(r.screen)}</span>
       <span>fit ${escapeHtml(String(r.fit || ""))}</span><span>${escapeHtml(r.posted||"")}</span></div>`;
    row.tabIndex = 0;
    row.addEventListener("click", () => selectRole(r.key));
    row.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectRole(r.key); } });
    list.appendChild(row);
  });
}

function escapeHtml(s){return (s||"").replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}

async function selectRole(key){
  activeKey = key; chosenVerdict = null; lastVerdictId = null;
  $("submit").disabled = true; $("reason").value = "";
  $("reveal").hidden = true; $("error").hidden = true;
  document.querySelectorAll("#verdict-bar .v").forEach(b=>b.classList.remove("active"));
  document.querySelectorAll("#queue .row").forEach(r=>r.classList.toggle("active", r.dataset.key===key));
  const res = await fetch("/role/" + encodeURIComponent(key));
  if (!res.ok){ $("role-meta").textContent = "role not found: " + key; return; }
  const r = await res.json();
  $("role-meta").innerHTML =
    `<div>${escapeHtml(r.company)} — ${escapeHtml(r.title)}</div>
     <div class="sub">${escapeHtml(r.location)} · ${escapeHtml(r.posting_age)}</div>`;
  $("jd-link").href = r.jd_link;
  $("jd-body").textContent = r.jd_md;
  $("jd-body").hidden = true; $("toggle-jd").textContent = "Show JD ▾";
  renderGates(r.extraction.gates || {});
  renderVariables(r.extraction.variables || {});
}

function renderGates(gates){
  const ul = $("gates"); ul.innerHTML = "";
  Object.entries(gates).forEach(([id, v])=>{
    const li = document.createElement("li");
    const ok = (v === "pass");
    li.innerHTML = `<span class="${ok?"hit":"miss"}">${ok?"✓":"✗"}</span> ${escapeHtml(id)}`;
    ul.appendChild(li);
  });
}

const VCLS = {MET:"v-met",PARTIAL:"v-partial",UNMET:"v-unmet",CANNOT_ASSESS:"v-na"};
function renderVariables(vars){
  const tb = document.querySelector("#variables tbody"); tb.innerHTML = "";
  // Show in stable order if known; else iterate.
  const order = ["frontier-strategy","mgmt-ladder","intellectual-agency","client-facing",
                 "player-coach","peer-bar","origination-bd","firm-stability"];
  const ids = Array.from(new Set([...order.filter(k=>k in vars), ...Object.keys(vars)]));
  ids.forEach(id=>{
    const r = vars[id] || {};
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${escapeHtml(id)}</td><td>${kindOf(id)}</td>
      <td class="${VCLS[r.verdict]||""}">${escapeHtml(r.verdict||"—")}</td>
      <td>${escapeHtml(r.quote||"")}</td>`;
    tb.appendChild(tr);
  });
}

function kindOf(id){
  if (id.startsWith("disq-")) return "disqualifier";
  if (id === "frontier-strategy" || id === "mgmt-ladder") return "spine";
  if (["intellectual-agency","client-facing","player-coach","peer-bar"].includes(id)) return "heavy";
  if (["origination-bd","firm-stability"].includes(id)) return "supporting";
  return "—";
}

document.querySelectorAll("#verdict-bar .v").forEach(b=>{
  b.addEventListener("click", () => {
    chosenVerdict = b.dataset.v;
    document.querySelectorAll("#verdict-bar .v").forEach(x=>x.classList.toggle("active", x===b));
    $("submit").disabled = !($("reason").value.trim() && chosenVerdict);
  });
});
$("reason").addEventListener("input", ()=>{
  $("submit").disabled = !($("reason").value.trim() && chosenVerdict);
});

$("toggle-jd").addEventListener("click", () => {
  const body = $("jd-body"); const open = !body.hidden;
  body.hidden = open ? true : false;
  $("toggle-jd").textContent = open ? "Show JD ▾" : "Hide JD ▴";
});

$("submit").addEventListener("click", async () => {
  $("error").hidden = true;
  const payload = {role_key: activeKey, verdict: chosenVerdict,
                   reason: $("reason").value.trim()};
  if (rubricChanged) payload.ack_rubric_changed = true;
  const res = await fetch("/verdict", {method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify(payload)});
  if (res.status === 409 && !rubricChanged){
    if (confirm("Rubric changed since last log row — log under the NEW ruler? (Recommended: stop and finish the batch.)")){
      payload.ack_rubric_changed = true;
      const res2 = await fetch("/verdict", {method:"POST",
        headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
      if (!res2.ok){ showError(await res2.text()); return; }
      const v = await res2.json(); lastVerdictId = v.verdict_id; return reveal(v);
    }
    return;
  }
  if (!res.ok){ showError(await res.text()); return; }
  const v = await res.json(); lastVerdictId = v.verdict_id; return reveal(v);
});

function showError(t){ $("error").hidden = false; $("error").textContent = t; }

async function reveal(v){
  const res = await fetch("/score/" + encodeURIComponent(activeKey) + "?after=" + lastVerdictId);
  if (!res.ok){ showError("score still locked — refresh"); return; }
  const s = await res.json();
  $("reveal").hidden = false;
  $("score-card").innerHTML =
    `<div><div class="lbl">fit</div><div class="num">${escapeHtml(String(s.fit||"—"))}</div></div>
     <div><div class="lbl">odds</div><div class="num">${escapeHtml(String(s.odds||"—"))}</div></div>
     <div><div class="lbl">band</div><div class="num">${escapeHtml(String((s.band||"—")).split(" ")[0])}</div></div>
     <div><div class="lbl">screen</div><div class="num"><span class="${pillClass(s.screen)}">${escapeHtml(String(s.screen||"—"))}</span></div></div>`;
  // Divergence: ordinal distance between chosen verdict and machine band
  const ord = {safety:4,achievable:3,stretch:2,moonshot:1,reject:0,null:null};
  const vo = {pursue:3,"on-ramp":2,no:0}[chosenVerdict];
  const mb = (s.band || "null").split(" ")[0];
  const mo = (s.screen === "reject") ? 0 : ord[mb];
  const div = $("divergence");
  if (mo === null || mo === undefined){
    div.className = "aligned";
    div.textContent = "Machine held / abstained — no contradiction to score.";
  } else {
    const dist = Math.abs(vo - mo);
    div.className = dist > 1 ? "diverged" : "aligned";
    div.textContent = `verdict=${chosenVerdict} (ord ${vo}) vs machine band=${mb} (ord ${mo}) — distance ${dist}${dist>1?" — DIVERGENCE (calibration signal)":" — aligned"}`;
  }
}

$("next").onclick = async () => {
  const idx = Q.findIndex(r=>r.key===activeKey);
  if (idx >= 0) Q.splice(idx, 1);
  renderQueue();
  // Surface review threshold by counting log lines via /count
  try {
    const c = await fetch("/count"); if (c.ok){
      const n = (await c.json()).count || 0;
      if (n >= 20) document.title = "CareerVinny — Calibration (≥20 verdicts: run review.py)";
    }
  } catch(_){}
  if (Q.length === 0){ alert("Queue empty — well done."); return; }
  selectRole(Q[0].key);
};

$("show-batch").addEventListener("click", async () => {
  const section = $("batch");
  if (!section.hidden) { section.hidden = true; $("show-batch").textContent = "Show batch summary ▾"; return; }
  const res = await fetch("/batch-summary");
  if (!res.ok) { alert("Failed to load batch summary"); return; }
  const bs = await res.json();
  const container = $("batch-summary");
  container.innerHTML = "";

  // Verdict mix chips
  const CHIP_CLS = { pursue: "v-pursue", "on-ramp": "v-onramp", no: "v-no" };
  const vm = bs.verdict_mix || {};
  const chipBar = document.createElement("div");
  chipBar.className = "verdict-chips";
  ["pursue", "on-ramp", "no"].forEach(v => {
    const chip = document.createElement("span");
    chip.className = "chip " + (CHIP_CLS[v] || "");
    chip.textContent = escapeHtml(v) + " " + escapeHtml(String(vm[v] || 0));
    chipBar.appendChild(chip);
  });
  container.appendChild(chipBar);

  // By-industry table
  const byInd = bs.by_industry || {};
  if (Object.keys(byInd).length > 0) {
    const h4 = document.createElement("h4"); h4.textContent = "By industry"; container.appendChild(h4);
    const tbl = document.createElement("table");
    tbl.innerHTML = "<thead><tr><th>industry</th><th>count</th><th>%pursue</th><th>mean fit (pursue)</th><th>mean fit (no)</th></tr></thead>";
    const tb = document.createElement("tbody");
    Object.entries(byInd).sort(([a],[b])=>a.localeCompare(b)).forEach(([ind, slot]) => {
      const pct = slot.count > 0 ? Math.round(100 * (slot.verdict_mix.pursue || 0) / slot.count) : 0;
      const mfp = slot.mean_fit_pursue != null ? slot.mean_fit_pursue.toFixed(1) : "n/a";
      const mfn = slot.mean_fit_no != null ? slot.mean_fit_no.toFixed(1) : "n/a";
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${escapeHtml(ind)}</td><td>${escapeHtml(String(slot.count))}</td>` +
        `<td>${escapeHtml(String(pct))}%</td><td>${escapeHtml(mfp)}</td><td>${escapeHtml(mfn)}</td>`;
      tb.appendChild(tr);
    });
    tbl.appendChild(tb);
    container.appendChild(tbl);
  }

  // Machine fit by verdict
  const mfbv = bs.machine_fit_by_verdict || {};
  const h4fit = document.createElement("h4"); h4fit.textContent = "Machine fit by verdict (mean)"; container.appendChild(h4fit);
  const fitDiv = document.createElement("div"); fitDiv.className = "fit-spread";
  ["pursue", "on-ramp", "no"].forEach(v => {
    const st = mfbv[v] || {};
    const span = document.createElement("span");
    span.className = "chip " + (CHIP_CLS[v] || "");
    const mean = st.mean != null ? st.mean.toFixed(1) : "n/a";
    span.textContent = escapeHtml(v) + " mean=" + escapeHtml(mean) + " (n=" + escapeHtml(String(st.n || 0)) + ")";
    fitDiv.appendChild(span);
  });
  container.appendChild(fitDiv);

  // Divergences count
  const divs = bs.divergences || [];
  const h4div = document.createElement("h4"); h4div.textContent = "Divergences (band-distance > 1): " + escapeHtml(String(divs.length)); container.appendChild(h4div);

  // Proposed deltas
  const pds = bs.proposed_deltas_summary || [];
  if (pds.length > 0) {
    const h4pd = document.createElement("h4"); h4pd.textContent = "Proposed deltas (" + escapeHtml(String(pds.length)) + ")"; container.appendChild(h4pd);
    const ul = document.createElement("ul");
    pds.forEach(entry => {
      const li = document.createElement("li");
      li.textContent = escapeHtml(entry.variable) + " — " + escapeHtml(entry.kind) + " (n=" + escapeHtml(String(entry.count)) + ")";
      ul.appendChild(li);
    });
    container.appendChild(ul);
  }

  section.hidden = false;
  $("show-batch").textContent = "Hide batch summary ▴";
});

renderQueue();
if (activeKey) selectRole(activeKey); else $("role-meta").textContent = "Queue empty.";

let propModalState = {};  // { proposal_id: "accept" | "reject" | "defer" }

function renderProposalCard(card, deferred=false){
  const div = document.createElement("div");
  div.className = "card card-" + card.kind + (card.confidence === "low" ? " low-conf" : "")
    + (deferred ? " deferred" : "");
  div.dataset.proposalId = card.proposal_id;
  const head = document.createElement("div"); head.className = "card-head";
  head.innerHTML = "<strong>" + escapeHtml(card.var_id || "") + "</strong> "
    + "<span class='kind'>" + escapeHtml(card.kind) + "</span>"
    + (card.confidence === "low" ? " <span class='conf-low'>low confidence</span>" : "")
    + (deferred ? " <span class='deferred-tag'>deferred from batch " + escapeHtml(String(card.deferred_from_batch || "?")) + "</span>" : "");
  div.appendChild(head);

  if (card.kind === "weight-up" || card.kind === "weight-down") {
    const m = document.createElement("p"); m.className = "magnitude";
    m.textContent = "Magnitude " + (card.magnitude || 0)
      + " (" + (card.current_weight ?? "?") + " → " + (card.proposed_weight ?? "?") + ")";
    div.appendChild(m);
  }

  const r = document.createElement("p"); r.className = "reasoning";
  r.textContent = card.reasoning || ""; div.appendChild(r);

  if (card.samples && card.samples.length) {
    const ul = document.createElement("ul"); ul.className = "samples";
    card.samples.forEach(s => {
      const li = document.createElement("li");
      li.innerHTML = "<code>" + escapeHtml(s.role_key || "") + "</code> · "
        + "you=<strong>" + escapeHtml(s.your_verdict || "") + "</strong> · "
        + "extracted=<em>" + escapeHtml(s.variable_verdict || "") + "</em>";
      ul.appendChild(li);
    });
    div.appendChild(ul);
  }

  if (card.downstream_reband && card.downstream_reband.count > 0) {
    const rb = document.createElement("p"); rb.className = "reband";
    rb.textContent = "Downstream if accepted: "
      + card.downstream_reband.count + " of your previously-decided roles re-band ("
      + card.downstream_reband.roles.slice(0,3).map(x => escapeHtml(x.role_key) + ": " + escapeHtml(x.from_band) + "→" + escapeHtml(x.to_band)).join("; ")
      + (card.downstream_reband.count > 3 ? "; …" : "") + ")";
    div.appendChild(rb);
  } else {
    const rb = document.createElement("p"); rb.className = "reband meta";
    rb.textContent = "Downstream: no previously-decided roles change band.";
    div.appendChild(rb);
  }

  const actions = document.createElement("div"); actions.className = "card-actions";
  ["accept","reject","defer"].forEach(act => {
    const b = document.createElement("button"); b.type = "button";
    b.className = "btn-action btn-" + act;
    b.textContent = act.charAt(0).toUpperCase() + act.slice(1);
    b.addEventListener("click", () => {
      propModalState[card.proposal_id] = act;
      Array.from(div.querySelectorAll(".btn-action")).forEach(x => x.classList.remove("chosen"));
      b.classList.add("chosen");
    });
    actions.appendChild(b);
  });
  div.appendChild(actions);
  return div;
}

document.getElementById("done-batch").addEventListener("click", async () => {
  const bc = await fetch("/batch/current"); const bcd = bc.ok ? await bc.json() : {verdicts_in_batch: 0};
  let body = {};
  if ((bcd.verdicts_in_batch || 0) < 20) {
    const reason = prompt("Batch has " + (bcd.verdicts_in_batch || 0) + " verdicts (<20). Type a reason to force-close, or Cancel:");
    if (reason === null) return;
    body = {force: true, force_reason: reason || "user-forced"};
  }
  const r = await fetch("/batch/propose", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body)});
  if (!r.ok) { alert("Propose failed: " + await r.text()); return; }
  const d = await r.json();
  propModalState = {};
  document.getElementById("pm-batch-id").textContent = escapeHtml(String(d.batch_id));
  document.getElementById("pm-mix").textContent =
    "verdict mix: pursue " + (d.verdict_mix.pursue || 0)
    + " · on-ramp " + (d.verdict_mix["on-ramp"] || 0)
    + " · no " + (d.verdict_mix.no || 0) + " · n=" + d.n_verdicts;
  const cards = document.getElementById("pm-cards"); cards.innerHTML = "";
  if (!d.cards.length) cards.innerHTML = "<p class='meta'>No new proposals from this batch (no threshold crossings).</p>";
  d.cards.forEach(c => { propModalState[c.proposal_id] = "defer"; cards.appendChild(renderProposalCard(c, false)); });
  const deferredWrap = document.getElementById("pm-deferred"); deferredWrap.innerHTML = "";
  if (!d.deferred.length) deferredWrap.innerHTML = "<p class='meta'>None deferred from prior batches.</p>";
  d.deferred.forEach(c => { propModalState[c.proposal_id] = "defer"; deferredWrap.appendChild(renderProposalCard(c, true)); });
  document.getElementById("propose-modal").showModal();
});

document.getElementById("pm-cancel").addEventListener("click", () => {
  document.getElementById("propose-modal").close();
});

document.getElementById("pm-apply").addEventListener("click", async () => {
  const accept_ids = [], reject_ids = [], defer_ids = [];
  Object.entries(propModalState).forEach(([pid, act]) => {
    if (act === "accept") accept_ids.push(pid);
    else if (act === "reject") reject_ids.push(pid);
    else defer_ids.push(pid);
  });
  const r = await fetch("/batch/apply", {method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({accept_ids, reject_ids, defer_ids})});
  document.getElementById("propose-modal").close();
  if (!r.ok) { alert("Apply failed: " + await r.text()); return; }
  const d = await r.json();
  renderAudit(d); document.getElementById("audit-modal").showModal();
});

function renderAudit(d){
  const ab = document.getElementById("audit-body"); ab.innerHTML = "";
  const sum = document.createElement("p");
  sum.innerHTML = "Guard: <strong class='" + (d.status === "applied" ? "ok" : d.status === "reverted" ? "bad" : "warn") + "'>"
    + escapeHtml(d.status) + "</strong>";
  ab.appendChild(sum);
  if (d.applied && d.applied.length) {
    const h = document.createElement("h4"); h.textContent = "Weight changes applied"; ab.appendChild(h);
    const ul = document.createElement("ul");
    d.applied.forEach(a => {
      const li = document.createElement("li");
      li.innerHTML = "<code>" + escapeHtml(a.var_id) + "</code> "
        + escapeHtml(a.kind) + " " + escapeHtml(String(a.magnitude)) + " ("
        + escapeHtml(String(a.old_weight)) + " → " + escapeHtml(String(a.new_weight)) + ")";
      ul.appendChild(li);
    });
    ab.appendChild(ul);
  }
  if (d.gate_decisions && d.gate_decisions.length) {
    const h = document.createElement("h4"); h.textContent = "Gate accepts (manual edit required)"; ab.appendChild(h);
    const ul = document.createElement("ul");
    d.gate_decisions.forEach(g => {
      const li = document.createElement("li");
      li.innerHTML = "<code>" + escapeHtml(g.var_id || "") + "</code> " + escapeHtml(g.kind || "");
      ul.appendChild(li);
    });
    ab.appendChild(ul);
    const p = document.createElement("p"); p.className = "meta";
    p.textContent = "You accepted these gate proposals; the rubric was NOT auto-edited. Make the structural edit by hand in reference/fit-rubric.md, then re-run check.sh.";
    ab.appendChild(p);
  }
  if (d.status === "reverted" && d.contradicting_roles && d.contradicting_roles.length) {
    const h = document.createElement("h4"); h.textContent = "Reverted — contradicting roles"; ab.appendChild(h);
    const ul = document.createElement("ul");
    d.contradicting_roles.forEach(k => {
      const li = document.createElement("li"); li.innerHTML = "<code>" + escapeHtml(k) + "</code>";
      ul.appendChild(li);
    });
    ab.appendChild(ul);
  }
  const link = document.createElement("p");
  link.innerHTML = "Audit: <a href='/batch/audit/" + escapeHtml(String(d.batch_id_closed)) + "' target='_blank'>"
    + escapeHtml(d.audit_path) + "</a>";
  ab.appendChild(link);
}

document.getElementById("audit-close").addEventListener("click", () => {
  document.getElementById("audit-modal").close();
  location.reload();
});
