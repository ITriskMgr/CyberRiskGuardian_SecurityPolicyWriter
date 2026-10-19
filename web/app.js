// Policy Builder web client — dependency-free ES module. All dynamic text is escaped before insertion.
import { STR } from "./i18n.js";

let LANG = (() => { try { return localStorage.getItem("pb-lang") || (navigator.language || "en").slice(0, 2); } catch { return "en"; } })();
if (!["en", "fr"].includes(LANG)) LANG = "en";
const t = (k) => (STR[LANG][k] ?? STR.en[k] ?? k);
const $app = document.getElementById("app");
let ME = null, META = null;

// ---------------------------------------------------------------- helpers
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const PH = /\[(DECISION|DÉCISION|ROLE|RÔLE|VALUE|VALEUR|DATE|SOURCE|APPROVER|APPROBATEUR|TECHNICAL_DETAIL|DÉTAIL_TECHNIQUE)\s*:\s*[^\]]+\]/g;
const marked = (s) => esc(s).replace(PH, (m) => `<mark class="ph">${m}</mark>`);
function toast(msg, err = false) {
  const el = document.getElementById("toast");
  el.textContent = msg; el.className = "toast show" + (err ? " err" : "");
  clearTimeout(toast._t); toast._t = setTimeout(() => (el.className = "toast"), err ? 6000 : 2600);
}
async function api(path, opts = {}) {
  const init = { method: opts.method || "GET", headers: { "x-requested-with": "policybuilder" }, credentials: "same-origin" };
  if (opts.body instanceof FormData) init.body = opts.body;
  else if (opts.body !== undefined) { init.body = JSON.stringify(opts.body); init.headers["content-type"] = "application/json"; }
  const sep = path.includes("?") ? "&" : "?";
  const r = await fetch(`/api${path}${opts.noLang ? "" : `${sep}lang=${LANG}`}`, init);
  if (r.status === 401 && !path.startsWith("/auth")) { location.hash = "#/login"; throw new Error("auth"); }
  const data = r.headers.get("content-type")?.includes("json") ? await r.json() : null;
  if (!r.ok) {
    const d = data?.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg).join("; ") : t("err");
    toast(msg, true); throw new Error(msg);
  }
  return data;
}
const busy = (btn, on) => { if (!btn) return; btn.disabled = on; if (on) { btn.dataset.label = btn.innerHTML; btn.innerHTML = `<span class="spinner"></span> ${esc(t("generating"))}`; } else if (btn.dataset.label) btn.innerHTML = btn.dataset.label; };
const on = (root, sel, ev, fn) => root.querySelectorAll(sel).forEach((el) => el.addEventListener(ev, (e) => fn(e, el)));

// ---------------------------------------------------------------- chrome
function paintChrome() {
  document.documentElement.lang = LANG;
  document.querySelectorAll(".lang-toggle button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === LANG)));
  const who = document.getElementById("who"), lo = document.getElementById("logout");
  who.textContent = ME ? `${ME.display_name} · ${ME.workspace.name} · ${ME.role}` : "";
  lo.hidden = !ME; lo.textContent = t("logout");
}
document.querySelectorAll(".lang-toggle button").forEach((b) => b.addEventListener("click", async () => {
  LANG = b.dataset.lang; try { localStorage.setItem("pb-lang", LANG); } catch {}
  if (ME) api("/auth/me/language", { method: "PUT", body: { ui_language: LANG } }).catch(() => {});
  route();
}));
document.getElementById("logout").addEventListener("click", async () => { await api("/auth/logout", { method: "POST" }); ME = null; location.hash = "#/login"; });

// ---------------------------------------------------------------- router
const STEPS = ["setup", "interview", "documents", "profile", "applicability", "library", "decisions", "drafts", "export"];
async function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/");
  paintChrome();
  if (parts[0] === "login" || parts[0] === "register") return authView(parts[0]);
  if (!ME) { try { ME = await api("/auth/me", { noLang: true }); META = await api("/meta", { noLang: true }); paintChrome(); } catch { return; } }
  if (parts[0] === "p" && parts[1]) return projectView(parts[1], parts[2] || "interview", parts[3]);
  return projectsView();
}
window.addEventListener("hashchange", route);

// ---------------------------------------------------------------- auth
function authView(mode) {
  $app.className = "app single";
  const reg = mode === "register";
  $app.innerHTML = `<main class="page"><div class="auth panel">
    <h1 style="margin-top:0">${esc(reg ? t("register") : t("signin"))}</h1>
    <form id="f">
      ${reg ? `<label class="field"><span>${esc(t("display_name"))}</span><input type="text" name="display_name" required maxlength="200" autocomplete="name"></label>
      <label class="field"><span>${esc(t("workspace_name"))}</span><input type="text" name="workspace_name" required maxlength="200"></label>` : ""}
      <label class="field"><span>${esc(t("email"))}</span><input type="email" name="email" required autocomplete="username"></label>
      <label class="field"><span>${esc(t("password"))}</span><input type="password" name="password" required minlength="${reg ? 10 : 1}" autocomplete="${reg ? "new-password" : "current-password"}"></label>
      <button class="btn" type="submit">${esc(reg ? t("register") : t("signin"))}</button>
    </form>
    <p class="small">${esc(reg ? t("have_account") : t("no_account"))} <a href="#/${reg ? "login" : "register"}">${esc(reg ? t("signin") : t("register"))}</a></p>
    <p class="small muted">${esc(t("local_note"))}</p></div></main>`;
  document.getElementById("f").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target));
    await api(reg ? "/auth/register" : "/auth/login", { method: "POST", body, noLang: true });
    ME = await api("/auth/me", { noLang: true }); META = await api("/meta", { noLang: true });
    location.hash = "#/projects";
  });
}

