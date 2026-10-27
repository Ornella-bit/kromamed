"use strict";
/* =====================================================================
   KromaMed – application mobile (PWA). Un seul fichier, en 9 parties :
   0 Outils · 1 Icônes · 2 Mémoire du téléphone · 3 Messages · 4 Appels au serveur
   5 Navigation · 6 Écrans · 7 Caméra et minuteur · 8 Actions (boutons) · 9 Démarrage
   ===================================================================== */

/* ---------- 0. Outils ---------- */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pad = (n) => String(n).padStart(2, "0");
const nowText = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`; };
const fmtRead = (s) => (s < 60 ? s + " s" : s % 60 === 0 ? s / 60 + " min" : s + " s");
const fmtClock = (s) => `${Math.floor(s / 60)}:${pad(s % 60)}`;

/* L'état de l'application (ce qui change pendant l'utilisation) */
const S = {
  current: null,      // résultat affiché : { data, source: "camera"|"demo"|"history", entry }
  pid: "", pidKeep: false, // identifiant du test en cours
  testMode: false,    // true = « photo de test (réglage) »
  stream: null, t0: null, tick: null, beeped: {}, armed: false,
  cameraFrom: "#/test", scenarios: [], version: "0.4.0", audio: null,
};

/* ---------- 1. Icônes (dessins vectoriels intégrés) ---------- */
const P = {
  home: '<path d="M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  cam: '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
  hist: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', clock: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 1.5M9 2h6"/>',
  guide: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M8 7h7"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
  back: '<path d="M15 5l-7 7 7 7"/>', chev: '<path d="M9 5l7 7-7 7"/>',
  pdf: '<path d="M6 3h8l4 4v14H6z"/><path d="M9 13h6M9 17h6"/>', save: '<path d="M5 4h12l2 2v14H5z"/><path d="M8 4v5h7V4"/>',
  xls: '<path d="M6 3h8l4 4v14H6z"/><path d="M9 11l6 6M15 11l-6 6"/>', img: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.8"/><path d="M4 18l5-5 4 4 3-3 4 4"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>', down: '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
  up: '<path d="M12 16V5M7 9l5-5 5 5M5 20h14"/>', flask: '<path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
};
function ic(name, s = 24) {
  if (name === "drop") return `<svg width="${s}" height="${s}" viewBox="0 0 100 100" aria-hidden="true"><path d="M50 4C50 4 16 44 16 66A34 34 0 0 0 84 66C84 44 50 4 50 4Z" fill="#fff"/><g transform="rotate(16 50 58)"><rect x="40" y="34" width="20" height="48" rx="6" fill="#1B2A1F"/><rect x="43.5" y="38.5" width="13" height="10" rx="3" fill="#2A9D8F"/><rect x="43.5" y="52.5" width="13" height="10" rx="3" fill="#1E7F5C"/><rect x="43.5" y="66.5" width="13" height="10" rx="3" fill="#E6D77A"/></g></svg>`;
  return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[name]}</svg>`;
}

/* ---------- 2. Mémoire du téléphone (rien n'est envoyé au serveur) ---------- */
const HKEY = "kromamed_history_v1", PKEY = "kromamed_profile_v1";
function readJSON(key, fallback) { try { const v = JSON.parse(localStorage.getItem(key)); return v ?? fallback; } catch (e) { return fallback; } }
function writeJSON(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch (e) { return false; } }
const getHistory = () => { const h = readJSON(HKEY, []); return Array.isArray(h) ? h : []; };
const setHistory = (h) => writeJSON(HKEY, h.slice(-200));
const getProfile = () => { const p = readJSON(PKEY, {}); return { name: typeof p.name === "string" ? p.name : "" }; };
const nextId = () => `TEST_${String(getHistory().length + 1).padStart(3, "0")}`;

