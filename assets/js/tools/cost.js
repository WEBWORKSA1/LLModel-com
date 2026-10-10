/* LLM API cost calculator. */
(function () {
  "use strict";
  var D = window.LLM_DATA, L = window.LLM;
  if (!D || !L) return;
  var $ = function (id) { return document.getElementById(id); };
  var el = { in: $("cc-in"), out: $("cc-out"), req: $("cc-req"), days: $("cc-days"), cache: $("cc-cache"), cacheOut: $("cc-cache-out"),
    batch: $("cc-batch"), legacy: $("cc-legacy"), bars: $("cc-bars"), pinned: $("cc-pinned"), pinnedH: $("cc-pinned-h"), summary: $("cc-summary"), cta: $("cc-cta") };
  var PRESETS = {
    chatbot: [2000, 400, 1000], rag: [6000, 500, 500], summaries: [12000, 800, 70], coding: [60000, 6000, 35], classify: [400, 20, 20000]
  };
  var weightsFilter = "", showAll = false;
  var by = {}; D.models.forEach(function (m) { by[m.s] = m; });
  var pinned = (L.params.get("models") || L.params.get("model") || "").split(",").filter(function (s) { return by[s]; });

  function setPreset(name) {
    var p = PRESETS[name]; if (!p) return;
    el.in.value = p[0]; el.out.value = p[1]; el.req.value = p[2];
    Array.prototype.forEach.call(document.querySelectorAll("#cc-presets button"), function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-preset") === name ? "true" : "false"); });
  }
  function num(x, d) { var v = parseFloat(x.value); return isNaN(v) || v < 0 ? d : v; }
  function compute() {
    var tin = num(el.in, 0), tout = num(el.out, 0), req = num(el.req, 0), days = Math.min(31, Math.max(1, num(el.days, 30)));
    var cache = (+el.cache.value) / 100, batch = el.batch.checked ? 0.5 : 1;
    el.cacheOut.textContent = el.cache.value + "%";
    var rows = D.models.filter(function (m) {
      if (m.i == null || m.o == null) return false;
      if (!el.legacy.checked && m.st === "legacy" && pinned.indexOf(m.s) === -1) return false;
      if (weightsFilter && m.w !== weightsFilter) return false;
      return true;
    }).map(function (m) {
      var cin = m.ci != null ? m.ci : m.i;
      var per = (tin * (1 - cache) * m.i + tin * cache * cin + tout * m.o) / 1e6 * batch;
      return { m: m, per: per, month: per * req * days };
    }).sort(function (a, b) { return a.month - b.month; });
    return { rows: rows, tin: tin, tout: tout, req: req, days: days };
  }
  function bar(r, max) {
    var w = max > 0 ? Math.max(1.5, Math.sqrt(r.month / max) * 100) : 0;
    return '<li><span class="b-name"><a href="' + r.m.u + '">' + L.esc(r.m.n) + '</a> <span class="muted" style="font-weight:400">' + L.esc(r.m.pn) + "</span></span>" +
      '<span class="b-track"><span class="b-fill" style="width:' + w.toFixed(1) + '%;background:' + (r.m.w === "open" ? "var(--v6)" : "var(--v3)") + '"></span></span>' +
      '<span class="b-val" title="' + L.price(r.m.i) + " in / " + L.price(r.m.o) + ' out per 1M">' + L.money(r.month) + "</span></li>";
  }
  function render() {
    var c = compute(), rows = c.rows;
    if (!rows.length) { el.bars.innerHTML = '<li class="empty">No priced models match these filters.</li>'; el.summary.innerHTML = ""; return; }
    var max = rows[rows.length - 1].month;
    var med = rows[Math.floor(rows.length / 2)];
    var monthTokens = (c.tin + c.tout) * c.req * c.days;
    el.summary.innerHTML =
      '<div><div class="k">Cheapest</div><div class="v">' + L.money(rows[0].month) + '</div><div class="k">' + L.esc(rows[0].m.n) + "</div></div>" +
      '<div><div class="k">Median model</div><div class="v">' + L.money(med.month) + '</div><div class="k">' + L.esc(med.m.n) + "</div></div>" +
      '<div><div class="k">Most expensive</div><div class="v">' + L.money(rows[rows.length - 1].month) + '</div><div class="k">' + L.esc(rows[rows.length - 1].m.n) + "</div></div>" +
      '<div><div class="k">Tokens per month</div><div class="v">' + L.tokens(Math.round(monthTokens)) + '</div><div class="k">' + L.num(c.req * c.days) + " requests</div></div>";
    var shown = showAll ? rows : rows.slice(0, 20);
    el.bars.innerHTML = shown.map(function (r) { return bar(r, max); }).join("");
    $("cc-all").textContent = showAll ? "Show the cheapest 20" : "Show all " + rows.length + " models";
    $("cc-all").hidden = rows.length <= 20;
    var pins = rows.filter(function (r) { return pinned.indexOf(r.m.s) > -1; });
    el.pinnedH.hidden = !pins.length;
    el.pinned.innerHTML = pins.map(function (r) { return bar(r, max); }).join("");
    var spend = pins.length ? pins[0].month : med.month;
    var band = spend < 500 ? "under-500" : spend < 5000 ? "500-5000" : spend < 50000 ? "5000-50000" : "50000-plus";
    el.cta.innerHTML = (spend >= 1000 ? "<strong>That's a real line item.</strong> " : "<strong>Planning to scale this?</strong> ") +
      'Routing, prompt caching and a smaller model for routine requests can cut a bill like this substantially. <a href="hire-llm-experts.html?need=cut-costs&amp;spend=' + band +
      (pins.length ? "&amp;model=" + pins[0].m.s : "") + '&amp;from=cost-calculator">Get a free cost review</a>.';
    writeUrl();
  }
  function writeUrl() {
    var p = new URLSearchParams();
    p.set("in", el.in.value); p.set("out", el.out.value); p.set("req", el.req.value); p.set("days", el.days.value);
    if (+el.cache.value) p.set("cache", el.cache.value);
    if (el.batch.checked) p.set("batch", "1");
    if (weightsFilter) p.set("w", weightsFilter);
    if (pinned.length) p.set("models", pinned.join(","));
    history.replaceState(null, "", window.location.pathname + "?" + p.toString());
  }
  /* restore */
  if (L.params.get("preset")) setPreset(L.params.get("preset"));
  ["in", "out", "req", "days", "cache"].forEach(function (k) { if (L.params.get(k) != null) el[k].value = L.params.get(k); });
  if (L.params.get("batch")) el.batch.checked = true;
  if (L.params.get("w")) weightsFilter = L.params.get("w");
  Array.prototype.forEach.call(document.querySelectorAll("#cc-weights button"), function (b) {
    b.setAttribute("aria-pressed", b.getAttribute("data-w") === weightsFilter ? "true" : "false");
    b.addEventListener("click", function () {
      weightsFilter = b.getAttribute("data-w");
      Array.prototype.forEach.call(document.querySelectorAll("#cc-weights button"), function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      render();
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll("#cc-presets button"), function (b) {
    b.addEventListener("click", function () { setPreset(b.getAttribute("data-preset")); render(); });
  });
  [el.in, el.out, el.req, el.days, el.cache].forEach(function (x) {
    x.addEventListener("input", function () {
      if (x !== el.cache) Array.prototype.forEach.call(document.querySelectorAll("#cc-presets button"), function (b) { b.setAttribute("aria-pressed", "false"); });
      render();
    });
  });
  [el.batch, el.legacy].forEach(function (x) { x.addEventListener("change", render); });
  $("cc-all").addEventListener("click", function () { showAll = !showAll; render(); });
  $("cc-link").addEventListener("click", function () { L.copy(window.location.href, "Link copied"); });
  $("cc-csv").addEventListener("click", function () {
    var c = compute();
    var lines = [["model", "provider", "input_per_1m_usd", "output_per_1m_usd", "cost_per_request_usd", "monthly_cost_usd"].join(",")];
    c.rows.forEach(function (r) { lines.push(['"' + r.m.n + '"', '"' + r.m.pn + '"', r.m.i, r.m.o, r.per.toFixed(6), r.month.toFixed(2)].join(",")); });
    var blob = new Blob([lines.join("\n")], { type: "text/csv" });
    var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "llm-costs-llmodel.csv";
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  });
  render();
})();