// ---------------------------------------------------------------- projects
async function projectsView() {
  $app.className = "app single";
  const projects = await api("/projects");
  $app.innerHTML = `<main class="page">
    <div class="page-head"><div><h1>${esc(t("projects"))}</h1><p>${esc(t("projects_sub"))}</p></div></div>
    <div class="cards">${projects.length ? projects.map((p) => `
      <a class="card" href="#/p/${esc(p.id)}/interview">
        <h3>${esc(p.name)}</h3><div class="muted small">${esc(p.org_display_name || "—")} · ${esc(p.doc_language.toUpperCase())} · ${esc(p.mode)}</div>
        <div class="meter"><i style="width:${Math.round(100 * p.progress.done / Math.max(1, p.progress.total))}%"></i></div>
        <div class="small">${p.progress.done}/${p.progress.total} ${esc(t("answered"))} · ${p.generated}/${p.selected} ${esc(t("drafts"))}
        ${p.stale ? ` · <span class="badge medium">${p.stale} ${esc(t("stale"))}</span>` : ""}</div>
      </a>`).join("") : `<p class="muted">${esc(t("no_projects"))}</p>`}</div>
    <section class="panel" style="margin-top:20px"><h2>${esc(t("new_project"))}</h2>
      <form id="np" class="grid2">
        <label class="field"><span>${esc(t("name"))}</span><input type="text" name="name" required maxlength="300"></label>
        <label class="field"><span>${esc(t("purpose"))}</span><select name="purpose">
          <option value="new_framework">${esc(t("p_new"))}</option><option value="single_policy">${esc(t("p_single"))}</option>
          <option value="improve">${esc(t("p_improve"))}</option><option value="update">${esc(t("p_update"))}</option></select></label>
        <label class="field"><span>${esc(t("doc_lang"))}</span><select name="doc_language">
          <option value="en" ${LANG === "en" ? "selected" : ""}>${esc(t("lang_en"))}</option><option value="fr" ${LANG === "fr" ? "selected" : ""}>${esc(t("lang_fr"))}</option>
          <option value="both">${esc(t("lang_both"))}</option></select></label>
        <label class="field"><span>${esc(t("mode"))}</span><select name="mode">
          <option value="express">${esc(t("express"))}</option><option value="standard">${esc(t("standard"))}</option></select></label>
        <div><button class="btn" type="submit">${esc(t("create"))}</button></div>
      </form></section></main>`;
  document.getElementById("np").addEventListener("submit", async (e) => {
    e.preventDefault();
    const p = await api("/projects", { method: "POST", body: Object.fromEntries(new FormData(e.target)) });
    location.hash = `#/p/${p.id}/interview`;
  });
}

// ---------------------------------------------------------------- project shell
async function projectView(pid, step, arg) {
  if (!STEPS.includes(step) && step !== "policy") step = "interview";
  const p = await api(`/projects/${pid}`);
  $app.className = "app";
  const doneIdx = { PROJECT_CREATED: 0, DISCOVERY_IN_PROGRESS: 1, EVIDENCE_REVIEW: 2, APPLICABILITY_REVIEW: 4, LIBRARY_CONFIRMED: 5, OUTLINE_REVIEW: 6, DRAFT_GENERATED: 7 }[p.workflow_state] ?? 0;
  const cur = step === "policy" ? "drafts" : step;
  $app.innerHTML = `<nav class="rail" aria-label="Project steps"><h2>${esc(p.name)}</h2><p class="sub">${esc(p.org_display_name || "")}</p>
    <ol class="steps">${STEPS.map((s, i) => `<li><a href="#/p/${esc(pid)}/${s}" class="${i <= doneIdx ? "done" : ""}" ${s === cur ? 'aria-current="page"' : ""}>
      <span>${esc(t("steps")[i])}${s === "drafts" && p.stale ? ` <span class="badge medium">${p.stale}</span>` : ""}</span></a></li>`).join("")}</ol>
    <a class="back" href="#/projects">${esc(t("all_projects"))}</a></nav><main class="page" id="main"></main>`;
  const main = document.getElementById("main");
  const views = { setup: setupView, interview: interviewView, documents: documentsView, profile: profileView, applicability: applicabilityView,
    library: libraryView, decisions: decisionsView, drafts: draftsView, export: exportView, policy: policyView };
  await views[step](main, p, arg);
  main.focus?.();
}
const head = (title, sub, right = "") => `<div class="page-head"><div><h1>${esc(title)}</h1>${sub ? `<p>${esc(sub)}</p>` : ""}</div>${right}</div>`;