/* ---------- 3. Messages : petite bulle, attente, confirmation ---------- */
let toastTimer;
function toast(msg, isError = false) {
  const t = $("#toast"); t.textContent = msg; t.className = isError ? "err" : ""; t.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => (t.hidden = true), 4200);
}
function setBusy(on, text = "Analyse en cours…") { $("#busy-text").textContent = text; $("#busy").hidden = !on; }
function confirmSheet({ title, text, ok, danger = false }) {
  return new Promise((resolve) => {
    const sh = $("#sheet");
    sh.innerHTML = `<div class="sheet"><h3>${esc(title)}</h3><p>${esc(text)}</p>
      <button class="btn ${danger ? "danger" : "primary"}" data-r="1">${esc(ok)}</button>
      <button class="btn out" data-r="0">Annuler</button></div>`;
    sh.hidden = false;
    sh.onclick = (e) => { const b = e.target.closest("[data-r]"); if (b || e.target === sh) { sh.hidden = true; resolve(!!b && b.dataset.r === "1"); } };
  });
}

/* ---------- 4. Appels au serveur ---------- */
async function api(url, options) {
  let r;
  try { r = await fetch(url, options); }
  catch (e) { throw new Error("Pas de connexion au serveur. L'analyse a besoin d'Internet pour l'instant."); }
  let d = null; try { d = await r.json(); } catch (e) { /* réponse sans JSON */ }
  if (!r.ok) throw new Error((d && d.detail) || "Erreur du serveur.");
  return d;
}
async function downloadFile(url, body, filename) {
  setBusy(true, "Préparation du fichier…");
  try {
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) { let d = {}; try { d = await r.json(); } catch (e) {} throw new Error(d.detail || "Téléchargement impossible."); }
    saveBlob(await r.blob(), filename);
  } catch (e) { toast(e.message || "Téléchargement impossible.", true); } finally { setBusy(false); }
}
function saveBlob(blob, filename) {
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = filename;
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}
const stripImages = (data) => { const c = { ...data }; delete c.images; return c; };

