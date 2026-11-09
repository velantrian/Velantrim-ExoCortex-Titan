(() => {
  const K = "velantrim_research_app_v1";
  const AK = "velantrim_research_audit_v1";
  const allowed = ["Supported", "Validated", "ImmutableCore"];
  const pending = ["Observed", "Hypothesized"];
  const esm = {
    Observed: ["Hypothesized", "Deprecated", "Retracted"],
    Hypothesized: ["Supported", "Contradicted", "Deprecated", "Retracted"],
    Supported: ["Validated", "Contradicted", "Deprecated", "Retracted"],
    Validated: ["ImmutableCore", "Contradicted", "Deprecated", "Retracted"],
    ImmutableCore: [],
    Contradicted: ["Deprecated", "Hypothesized", "Retracted"],
    Deprecated: [],
    Retracted: [],
  };
  const levels = ["domain", "concept", "mechanism", "evidence", "principle"];
  const stop = new Set("и в на с что это по к из за не как или но the a an of to in is it was for are with und die der das ist ein eine mit von zu den".split(" "));
  let facts = JSON.parse(localStorage.getItem(K) || "[]");
  let audit = JSON.parse(localStorage.getItem(AK) || "[]");
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
  const save = () => { localStorage.setItem(K, JSON.stringify(facts)); localStorage.setItem(AK, JSON.stringify(audit)); };
  const tok = (s) => (String(s || "").toLowerCase().match(/[a-zа-яё0-9]{3,}/gi) || []).filter((w) => !stop.has(w));
  const days = (iso) => Math.max(0, (Date.now() - new Date(iso || Date.now()).getTime()) / 86400000);
  const retention = (f) => Math.pow(1 + (19 / 81) * (days(f.last_accessed) / Math.max(f.stability || 1, 0.1)), -0.5);
  async function sha(s) {
    const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
    return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
  }
  async function log(fact_id, event, payload = {}) {
    const at = new Date().toISOString();
    const prev_hash = audit.at(-1)?.entry_hash || "0".repeat(64);
    const canonical = JSON.stringify({ fact_id, event, payload, at });
    const entry_hash = await sha(prev_hash + canonical);
    audit.push({ id: audit.length + 1, fact_id, event, payload, at, prev_hash, entry_hash });
    save();
  }
  async function verifyAudit() {
    let prev = "0".repeat(64);
    for (const r of audit) {
      const canonical = JSON.stringify({ fact_id: r.fact_id, event: r.event, payload: r.payload, at: r.at });
      const h = await sha(prev + canonical);
      if (h !== r.entry_hash || r.prev_hash !== prev) return { ok: false, id: r.id };
      prev = r.entry_hash;
    }
    return { ok: true, id: null };
  }
  function classify(q) {
    const x = String(q || "").toLowerCase();
    if (/^(почему|зачем|why|warum|как|how|wie)/.test(x)) return "mechanism";
    if (/^(докажи|источник|откуда|source|evidence)/.test(x)) return "evidence";
    if (/(принцип|закон|правило|principle|rule)/.test(x)) return "principle";
    if (/(домен|область|domain)/.test(x)) return "domain";
    return "concept";
  }
  function score(q, f) {
    const qs = new Set(tok(q));
    const fs = new Set(tok(f.claim + " " + f.level + " " + f.layer));
    let n = 0;
    qs.forEach((w) => { if (fs.has(w)) n += 1; });
    return n / Math.max(1, qs.size);
  }
  function search(q) {
    const start = classify(q);
    const out = [];
    const path = [];
    let i = levels.indexOf(start);
    if (i < 0) i = 1;
    for (let d = 0; d < 4 && i < levels.length; d++, i++) {
      const lv = levels[i];
      const found = facts
        .map((f) => ({ ...f, _score: score(q, f) + (f.level === lv ? 0.15 : 0) }))
        .filter((f) => f._score > 0.05 && (f.layer === "L3" || f.layer === "L2"))
        .sort((a, b) => b._score - a._score)
        .slice(0, 5);
      out.push(...found);
      path.push(`${lv}:${found.length}`);
      const avg = found.reduce((s, f) => s + (f.confidence || 0.5), 0) / Math.max(1, found.length);
      if (found.length && avg >= 0.72) break;
    }
    const seen = new Set();
    return { path, facts: out.filter((f) => !seen.has(f.id) && seen.add(f.id)).slice(0, 8), start };
  }
  function gate(fs) {
    if (!fs.length) return { passed: false, reason: "⚠️ Нет фактов в Research-памяти по этой теме." };
    const v = fs.filter((f) => allowed.includes(f.state));
    if (!v.length) return { passed: false, reason: "⚠️ Все найденные факты Pending: нужен Support/Validate." };
    const avg = v.reduce((s, f) => s + (Number(f.confidence) || 0.5), 0) / v.length;
    if (avg < 0.35) return { passed: false, reason: `⚠️ Низкая уверенность: ${Math.round(avg * 100)}%.` };
    return { passed: true, reason: null, valid: v, avg };
  }
  function faith(answer, fs) {
    const a = new Set(tok(answer));
    const f = new Set(fs.flatMap((x) => tok(x.claim)));
    let n = 0;
    a.forEach((w) => { if (f.has(w)) n += 1; });
    return a.size ? n / a.size : 0;
  }
  async function addFact(claim, layer, state, level, confidence) {
    const id = "rf_" + Date.now().toString(36) + "_" + Math.random().toString(16).slice(2, 6);
    const f = { id, claim: claim.trim(), layer, state, level, confidence: Number(confidence) || 0.5, stability: 1, last_accessed: new Date().toISOString(), guardian_verified: allowed.includes(state) };
    facts.unshift(f);
    await log(id, "fact_created", { layer, state, level, confidence: f.confidence });
    save();
    render();
  }
  async function transition(id, to) {
    const f = facts.find((x) => x.id === id);
    if (!f || !esm[f.state]?.includes(to)) return alert(`Переход ${f?.state} → ${to} запрещён ESM.`);
    const from = f.state;
    f.state = to;
    f.guardian_verified = allowed.includes(to);
    await log(id, "esm_transition", { from, to });
    save();
    render();
  }
  async function promote(id) {
    const f = facts.find((x) => x.id === id);
    if (!f) return;
    if (!["Supported", "Validated"].includes(f.state)) return alert("В L3 можно только Supported/Validated.");
    const g = gate([f]);
    if (!g.passed) return alert(g.reason);
    f.layer = "L3";
    f.state = "Validated";
    f.guardian_verified = true;
    await log(id, "promoted_to_l3", { confidence: f.confidence });
    save();
    render();
  }
  function textRank(text, n = 5) {
    const s = String(text || "").split(/[.!?\n]+/).map((x) => x.trim()).filter((x) => x.length > 25);
    const freq = {};
    s.forEach((x) => tok(x).forEach((w) => { freq[w] = (freq[w] || 0) + 1; }));
    return s.map((x, i) => ({ x, i, v: tok(x).reduce((a, w) => a + (freq[w] || 0), 0) / Math.max(1, tok(x).length) }))
      .sort((a, b) => b.v - a.v).slice(0, n).sort((a, b) => a.i - b.i).map((x) => x.x);
  }
  async function ask() {
    const q = $("q").value.trim();
    if (!q) return;
    const r = search(q);
    const g = gate(r.facts);
    let answer;
    if (!g.passed) {
      answer = g.reason;
    } else {
      answer = "Опираюсь на Research L3/L2:\n" + g.valid.map((f) => `• ${f.claim}`).join("\n");
      for (const f of g.valid) {
        f.last_accessed = new Date().toISOString();
        f.stability = Math.min(100, (f.stability || 1) * 1.15);
      }
      await log("response", "answer_generated", { q, facts: g.valid.map((f) => f.id) });
    }
    const faithfulness = g.passed ? faith(answer, g.valid) : 0;
    $("answer").textContent = answer;
    $("trace").textContent = JSON.stringify({
      query: q,
      query_type: r.start.toUpperCase(),
      retrieval_path: r.path,
      truth_gate_passed: g.passed,
      truth_gate_reason: g.reason,
      facts_used: (g.valid || []).map((f) => ({ id: f.id, state: f.state, layer: f.layer, retention: +retention(f).toFixed(2), claim: f.claim })),
      facts_discarded: r.facts.filter((f) => !allowed.includes(f.state)).map((f) => ({ id: f.id, state: f.state, claim: f.claim })),
      guardian_score: +faithfulness.toFixed(2),
      guardian_warn: faithfulness < 0.3 && g.passed,
      answer_allowed: g.passed,
    }, null, 2);
    save();
    render();
  }
  function render() {
    $("cFacts").textContent = facts.length;
    $("cPend").textContent = facts.filter((f) => pending.includes(f.state)).length;
    $("cL3").textContent = facts.filter((f) => f.layer === "L3").length;
    $("cAudit").textContent = audit.length;
    $("facts").innerHTML = facts.map((f) => `
      <div class="fact">
        <b>${esc(f.claim)}</b>
        <div class="meta">${esc(f.layer)} · ${esc(f.level)} · ${esc(f.state)} · conf ${Math.round((f.confidence || 0) * 100)}% · R ${Math.round(retention(f) * 100)}%</div>
        <div class="btns">
          ${esm[f.state]?.includes("Supported") ? `<button data-act="sup" data-id="${f.id}">✅ Support</button>` : ""}
          ${["Supported", "Validated"].includes(f.state) ? `<button data-act="l3" data-id="${f.id}">🧠 L3</button>` : ""}
          ${esm[f.state]?.includes("Deprecated") ? `<button data-act="dep" data-id="${f.id}">🗑 Deprecate</button>` : ""}
        </div>
      </div>`).join("") || `<div class="hint">Пока фактов нет.</div>`;
  }
  document.addEventListener("click", async (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.id === "save" && $("claim").value.trim()) await addFact($("claim").value, $("layer").value, $("state").value, $("level").value, $("conf").value);
    if (b.id === "seed") {
      await addFact("Деревья производят кислород через фотосинтез.", "L3", "Validated", "mechanism", 0.9);
      await addFact("Лес поглощает CO2 и поддерживает экосистему.", "L3", "Supported", "principle", 0.74);
      await addFact("Пользователь сказал, что деревья важны для тени.", "L2", "Observed", "evidence", 0.55);
    }
    if (b.id === "rank") {
      const top = textRank($("bulk").value, 5);
      for (const s of top) await addFact(s, "L2", "Hypothesized", "concept", 0.55);
      $("rankOut").textContent = top.length ? `Сохранено L2: ${top.length}` : "Нет достаточно длинных предложений.";
    }
    if (b.id === "ask") await ask();
    if (b.id === "audit") {
      const v = await verifyAudit();
      alert(v.ok ? `✅ Audit-chain целостна: ${audit.length}` : `❌ Audit-chain сломана на #${v.id}`);
    }
    if (b.id === "wipe" && confirm("Очистить только Research sandbox в браузере?")) { facts = []; audit = []; save(); render(); $("answer").textContent = "Research sandbox очищен."; $("trace").textContent = "TRACE очищен."; }
    if (b.dataset.act === "sup") await transition(b.dataset.id, "Supported");
    if (b.dataset.act === "dep") await transition(b.dataset.id, "Deprecated");
    if (b.dataset.act === "l3") await promote(b.dataset.id);
  });
  render();
})();