// ---------------------------------------------------------------- setup
async function setupView(main, p) {
  const live = META?.ai_provider === "anthropic";
  main.innerHTML = head(t("setup_title"), t("setup_sub")) + `
    <section class="panel"><form id="sf" class="grid2">
      <label class="field"><span>${esc(t("name"))}</span><input type="text" name="name" value="${esc(p.name)}" maxlength="300"></label>
      <label class="field"><span>${esc(t("doc_lang"))}</span><select name="doc_language">
        ${["en", "fr", "both"].map((v) => `<option value="${v}" ${p.doc_language === v ? "selected" : ""}>${esc(t("lang_" + v))}</option>`).join("")}</select></label>
      <label class="field"><span>${esc(t("mode"))}</span><select name="mode">
        ${["express", "standard"].map((v) => `<option value="${v}" ${p.mode === v ? "selected" : ""}>${esc(t(v))}</option>`).join("")}</select></label>
      <div><button class="btn" type="submit">${esc(t("save"))}</button></div></form></section>
    <section class="panel"><h2>${esc(t("ai_status"))}</h2>
      <p class="note ${live ? "" : "warn"}">${esc(live ? `${t("ai_live")} (${META.ai_model}).` : t("ai_mock"))}</p>
      <label class="row"><input type="checkbox" id="aisrc" ${p.ai_on_sources ? "checked" : ""} ${ME.role === "admin" || ME.role === "owner" ? "" : "disabled"}> <strong>${esc(t("ai_sources"))}</strong></label>
      <p class="small muted">${esc(t("ai_sources_help"))}</p></section>
    <section class="panel"><h2>${esc(t("audit"))}</h2><div id="audit" class="small muted">…</div></section>
    <section class="panel"><button class="btn danger" id="del">${esc(t("delete_project"))}</button></section>`;
  document.getElementById("sf").addEventListener("submit", async (e) => {
    e.preventDefault(); await api(`/projects/${p.id}`, { method: "PATCH", body: Object.fromEntries(new FormData(e.target)) }); toast(t("saved")); route();
  });
  document.getElementById("aisrc").addEventListener("change", async (e) => { await api(`/projects/${p.id}`, { method: "PATCH", body: { ai_on_sources: e.target.checked } }); toast(t("saved")); });
  document.getElementById("del").addEventListener("click", async () => {
    const typed = prompt(t("delete_confirm")); if (typed !== p.name) return;
    await api(`/projects/${p.id}`, { method: "DELETE" }); toast(t("deleted")); location.hash = "#/projects";
  });
  const log = await api(`/projects/${p.id}/audit`);
  document.getElementById("audit").innerHTML = `<table class="list"><tbody>${log.slice(0, 40).map((e) => `<tr><td>${esc(e.at.slice(0, 19).replace("T", " "))}</td><td>${esc(e.actor)}</td><td>${esc(e.action)}</td><td>${esc(e.entity_id || "")}</td></tr>`).join("")}</tbody></table>`;
}