/* ---------- 5. Navigation (une adresse # par écran) ---------- */
const SCREENS = ["home", "test", "camera", "result", "history", "guide", "profile"];
const ROUTES = { "/": "home", "/test": "test", "/camera": "camera", "/result": "result", "/history": "history", "/guide": "guide", "/profile": "profile" };
let currentScreen = "home";
const nameOf = (h) => ROUTES[(h || "").replace(/^#/, "") || "/"] || "home";
const hashOf = (name) => "#" + Object.keys(ROUTES).find((k) => ROUTES[k] === name);

/* Bouton RETOUR : sous-page -> onglet -> accueil -> sortie de l'application.
   L'historique du navigateur ne contient jamais plus de 2 entrées : [accueil] et l'écran courant.
   Ainsi « retour » revient toujours à l'accueil, sauf pour les sous-pages (voir parentOf). */
function parentOf(name) {
  if (name === "camera") return S.cameraFrom === "#/test" ? "test" : S.cameraFrom === "#/profile" ? "profile" : "home";
  if (name === "result") return S.current && S.current.source === "history" ? "history" : S.testMode ? "profile" : "home";
  return "home";
}
let leavingToHome = false;
function go(hash) {
  const name = nameOf(hash);
  if (name === currentScreen) { showScreen(name); return; }
  if (name === "home") { leavingToHome = true; history.back(); return; }          // on dépile jusqu'à l'accueil
  if (currentScreen === "home") history.pushState({ n: name }, "", hashOf(name));   // accueil -> écran : on empile
  else history.replaceState({ n: name }, "", hashOf(name));                          // écran -> écran : on remplace
  showScreen(name);
}
window.addEventListener("popstate", () => {          // touche RETOUR du téléphone (ou bouton ← de l'application)
  const name = nameOf(location.hash);
  if (name === "home") {
    if (leavingToHome) leavingToHome = false;
    else if (currentScreen !== "home") {
      const parent = parentOf(currentScreen);
      if (parent !== "home") { history.pushState({ n: parent }, "", hashOf(parent)); showScreen(parent); return; }
    }
    showScreen("home");
  } else showScreen(name);
});
function showScreen(name) {
  if (name === "result" && !S.current) name = "home";
  if (currentScreen === "camera" && name !== "camera") leaveCamera();
  currentScreen = name;
  SCREENS.forEach((n) => $("#s-" + n).classList.toggle("on", n === name));
  document.body.classList.toggle("nonav", name === "camera");
  const tab = name === "result" ? (S.current.source === "history" ? "history" : "home") : name === "test" ? "home" : name;
  $$(".tab").forEach((t) => t.classList.toggle("on", t.dataset.tab === tab));
  ({ home: renderHome, test: renderTest, camera: enterCamera, result: renderResult, history: renderHistory, guide() {}, profile: renderProfile })[name]();
  $("#s-" + name).scrollTop = 0;
}

/* ---------- 6. Écrans ---------- */
const pillFor = (entry) => {
  const r = entry.result || {}, bad = (r.pads || []).filter((p) => p.normal === false).length || entry.abnormal || 0;
  return bad ? `<span class="pill bad">${bad} anomalie${bad > 1 ? "s" : ""}</span>` : `<span class="pill ok">Normal</span>`;
};
function entryRow(e) {
  return `<button class="row" data-act="open" data-id="${esc(e.id ?? "")}"><div class="grow"><b>${esc(e.patient_id || "ANONYME")}</b><small>${esc(e.date)}</small></div>${pillFor(e)}<span class="chev">${ic("chev", 18)}</span></button>`;
}

function renderHome() {
  const name = getProfile().name.trim(), h = getHistory();
  $("#hello").hidden = !name; $("#hello").textContent = name ? `Bonjour, ${name}` : "";
  $("#home-count").textContent = `${h.length} test${h.length > 1 ? "s" : ""}`;
  $("#demo-chips").innerHTML = S.scenarios.length
    ? S.scenarios.map((s) => `<button class="chip${s.label.includes("refusée") ? " bad" : ""}" data-act="demo" data-id="${esc(s.id)}">${esc(s.label)}</button>`).join("")
    : `<span class="note">Démos indisponibles hors connexion.</span>`;
}

function renderTest() { $("#pid").value = S.pidKeep && S.pid ? S.pid : nextId(); }

function qualityHTML(q) {
  const CRIT = [["markers", "Repères visibles"], ["sharpness", "Netteté"], ["exposure", "Exposition"], ["illumination", "Éclairage uniforme"], ["calibration", "Étalonnage couleurs"]];
  return CRIT.map(([k, label]) => {
    const v = q[k] ?? 0;
    return `<div class="q${v < 0.85 ? " fail" : ""}"><span>${label}</span><div class="meter"><i style="width:${Math.round(v * 100)}%"></i><u></u></div><b>${Math.round(v * 100)} %</b></div>`;
  }).join("");
}

function renderResult() {
  const { data, source, entry } = S.current, s = data.summary, q = data.quality, ok = data.status === "ok";
  const tech = S.testMode && source === "camera";
  let html = `<header class="hd bar"><button class="back" data-act="resback" aria-label="Retour">${ic("back")}</button>
    <div><h1>${tech ? "Photo de test" : "Résultat"}</h1><small>${esc(source === "history" ? entry.patient_id + " · " + entry.date : source === "demo" ? "Photo simulée" : "Qualité de la capture : " + Math.round(q.overall * 100) + " %")}</small></div></header>`;
  html += `<div class="banner ${esc(s.level)}"><h2>${esc(s.headline)}</h2>${s.details.map((d) => `<p>${esc(d)}</p>`).join("")}</div>`;
  if (ok) {
    html += `<h2 class="sec" style="margin-top:6px">Résultats par paramètre</h2><div class="card flush">` + data.pads.map((p) => {
      let cls = "unk", st = "Indéterminé";
      if (p.status === "ok") { cls = p.normal ? "ok" : "bad"; st = p.normal ? "Normal" : "Anormal"; }
      return `<div class="row"><div class="grow"><b>${esc(p.label)}</b><small>lecture idéale : ${fmtRead(p.read_time_s)}</small></div><span class="val">${esc(p.level ?? "—")}</span><span class="pill ${cls}">${st}</span></div>`;
    }).join("") + `</div>`;
  }
  html += `<details class="card" ${!ok || tech ? "open" : ""}><summary>Qualité de la capture : ${Math.round(q.overall * 100)} %<span class="chev">${ic("chev", 18)}</span></summary>
    <p class="note" style="margin-top:0">Seuil de sécurité : 85 % (trait noir). En dessous, aucune lecture n'est rendue.</p>${qualityHTML(q)}</details>`;
  if (data.images && (tech || source === "demo")) {
    const im = data.images, fig = (src, cap) => src ? `<figure><img src="${src}" alt="${esc(cap)}"><figcaption>${esc(cap)}</figcaption></figure>` : "";
    html += `<details class="card" ${tech ? "open" : ""}><summary>Ce que voit le moteur<span class="chev">${ic("chev", 18)}</span></summary><div class="imgs">${fig(im.input, "Photo analysée")}${fig(im.card_raw, "Carte redressée")}${fig(im.card_result || im.card_corrected, "Corrigée + lecture")}</div></details>`;
  }
  if (tech) html += `<details class="card"><summary>Détails techniques (JSON)<span class="chev">${ic("chev", 18)}</span></summary><pre>${esc(JSON.stringify(stripImages(data), null, 2))}</pre></details>`;
  html += `<div class="actions">`;
  if (tech) html += `<div class="two"><button class="btn primary" data-act="reshoot">${ic("cam", 20)}Nouvelle photo</button><button class="btn out" data-go="#/profile">Terminer</button></div>`;
  else if (!ok) html += `<button class="btn primary" data-act="reshoot">${ic("cam", 20)}Reprendre la photo</button>`;
  else if (source === "history") html += `<div class="two"><button class="btn primary" data-act="pdf">${ic("pdf", 20)}Rapport PDF</button><button class="btn danger" data-act="delone">${ic("trash", 20)}Supprimer</button></div>`;
  else html += `<div class="two"><button class="btn primary" data-act="pdf">${ic("pdf", 20)}Rapport PDF</button><button class="btn out" data-act="save">${ic("save", 20)}Enregistrer</button></div>`;
  html += `</div>`;
  $("#result-body").innerHTML = html;
}

function renderHistory() {
  const h = getHistory();
  $("#hist-sub").textContent = `${h.length} test${h.length > 1 ? "s" : ""} sur cet appareil`;
  $("#history-body").innerHTML = h.length
    ? `<div class="card flush">${h.slice().reverse().map(entryRow).join("")}</div>
       <div style="padding:0 16px 20px"><button class="btn out" data-act="xlsx">${ic("xls", 20)}Exporter vers Excel</button></div>`
    : `<div class="card empty">Aucun test enregistré pour l'instant.<br><br><button class="btn primary" data-go="#/test">Faire un test</button></div>`;
}

function renderProfile() {
  const name = getProfile().name;
  const row = (act, icon, title, sub, cls = "") => `<button class="setrow ${cls}" data-act="${act}"><i>${ic(icon, 24)}</i><div><b>${title}</b><span>${sub}</span></div></button>`;
  $("#profile-body").innerHTML = `
    <div class="card"><div class="avatar">${esc((name.trim()[0] || "?").toUpperCase())}</div>
      <label class="f" for="uname">Votre nom (facultatif)</label>
      <input type="text" id="uname" maxlength="40" value="${esc(name)}" placeholder="ex. Ashley" autocomplete="off">
      <button class="btn primary sm" style="margin-top:10px" data-act="savename">Enregistrer</button></div>
    <details class="card"><summary>${ic("info", 20)}&nbsp;À propos de l'application<span class="chev">${ic("chev", 18)}</span></summary>
      <div class="abt"><p><b>KromaMed ${esc(S.version)}</b> : lecture colorimétrique de bandelettes urinaires <b>Multistix 10 SG</b> (10 paramètres) avec un smartphone et une carte d'étalonnage imprimée.</p>
      <p>Les photos sont analysées en mémoire par le serveur et <b>jamais conservées</b>. Votre historique reste sur cet appareil.</p>
      <p>Les couleurs de référence sont des <b>valeurs de démonstration</b>, non validées cliniquement. Application en phase de prototype.</p>
      <p><b>KromaMed est une aide à la lecture, pas un diagnostic médical.</b> Consultez un professionnel de santé.</p></div></details>
    <h2 class="sec">Paramètres</h2>
    <div class="card flush">
      ${row("testmode", "flask", "Photo de test (réglage)", "Vérifier la caméra et voir les contrôles qualité en détail")}
      ${row("xlsx", "xls", "Exporter l'historique", "Fichier Excel de tous vos tests")}
      ${row("backup", "down", "Sauvegarder mes données", "Télécharger un fichier de sauvegarde")}
      ${row("restore", "up", "Restaurer une sauvegarde", "Remplacer les données par un fichier de sauvegarde")}
      ${row("wipe", "trash", "Supprimer tous les tests", "Efface l'historique de cet appareil", "dg")}
    </div><p class="note" style="margin:0 16px 24px;text-align:center">Version ${esc(S.version)}</p>`;
}

/* ---------- 7. Caméra et minuteur ---------- */
function enterCamera() {
  const t = S.testMode;
  $("#cam-title").textContent = t ? "Photo de test (réglage)" : "Nouveau test";
  $("#cam-sub").textContent = t ? "Contrôle de la caméra et de la qualité" : S.t0 ? "Étape 5 sur 5 · Photo" : "Photo sans minuteur";
  updateTimerUI();
  clearInterval(S.tick); if (S.t0) S.tick = setInterval(updateTimerUI, 250);
  startCamera();
}
function leaveCamera() { stopCamera(); clearInterval(S.tick); }
async function startCamera() {
  const err = $("#cam-error"); err.hidden = true;
  stopCamera();
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    err.textContent = "La caméra intégrée demande une connexion sécurisée (https). Utilisez le bouton de droite pour ouvrir l'appareil photo du téléphone."; err.hidden = false; return;
  }
  try {
    S.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 2560 }, height: { ideal: 1920 } }, audio: false });
    const v = $("#video"); v.srcObject = S.stream; await v.play();
  } catch (e) {
    err.textContent = e && e.name === "NotAllowedError"
      ? "Accès à la caméra refusé. Autorisez-la dans les réglages du navigateur, ou utilisez le bouton de droite."
      : "Caméra indisponible. Utilisez le bouton de droite (appareil photo du téléphone) ou le bouton de gauche (galerie).";
    err.hidden = false;
  }
}
function stopCamera() { if (S.stream) { S.stream.getTracks().forEach((t) => t.stop()); S.stream = null; } const v = $("#video"); if (v) v.srcObject = null; }

