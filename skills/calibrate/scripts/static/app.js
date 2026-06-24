"use strict";
const $ = (id) => document.getElementById(id);
document.getElementById("rubric-version-label").textContent = window.__RUBRIC_VERSION__;
const Q = window.__QUEUE__ || [];
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

$("next").addEventListener("click", () => {
  // remove the labelled role from queue, pick next
  const idx = Q.findIndex(r=>r.key===activeKey);
  if (idx >= 0) Q.splice(idx, 1);
  renderQueue();
  if (Q.length === 0){ alert("Queue empty — well done."); return; }
  selectRole(Q[0].key);
});

renderQueue();
if (activeKey) selectRole(activeKey); else $("role-meta").textContent = "Queue empty.";