// ---------------------------------------------------------------- question widget (shared by interview and decisions)
function questionHTML(q) {
  const a = q.answer || {}, v = a.status === "answered" ? a.value : null, st = a.status;
  let input = "";
  const name = `q-${q.code}`;
  if (q.type === "select") input = `<div class="choices">${q.options.map((o) => `<label><input type="radio" name="${name}" value="${esc(o.value)}" ${v === o.value ? "checked" : ""}> <span>${esc(o.label)}</span></label>`).join("")}</div>`;
  else if (q.type === "multi") input = `<div class="choices">${q.options.map((o) => `<label><input type="checkbox" name="${name}" value="${esc(o.value)}" ${Array.isArray(v) && v.includes(o.value) ? "checked" : ""}> <span>${esc(o.label)}</span></label>`).join("")}</div>`;
  else if (q.type === "textarea") input = `<textarea name="${name}" maxlength="2000">${esc(v || "")}</textarea>`;
  else input = `<input type="${q.type === "date" ? "date" : "text"}" name="${name}" value="${esc(v || "")}" maxlength="300">`;
  const sugg = q.suggested ? q.options.find((o) => o.value === q.suggested) : null;
  return `<div class="q" data-code="${esc(q.code)}" data-type="${esc(q.type)}">
    <div class="q-head"><div class="q-label">${esc(q.label)} ${q.required ? `<span class="badge">${esc(t("required"))}</span>` : ""} ${q.legal_review ? `<span class="badge medium">${esc(t("legal_flag"))}</span>` : ""}</div><span class="saved" aria-live="polite"></span></div>
    <div class="q-help">${esc(q.help)} <button type="button" class="link-btn small why-btn">${esc(t("why"))}</button></div>
    <p class="q-why" hidden>${esc(q.why)}</p>
    ${input}
    ${sugg && st !== "answered" ? `<p class="suggest muted">${esc(t("suggested"))}: <strong>${esc(sugg.label)}</strong> <button type="button" class="btn sm ghost use-sugg" data-v="${esc(sugg.value)}">${esc(t("use_suggestion"))}</button></p>` : ""}
    <div class="q-status">
      <button type="button" data-st="unknown" aria-pressed="${st === "unknown"}">${esc(t("unknown"))}</button>
      ${q.required ? "" : `<button type="button" data-st="not_applicable" aria-pressed="${st === "not_applicable"}">${esc(t("na"))}</button>`}
      <button type="button" data-st="decide_later" aria-pressed="${st === "decide_later"}">${esc(t("later"))}</button>
    </div></div>`;
}
function wireQuestions(root, pid, after) {
  const save = async (qEl, value, status) => {
    const code = qEl.dataset.code;
    const res = await api(`/projects/${pid}/answers/${encodeURIComponent(code)}`, { method: "PUT", body: { value, status } });
    const s = qEl.querySelector(".saved"); s.textContent = "✓ " + t("saved"); setTimeout(() => (s.textContent = ""), 1800);
    qEl.querySelectorAll(".q-status button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.st === status)));
    if (status !== "answered") qEl.querySelectorAll("input[type=radio],input[type=checkbox]").forEach((i) => (i.checked = false));
    after && after(res, code);
  };
  root.querySelectorAll(".q").forEach((qEl) => {
    const type = qEl.dataset.type;
    qEl.querySelector(".why-btn").addEventListener("click", () => { const w = qEl.querySelector(".q-why"); w.hidden = !w.hidden; });
    qEl.querySelectorAll(".q-status button").forEach((b) => b.addEventListener("click", () => save(qEl, null, b.dataset.st).catch(() => {})));
    qEl.querySelector(".use-sugg")?.addEventListener("click", (e) => {
      const r = qEl.querySelector(`input[value="${CSS.escape(e.target.dataset.v)}"]`); if (r) r.checked = true;
      save(qEl, e.target.dataset.v, "answered").then(() => e.target.closest(".suggest")?.remove()).catch(() => {});
    });
    if (type === "select") qEl.querySelectorAll("input[type=radio]").forEach((i) => i.addEventListener("change", () => save(qEl, i.value, "answered").catch(() => {})));
    else if (type === "multi") qEl.querySelectorAll("input[type=checkbox]").forEach((i) => i.addEventListener("change", () => {
      let vals = [...qEl.querySelectorAll("input[type=checkbox]:checked")].map((x) => x.value);
      if (i.value === "none" && i.checked) { qEl.querySelectorAll("input[type=checkbox]").forEach((x) => (x.checked = x.value === "none")); vals = ["none"]; }
      else if (i.checked) { const n = qEl.querySelector('input[value="none"]'); if (n) n.checked = false; vals = vals.filter((x) => x !== "none"); }
      if (vals.length) save(qEl, vals, "answered").catch(() => {});
    }));
    else qEl.querySelectorAll("input,textarea").forEach((i) => i.addEventListener("change", () => { if (i.value.trim()) save(qEl, i.value, "answered").catch(() => {}); }));
  });
}

// ---------------------------------------------------------------- interview
async function interviewView(main, p, stepKey) {
  const data = await api(`/projects/${p.id}/interview`);
  const secs = data.sections;
  let idx = Math.max(0, secs.findIndex((s) => s.key === stepKey));
  const byCode = Object.fromEntries(data.questions.map((q) => [q.code, q]));
  const pr = data.progress;
  main.innerHTML = head(t("interview"), t("interview_sub"), `<div class="small" style="min-width:220px">${esc(t("progress"))}: ${pr.done}/${pr.total}<div class="meter"><i style="width:${Math.round(100 * pr.done / Math.max(1, pr.total))}%"></i></div></div>`) +
    (pr.minimum_complete ? `<div class="note row"><span class="grow">${esc(t("min_done"))}</span><a class="btn ghost sm" href="#/p/${esc(p.id)}/library">${esc(t("go_library"))}</a><button class="btn sm" id="basic">${esc(t("basic_eisp"))}</button></div>` : "") +
    `<div class="tabs" role="tablist">${secs.map((s, i) => { const answered = s.questions.filter((c) => byCode[c]?.answer).length;
      return `<button role="tab" data-i="${i}" aria-selected="${i === idx}">${esc(s.title)}<span class="count">${answered}/${s.questions.length}</span></button>`; }).join("")}</div>
    <section class="panel" id="qs"></section>
    <div class="row"><button class="btn quiet" id="prev">${esc(t("prev_step"))}</button><span class="grow"></span><button class="btn" id="next">${esc(t("next_step"))}</button></div>
    ${data.observations.length ? `<section class="panel" style="margin-top:16px"><h2>${esc(t("observations"))}</h2>${data.observations.map((o) => `<p><span class="badge ${o.severity}">${esc(t("sev")[o.severity])}</span> ${esc(o.text)}</p>`).join("")}</section>` : ""}`;
  const paint = () => {
    const qs = document.getElementById("qs");
    qs.innerHTML = secs[idx].questions.map((c) => questionHTML(byCode[c])).join("");
    wireQuestions(qs, p.id, (res, code) => { if (["ORG-02", "ORG-13", "TECH-03", "DATA-02", "ORG-05"].includes(code)) interviewView(main, p, secs[idx].key); });
    main.querySelectorAll(".tabs button").forEach((b) => b.setAttribute("aria-selected", String(+b.dataset.i === idx)));
    document.getElementById("prev").disabled = idx === 0;
  };
  on(main, ".tabs button", "click", (e, b) => { idx = +b.dataset.i; paint(); });
  document.getElementById("prev").addEventListener("click", () => { if (idx > 0) { idx--; paint(); window.scrollTo(0, 0); } });
  document.getElementById("next").addEventListener("click", () => { if (idx < secs.length - 1) { idx++; paint(); window.scrollTo(0, 0); } else location.hash = `#/p/${p.id}/documents`; });
  document.getElementById("basic")?.addEventListener("click", async (e) => {
    busy(e.target, true);
    try {
      const cat = await api(`/projects/${p.id}/catalogue`);
      const sel = cat.saved ? cat.items.filter((i) => i.selected).map((i) => i.code) : [];
      if (!sel.includes("EISP")) sel.unshift("EISP");
      await api(`/projects/${p.id}/selection`, { method: "PUT", body: { codes: sel } });
      await api(`/projects/${p.id}/generate`, { method: "POST", body: { codes: ["EISP"] } });
      const pols = await api(`/projects/${p.id}/policies`);
      location.hash = `#/p/${p.id}/policy/${pols.find((x) => x.code === "EISP").id}`;
    } finally { busy(e.target, false); }
  });
  paint();
}

// ---------------------------------------------------------------- documents and facts
async function documentsView(main, p) {
  const [sources, facts] = await Promise.all([api(`/projects/${p.id}/sources`), api(`/projects/${p.id}/facts`)]);
  const cats = t("cats");
  main.innerHTML = head(t("documents"), t("documents_sub")) + `
    <section class="panel"><div class="drop" id="drop">
      <p>${esc(t("drop"))} <label class="link-btn" style="cursor:pointer">${esc(t("browse"))}<input type="file" id="file" multiple hidden accept=".docx,.pdf,.txt,.md,.csv,.xlsx"></label></p>
      <label class="small">${esc(t("category"))} <select id="cat" style="width:auto">${Object.entries(cats).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("")}</select></label>
      <p class="small muted">${esc(t("accepted"))}</p><div id="up" class="small"></div></div>
      ${p.ai_on_sources ? `<p class="note warn small">${esc(t("ai_sources_help"))}</p>` : ""}</section>
    <section class="panel"><h2>${esc(t("sources"))}</h2>${sources.length ? `<table class="list"><thead><tr><th>${esc(t("document"))}</th><th>${esc(t("category"))}</th><th>${esc(t("facts"))}</th><th></th></tr></thead><tbody>
      ${sources.map((s) => `<tr><td><strong>${esc(s.filename)}</strong>${s.title ? `<div class="small muted">${esc(s.title)}</div>` : ""}${s.warnings.map((w) => `<div class="small" style="color:var(--warn)">⚠ ${esc(w)}</div>`).join("")}</td>
        <td class="small">${esc(cats[s.category] || s.category)}</td><td>${s.facts}${s.pending ? ` <span class="badge medium">${s.pending}</span>` : ""}</td>
        <td class="row"><button class="btn sm quiet seg" data-id="${esc(s.id)}">${esc(t("view_text"))}</button><button class="btn sm danger delsrc" data-id="${esc(s.id)}">${esc(t("delete"))}</button></td></tr>
        <tr hidden id="seg-${esc(s.id)}"><td colspan="4"></td></tr>`).join("")}</tbody></table>` : `<p class="muted">${esc(t("none_yet"))}</p>`}</section>
    <section class="panel"><h2>${esc(t("facts"))}</h2><p class="muted small">${esc(t("facts_sub"))}</p>
      ${facts.length ? `<table class="list"><tbody>${facts.map((f) => `<tr>
        <td style="width:60%"><strong>${esc(f.question)}</strong> ${f.conflict_group ? `<span class="badge high">${esc(t("conflict"))}</span>` : ""}
          <div>${esc(t("from_doc"))}: <strong>${esc(f.value_label)}</strong>${f.current_answer ? ` · ${esc(t("your_answer"))}: ${esc(f.current_answer)}` : ""}</div>
          <blockquote class="quote">“${esc(f.quote)}”</blockquote><div class="small muted">${esc(f.source)} · ${esc(f.locator)} · ${esc(f.extractor)} · ${esc(f.confidence)}</div></td>
        <td>${f.state === "proposed" ? `<div class="row"><button class="btn sm fact" data-id="${esc(f.id)}" data-a="confirm">${esc(t("confirm"))}</button><button class="btn sm quiet fact" data-id="${esc(f.id)}" data-a="reject">${esc(t("reject"))}</button></div>` : `<span class="badge ${f.state === "confirmed" ? "ok" : ""}">${esc(t("state")[f.state])}</span>`}</td></tr>`).join("")}</tbody></table>` : `<p class="muted">${esc(t("none_yet"))}</p>`}</section>`;
  const upload = async (files) => {
    const up = document.getElementById("up");
    for (const f of files) {
      up.innerHTML = `<span class="spinner"></span> ${esc(t("uploading"))} ${esc(f.name)}`;
      const fd = new FormData(); fd.append("file", f); fd.append("category", document.getElementById("cat").value);
      try { await api(`/projects/${p.id}/sources`, { method: "POST", body: fd }); } catch {}
    }
    up.textContent = ""; documentsView(main, p);
  };
  document.getElementById("file").addEventListener("change", (e) => upload([...e.target.files]));
  const drop = document.getElementById("drop");
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); upload([...e.dataTransfer.files]); });
  on(main, ".delsrc", "click", async (e, b) => { if (!confirm(t("delete") + "?")) return; await api(`/sources/${b.dataset.id}`, { method: "DELETE" }); documentsView(main, p); });
  on(main, ".fact", "click", async (e, b) => { await api(`/facts/${b.dataset.id}/decision`, { method: "POST", body: { action: b.dataset.a } }); documentsView(main, p); });
  on(main, ".seg", "click", async (e, b) => {
    const row = document.getElementById(`seg-${b.dataset.id}`);
    if (!row.hidden) { row.hidden = true; return; }
    const d = await api(`/sources/${b.dataset.id}/segments`);
    row.firstElementChild.innerHTML = d.segments.map((s) => `<div style="margin:8px 0"><span class="small muted">${esc(s.locator)}</span>${s.injection ? ` <span class="badge high">${esc(t("injection"))}</span>` : ""}<blockquote class="quote" style="white-space:pre-wrap">${esc(s.text)}</blockquote></div>`).join("");
    row.hidden = false;
  });
}