function beep() {
  try { const c = S.audio || new (window.AudioContext || window.webkitAudioContext)(); S.audio = c; const o = c.createOscillator(), g = c.createGain();
    o.connect(g); g.connect(c.destination); o.frequency.value = 880; g.gain.value = 0.15; o.start(); setTimeout(() => o.stop(), 350); } catch (e) { /* pas de son */ }
  if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
}
function updateTimerUI() {
  const ring = $("#ring"), clock = $("#clock"), sub = $("#clock-sub"), chip = $("#tchip");
  if (!S.t0 || S.testMode) { ring.setAttribute("stroke-dashoffset", 0); ring.setAttribute("stroke", "#F2B134"); clock.textContent = "Photo"; sub.textContent = ""; chip.hidden = true; return; }
  const s = Math.floor((Date.now() - S.t0) / 1000);
  ring.setAttribute("stroke-dashoffset", 289 * (1 - Math.min(s, 60) / 60));
  ring.setAttribute("stroke", s >= 60 ? "#3FC58A" : "#F2B134");
  clock.textContent = fmtClock(s); chip.hidden = false;
  if (s >= 120) { chip.className = "tchip late"; chip.textContent = "2 min : les leucocytes sont lisibles"; sub.textContent = "photo !"; if (!S.beeped[120]) { S.beeped[120] = 1; beep(); } }
  else if (s >= 60) { chip.className = "tchip go"; chip.textContent = "Photographiez maintenant (60 s)"; sub.textContent = "photo !"; if (!S.beeped[60]) { S.beeped[60] = 1; beep(); } }
  else { chip.className = "tchip"; chip.textContent = "Attendez… photo à 60 s"; sub.textContent = "photo à 1:00"; }
}
function shoot() {
  if (S.t0 && !S.testMode && Date.now() - S.t0 < 60000 && !S.armed) {
    S.armed = true; setTimeout(() => (S.armed = false), 4000);
    toast("Pas encore 60 s : la lecture sera moins fiable. Touchez encore pour photographier quand même."); return;
  }
  const v = $("#video");
  if (!S.stream || !v.videoWidth) { toast("Caméra pas prête. Utilisez les boutons à gauche ou à droite.", true); return; }
  const c = document.createElement("canvas"); c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext("2d").drawImage(v, 0, 0);
  c.toBlob((b) => analyzeBlob(b), "image/jpeg", 0.92);
}
async function analyzeBlob(blob) {
  setBusy(true);
  try {
    const fd = new FormData(); fd.append("file", blob, "photo.jpg");
    S.current = { data: await api("/api/analyze", { method: "POST", body: fd }), source: "camera" };
    go("#/result");
  } catch (e) { toast(e.message, true); } finally { setBusy(false); }
}