// ---------------------------------------------------------------- profile
async function profileView(main, p) {
  const d = await api(`/projects/${p.id}/profile`);
  main.innerHTML = head(t("profile"), t("profile_sub")) +
    (d.observations.length ? `<section class="panel"><h2>${esc(t("observations"))}</h2>${d.observations.map((o) => `<p><span class="badge ${o.severity}">${esc(t("sev")[o.severity])}</span> ${esc(o.text)}</p>`).join("")}</section>` : "") +
    d.groups.map((g) => `<section class="panel"><h2>${esc(g.title)}</h2><table class="list"><tbody>${g.items.map((it) => `<tr>
      <td style="width:45%">${esc(it.label)}</td>
      <td>${it.status === "answered" ? esc(it.value) : it.status ? `<span class="badge medium">${esc({ unknown: t("unknown"), not_applicable: t("na"), decide_later: t("later") }[it.status])}</span>` : `<span class="muted">—</span>`}</td>
      <td class="small muted">${it.source ? esc(it.source === "document" ? t("src_doc") : t("src_user")) : ""}</td></tr>`).join("")}</tbody></table>
      <p class="small"><a href="#/p/${esc(p.id)}/${g.section === "decisions" ? "decisions" : "interview"}">${esc(t("edit"))}</a></p></section>`).join("");
}

// ---------------------------------------------------------------- applicability
async function applicabilityView(main, p) {
  const d = await api(`/projects/${p.id}/applicability`);
  const st = t("st");
  main.innerHTML = head(t("applic"), t("applic_sub")) + (d.items.length ? d.items.map((c) => `
    <section class="panel"><div class="row"><h2 class="grow" style="margin:0">${esc(c.name)}</h2>
      <span class="badge">${esc(c.kind_label)}</span><span class="badge ${c.status === "applies" ? "ok" : c.status === "candidate" ? "medium" : ""}">${esc(st[c.status])}</span></div>
      ${c.verification ? `<p class="small" style="color:var(--warn)">${esc(c.verification)}</p>` : ""}
      <p class="small"><strong>${esc(t("observed"))}:</strong> ${esc(c.observed)}<br><strong>${esc(t("to_confirm"))}:</strong> ${esc(c.confirm)}<br>
      <strong>${esc(t("affects"))}:</strong> ${esc(c.policies.join(", "))}
      ${c.url ? `<br><strong>${esc(t("reference"))}:</strong> <a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer">${esc(c.url)}</a>` : ""}</p>
      ${c.decision ? `<p class="small muted">${esc(c.decision.reviewer_name)} — ${esc(c.decision.rationale)} (${esc((c.decision.decided_at || "").slice(0, 10))})</p>` : ""}
      <form class="grid2 dec" data-code="${esc(c.code)}">
        <label class="field"><span>${esc(t("status"))}</span><select name="status">${Object.entries(st).map(([k, v]) => `<option value="${k}" ${c.status === k ? "selected" : ""}>${esc(v)}</option>`).join("")}</select></label>
        <label class="field"><span>${esc(t("reviewer"))}</span><input type="text" name="reviewer_name" maxlength="200" value="${esc(c.decision?.reviewer_name || "")}"></label>
        <label class="field" style="grid-column:1/-1"><span>${esc(t("rationale"))}</span><textarea name="rationale" maxlength="2000">${esc(c.decision?.rationale || "")}</textarea></label>
        <div><button class="btn sm" type="submit">${esc(t("record"))}</button></div></form></section>`).join("") : `<section class="panel"><p class="muted">${esc(t("none_yet"))}</p></section>`);
  on(main, "form.dec", "submit", async (e, f) => {
    e.preventDefault();
    await api(`/projects/${p.id}/applicability/${encodeURIComponent(f.dataset.code)}`, { method: "POST", body: Object.fromEntries(new FormData(f)) });
    toast(t("saved")); applicabilityView(main, p);
  });
}

// ---------------------------------------------------------------- library
async function libraryView(main, p) {
  const d = await api(`/projects/${p.id}/catalogue`);
  const levels = [...new Set(d.items.map((i) => i.level_label))];
  main.innerHTML = head(t("library"), t("library_sub"), `<button class="btn" id="savesel">${esc(t("save_selection"))}</button>`) +
    (d.small_org ? `<p class="note">${esc(t("small_org"))}</p>` : "") +
    `<section class="panel">${levels.map((lv) => `<p class="lib-level">${esc(lv)}</p>` + d.items.filter((i) => i.level_label === lv).map((i) => `
      <div class="lib-item"><input type="checkbox" class="pick" value="${esc(i.code)}" ${i.selected ? "checked" : ""} aria-label="${esc(i.title)}">
        <div><h4>${esc(i.title)}</h4><div class="small muted">${esc(i.summary)} · ${esc(i.domain_label)}</div>
          <ul>${i.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul></div>
        <div style="text-align:right">${i.recommended ? `<span class="badge seal">${esc(t("recommended"))}</span><br>` : ""}
          <span class="badge ${i.priority}">${esc(t("priority")[i.priority])} · ${i.score}</span><br>
          <span class="badge" style="margin-top:4px">${esc(i.template === "full" ? t("tpl_full") : t("tpl_structure"))}</span></div></div>`).join("")).join("")}</section>`;
  document.getElementById("savesel").addEventListener("click", async () => {
    const codes = [...main.querySelectorAll(".pick:checked")].map((x) => x.value);
    await api(`/projects/${p.id}/selection`, { method: "PUT", body: { codes } }); toast(t("selection_saved"));
    location.hash = `#/p/${p.id}/decisions`;
  });
}

// ---------------------------------------------------------------- decisions
async function decisionsView(main, p) {
  const groups = await api(`/projects/${p.id}/decisions`);
  main.innerHTML = head(t("decisions"), t("decisions_sub"), `<a class="btn" href="#/p/${esc(p.id)}/drafts">${esc(t("next_step"))}</a>`) +
    (groups.length ? groups.map((g) => `<section class="panel"><h2>${esc(g.title)}</h2>${g.questions.map(questionHTML).join("")}</section>`).join("")
      : `<section class="panel"><p class="muted">${esc(t("no_selection"))}</p></section>`);
  wireQuestions(main, p.id, (r, code) => { if (code === "DEC-EISP-COMMITTEE") decisionsView(main, p); });
}