/* ---------- 8. Actions (chaque bouton avec data-act="nom") ---------- */
function startTest(withTimer) {
  S.pid = $("#pid").value.trim() || nextId(); S.pidKeep = true; S.testMode = false; S.cameraFrom = "#/test";
  S.beeped = {}; S.armed = false; S.t0 = withTimer ? Date.now() : null;
  if (withTimer) { try { S.audio = S.audio || new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} }  // débloque le son
  go("#/camera");
}
const entryOf = () => S.current.entry || { patient_id: S.pid, date: nowText() };
const ACT = {
  start: () => startTest(true),
  notimer: () => startTest(false),
  camback: () => history.back(),
  shutter: shoot,
  gallery: () => $("#f-gallery").click(),
  native: () => $("#f-native").click(),
  reshoot() { S.armed = false; if (S.testMode) S.cameraFrom = "#/profile"; go("#/camera"); },
  resback() { history.back(); },
  async demo(el) {
    setBusy(true, "Analyse de la démonstration…");
    try { S.testMode = false; S.pid = "DEMO"; S.pidKeep = false; S.current = { data: await api("/api/demo/" + el.dataset.id), source: "demo" }; go("#/result"); }
    catch (e) { toast(e.message, true); } finally { setBusy(false); }
  },
  pdf() { const e = entryOf(); downloadFile("/api/report", { patient_id: e.patient_id, date: e.date, result: stripImages(S.current.data) }, "rapport_kromamed.pdf"); },
  save(el) {
    const d = stripImages(S.current.data), results = {};
    d.pads.forEach((p) => (results[p.param] = p.level));
    const h = getHistory();
    h.push({ id: Date.now(), date: nowText(), patient_id: S.pid || nextId(), result: d, results, abnormal: d.pads.filter((p) => p.normal === false).length, headline: d.summary.headline });
    if (setHistory(h)) { S.pidKeep = false; el.disabled = true; el.innerHTML = "✓ Enregistré"; toast("Test enregistré dans l'historique."); } else toast("Enregistrement impossible (mémoire pleine ?).", true);
  },
  open(el) {
    const e = getHistory().find((x) => String(x.id) === el.dataset.id);
    if (!e || !e.result) { toast("Ce test ancien n'a pas de détails à afficher."); return; }
    S.testMode = false; S.current = { data: e.result, source: "history", entry: e }; go("#/result");
  },
  async delone() {
    if (!(await confirmSheet({ title: "Supprimer ce test ?", text: "Il sera effacé de l'historique de cet appareil.", ok: "Supprimer", danger: true }))) return;
    const id = String(S.current.entry.id); setHistory(getHistory().filter((x) => String(x.id) !== id)); S.current = null; toast("Test supprimé."); go("#/history");
  },
  xlsx() {
    const h = getHistory(); if (!h.length) { toast("Aucun test à exporter."); return; }
    downloadFile("/api/history/xlsx", { rows: h.map((e) => ({ date: e.date, patient_id: e.patient_id, results: e.results || {} })) }, "historique_kromamed.xlsx");
  },
  savename() {
    const name = $("#uname").value.trim(); writeJSON(PKEY, { name }); toast(name ? "Profil enregistré." : "Nom effacé."); renderProfile();
  },
  testmode() { S.testMode = true; S.pid = "REGLAGE"; S.pidKeep = false; S.t0 = null; S.cameraFrom = "#/profile"; go("#/camera"); },
  backup() {
    const payload = { app: "kromamed", version: 1, exported: nowText(), profile: getProfile(), history: getHistory() };
    saveBlob(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }), `sauvegarde_kromamed_${nowText().slice(0, 10)}.json`);
    toast("Sauvegarde téléchargée.");
  },
  restore() { $("#f-restore").click(); },
  async wipe() {
    if (!(await confirmSheet({ title: "Supprimer tous les tests ?", text: "Cette action est définitive. Pensez à faire une sauvegarde avant.", ok: "Tout supprimer", danger: true }))) return;
    setHistory([]); toast("Tous les tests ont été supprimés."); renderProfile();
  },
};
document.addEventListener("click", (e) => {
  const a = e.target.closest("[data-act]");
  if (a) { const f = ACT[a.dataset.act]; if (f) f(a, e); return; }
  const g = e.target.closest("[data-go]"); if (g) go(g.dataset.go);
});
$("#f-gallery").addEventListener("change", (e) => { const f = e.target.files[0]; e.target.value = ""; if (f) analyzeBlob(f); });
$("#f-native").addEventListener("change", (e) => { const f = e.target.files[0]; e.target.value = ""; if (f) analyzeBlob(f); });
$("#f-restore").addEventListener("change", async (e) => {
  const f = e.target.files[0]; e.target.value = ""; if (!f) return;
  try {
    const o = JSON.parse(await f.text());
    if (!o || o.app !== "kromamed" || !Array.isArray(o.history)) throw new Error();
    if (!(await confirmSheet({ title: "Restaurer cette sauvegarde ?", text: `${o.history.length} test(s) remplaceront vos données actuelles.`, ok: "Restaurer" }))) return;
    setHistory(o.history); writeJSON(PKEY, { name: (o.profile && o.profile.name) || "" }); toast("Sauvegarde restaurée."); renderProfile();
  } catch (err) { toast("Fichier de sauvegarde non valide.", true); }
});

/* ---------- 9. Démarrage ---------- */
$$("[data-i]").forEach((el) => (el.innerHTML = ic(el.dataset.i, +el.dataset.s || 24)));
// Au chargement : si on ouvre directement un écran (rechargement), on place l'accueil en dessous pour que RETOUR fonctionne.
{
  let first = nameOf(location.hash);
  if (first === "result") first = "home";                 // pas de résultat après un rechargement
  history.replaceState({ n: "home" }, "", "#/");
  if (first !== "home") history.pushState({ n: first }, "", hashOf(first));
  showScreen(first);
}
fetch("/api/scenarios").then((r) => r.json()).then((l) => { S.scenarios = l; if (currentScreen === "home") renderHome(); }).catch(() => {});
fetch("/api/health").then((r) => r.json()).then((d) => { S.version = d.version; }).catch(() => {});
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