// ---------------------------------------------------------------- drafts
async function draftsView(main, p) {
  const [pols, issues] = await Promise.all([api(`/projects/${p.id}/policies`), api(`/projects/${p.id}/issues`)]);
  const live = META?.ai_provider === "anthropic";
  main.innerHTML = head(t("drafts"), t("drafts_sub")) + (pols.length ? `
    <section class="panel"><div class="row"><button class="btn" id="genall">${esc(t("generate_all"))}</button>
      ${pols.some((x) => x.stale) ? `<button class="btn ghost" id="genstale">${esc(t("regenerate_stale"))}</button>` : ""}
      <label class="small row"><input type="checkbox" id="tailor" ${live ? "" : "disabled"}> ${esc(t("tailor"))}</label></div>
      ${live ? "" : `<p class="small muted">${esc(t("tailor_off"))}</p>`}</section>
    <section class="panel"><table class="list"><tbody>${pols.map((x) => `<tr>
      <td><strong>${esc(x.title)}</strong><div class="small muted">${esc(x.policy_id)} · ${esc(x.template === "full" ? t("tpl_full") : t("tpl_structure"))}</div></td>
      <td class="small">${x.version ? `${esc(t("version"))} 0.${x.version}${x.stale ? ` <span class="badge medium">${esc(t("stale"))}</span>` : ""}` : `<span class="muted">${esc(t("not_generated"))}</span>`}
        ${x.summary ? `<div class="muted">${x.summary.clauses} ${esc(t("clauses"))} · ${x.summary.open_decisions} ${esc(t("open_dec"))}${x.summary.gaps ? ` · ${x.summary.gaps} ${esc(t("gaps"))}` : ""}</div>` : ""}</td>
      <td>${x.version ? `<a class="btn sm ghost" href="#/p/${esc(p.id)}/policy/${esc(x.id)}">${esc(t("view"))}</a>` : ""}</td></tr>`).join("")}</tbody></table></section>
    ${issuesHTML(issues)}` : `<section class="panel"><p class="muted">${esc(t("no_selection"))}</p></section>`);
  const gen = async (btn, codes) => {
    busy(btn, true);
    try { await api(`/projects/${p.id}/generate`, { method: "POST", body: { codes, tailor_with_ai: document.getElementById("tailor")?.checked || false } }); toast(t("generated")); route(); }
    finally { busy(btn, false); }
  };
  document.getElementById("genall")?.addEventListener("click", (e) => gen(e.target, null));
  document.getElementById("genstale")?.addEventListener("click", (e) => gen(e.target, pols.filter((x) => x.stale).map((x) => x.code)));
  wireIssues(main, () => draftsView(main, p));
}
function issuesHTML(issues) {
  if (!issues.length) return "";
  return `<section class="panel"><h2>${esc(t("issues"))}</h2>${issues.map((i) => `<div class="issue" style="${i.status !== "open" ? "opacity:.6" : ""}">
    <div class="row"><span class="badge ${i.severity}">${esc(t("sev")[i.severity])}</span><span class="small muted">${esc(i.kind.replaceAll("_", " "))}</span><span class="grow"></span>
    ${i.status === "open" ? `<button class="btn sm quiet iss" data-id="${esc(i.id)}" data-s="acknowledged">${esc(t("ack"))}</button><button class="btn sm quiet iss" data-id="${esc(i.id)}" data-s="resolved">${esc(t("resolve"))}</button>`
      : `<button class="btn sm quiet iss" data-id="${esc(i.id)}" data-s="open">${esc(t("reopen"))}</button>`}</div>
    <div>${esc(i.message)}</div>${i.suggestion ? `<div class="small muted">${esc(i.suggestion)}</div>` : ""}</div>`).join("")}</section>`;
}
function wireIssues(main, reload) { on(main, ".iss", "click", async (e, b) => { await api(`/issues/${b.dataset.id}`, { method: "POST", body: { status: b.dataset.s } }); reload(); }); }

// ---------------------------------------------------------------- policy viewer
async function policyView(main, p, docId) {
  const langs = p.doc_language === "both" ? ["en", "fr"] : [p.doc_language];
  let dlang = policyView._lang && langs.includes(policyView._lang) ? policyView._lang : langs.includes(LANG) ? LANG : langs[0];
  const [d, versions] = await Promise.all([api(`/policies/${docId}?lang=${dlang}`, { noLang: true }), api(`/policies/${docId}/versions`)]);
  const b = d.body, basis = t("basis");
  const vnums = [...new Set(versions.map((v) => v.version_no))];
  main.innerHTML = `<div class="page-head"><div><a href="#/p/${esc(p.id)}/drafts" class="small">← ${esc(t("drafts"))}</a></div>
      <div class="row">${langs.length > 1 ? `<div class="lang-toggle">${langs.map((l) => `<button data-dl="${l}" aria-pressed="${l === dlang}">${l.toUpperCase()}</button>`).join("")}</div>` : ""}
      <button class="btn" id="dl">${esc(t("export_doc"))}</button></div></div>
    ${d.stale ? `<p class="note warn">${esc(t("stale_banner"))} <span class="small muted">${esc(d.stale_reason)}</span></p>` : ""}
    <div class="doc-layout"><article class="doc">
      <span class="stamp">${esc(b.language === "fr" ? "ÉBAUCHE — NON APPROUVÉE" : "DRAFT — NOT APPROVED")}</span>
      <h2>${esc(b.title)}</h2><div class="doc-meta">${esc(b.organization)} · ${esc(b.policy_id)} · ${esc(t("version"))} ${esc(b.version)} · ${esc(b.level_label)}</div>
      ${b.sections.map((s) => `<h3>${esc(s.number)}. ${esc(s.heading)}</h3>${s.clauses.map((c) => `
        <div class="clause ${c.edited ? "edited" : ""}" data-id="${esc(c.clause_id)}"><div class="num">${esc(c.number)}</div>
          <div><div class="txt">${marked(c.text)}</div>
          <div class="meta"><span class="badge ${c.source_type === "open_decision" ? "high" : c.source_type === "framework_recommendation" ? "" : "ok"}">${esc(basis[c.source_type] || c.source_type)}</span>
            ${c.legal_review ? `<span class="badge medium">${esc(t("legal"))}</span>` : ""}${c.edited ? `<span class="badge seal">${esc(t("edited"))}</span>` : ""}${c.ai_tailored ? `<span class="badge seal">AI</span>` : ""}
            <span title="${esc(t("refs"))}">${esc(c.framework_refs.join(", "))}</span>
            <button class="link-btn small ed">${esc(t("edit_clause"))}</button></div>
          <div class="edit-area" hidden><textarea>${esc(c.text)}</textarea><div class="row"><button class="btn sm sv">${esc(t("save_clause"))}</button><button class="btn sm quiet cx">${esc(t("cancel"))}</button></div></div>
          </div></div>`).join("")}`).join("")}
    </article><aside class="side">
      <section class="panel"><h2>${esc(t("open_decisions"))} (${b.open_decisions.length})</h2><ul>${b.open_decisions.map((o) => `<li><a href="#" class="jump" data-id="${esc(o.clause_id)}">${esc(o.clause_id)}</a> <span class="badge ${o.severity}">${esc(t("phtype")[o.type] || o.type)}</span> ${esc(o.text)}</li>`).join("")}</ul></section>
      ${b.gaps.length ? `<section class="panel"><h2>${esc(t("impl_gaps"))}</h2><ul>${b.gaps.map((g) => `<li>${esc(g.clause_id)}: ${esc(g.text)}</li>`).join("")}</ul></section>` : ""}
      ${b.assumptions.length ? `<section class="panel"><h2>${esc(t("assumptions"))}</h2><ul>${b.assumptions.map((a) => `<li>${esc(a.text)}</li>`).join("")}</ul></section>` : ""}
      <section class="panel"><h2>${esc(t("versions"))}</h2><ul>${vnums.map((n) => `<li>${n === d.version_no ? `<strong>0.${n}</strong>` : `0.${n}`} <span class="small muted">${esc((versions.find((v) => v.version_no === n)?.created_at || "").slice(0, 16).replace("T", " "))}</span></li>`).join("")}</ul>
        <p class="small muted">${esc(d.generator.provider || "")}${d.generator.model ? " · " + esc(d.generator.model) : ""} · ${esc(d.generator.library_version || "")}</p></section>
    </aside></div>`;
  on(main, "[data-dl]", "click", (e, btn) => { policyView._lang = btn.dataset.dl; policyView(main, p, docId); });
  on(main, ".jump", "click", (e, a) => { e.preventDefault(); main.querySelector(`.clause[data-id="${CSS.escape(a.dataset.id)}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" }); });
  on(main, ".ed", "click", (e, btn) => { const c = btn.closest(".clause"); c.querySelector(".edit-area").hidden = false; c.querySelector("textarea").focus(); });
  on(main, ".cx", "click", (e, btn) => { btn.closest(".edit-area").hidden = true; });
  on(main, ".sv", "click", async (e, btn) => {
    const c = btn.closest(".clause");
    await api(`/policies/${docId}/clauses/${encodeURIComponent(c.dataset.id)}`, { method: "PATCH", body: { text: c.querySelector("textarea").value, lang: dlang }, noLang: true });
    toast(t("saved")); policyView(main, p, docId);
  });
  document.getElementById("dl").addEventListener("click", async (e) => {
    const job = await api(`/projects/${p.id}/exports`, { method: "POST", body: { kind: "docx", document_id: docId, lang: dlang }, noLang: true });
    location.href = job.download;
  });
}

// ---------------------------------------------------------------- export
async function exportView(main, p) {
  const [pols, exports] = await Promise.all([api(`/projects/${p.id}/policies`), api(`/projects/${p.id}/exports`)]);
  const gen = pols.filter((x) => x.version);
  const langs = p.doc_language === "both" ? ["en", "fr"] : [p.doc_language];
  main.innerHTML = head(t("export"), t("export_sub")) + (gen.length ? `
    <div class="grid2"><section class="panel"><h2>${esc(t("export_zip"))}</h2><p class="small muted">${esc(t("export_zip_help"))}</p><button class="btn" id="zip">${esc(t("export_zip"))}</button></section>
    <section class="panel"><h2>${esc(t("export_one"))}</h2>
      <label class="field"><span>${esc(t("document"))}</span><select id="one">${gen.map((x) => `<option value="${esc(x.id)}">${esc(x.policy_id)} — ${esc(x.title)}</option>`).join("")}</select></label>
      <label class="field"><span>${esc(t("language"))}</span><select id="onel">${langs.map((l) => `<option value="${l}">${esc(t("lang_" + l))}</option>`).join("")}</select></label>
      <button class="btn ghost" id="single">${esc(t("export_doc"))}</button></section></div>` : `<section class="panel"><p class="muted">${esc(t("nothing_generated"))}</p></section>`) +
    `<section class="panel"><h2>${esc(t("exports"))}</h2>${exports.length ? `<table class="list"><tbody>${exports.map((j) => `<tr><td><strong>${esc(j.filename)}</strong><div class="small muted">SHA-256 ${esc(j.sha256.slice(0, 16))}… · ${j.files} file(s)</div></td>
      <td class="small">${esc(j.created_at.slice(0, 16).replace("T", " "))}</td><td><a class="btn sm ghost" href="${esc(j.download)}">${esc(t("download"))}</a></td></tr>`).join("")}</tbody></table>` : `<p class="muted">${esc(t("none_yet"))}</p>`}</section>`;
  document.getElementById("zip")?.addEventListener("click", async (e) => {
    busy(e.target, true);
    try { const job = await api(`/projects/${p.id}/exports`, { method: "POST", body: { kind: "zip" } }); location.href = job.download; setTimeout(() => exportView(main, p), 800); }
    finally { busy(e.target, false); }
  });
  document.getElementById("single")?.addEventListener("click", async () => {
    const job = await api(`/projects/${p.id}/exports`, { method: "POST", body: { kind: "docx", document_id: document.getElementById("one").value, lang: document.getElementById("onel").value }, noLang: true });
    location.href = job.download; setTimeout(() => exportView(main, p), 800);
  });
}

route();
