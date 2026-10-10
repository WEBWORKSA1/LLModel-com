/* Model directory: filter, sort and select rows for comparison. State lives in the URL. */
(function () {
  "use strict";
  var table = document.getElementById("dir-table");
  if (!table) return;
  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.rows);
  var q = document.getElementById("dir-q");
  var provider = document.getElementById("dir-provider");
  var count = document.getElementById("dir-count");
  var chips = Array.prototype.slice.call(document.querySelectorAll("#dir-filters .chip-toggle"));
  var bar = document.getElementById("cmp-bar"), barText = document.getElementById("cmp-text"), barGo = document.getElementById("cmp-go");
  var sortKey = null, sortDir = 1;
  var params = new URLSearchParams(window.location.search);

  function active(group) {
    return chips.filter(function (c) { return c.getAttribute("data-filter") === group && c.getAttribute("aria-pressed") === "true"; })
      .map(function (c) { return c.getAttribute("data-value"); });
  }
  function apply() {
    var term = (q.value || "").toLowerCase().trim(), words = term ? term.split(/\s+/) : [];
    var prov = provider.value;
    var f = { weights: active("weights"), tier: active("tier"), status: active("status"), mods: active("mods"), reasoning: active("reasoning"), ctx: active("ctx") };
    var shown = 0;
    rows.forEach(function (r) {
      var d = r.dataset, ok = true;
      if (prov && d.provider !== prov) ok = false;
      if (ok && f.weights.length && f.weights.indexOf(d.weights) === -1) ok = false;
      if (ok && f.tier.length && f.tier.indexOf(d.tier) === -1) ok = false;
      if (ok && f.status.length && f.status.indexOf(d.status) === -1) ok = false;
      if (ok && f.mods.length) { var ms = d.mods.split(" "); ok = f.mods.every(function (m) { return ms.indexOf(m) > -1; }); }
      if (ok && f.reasoning.length && d.reasoning !== "1") ok = false;
      if (ok && f.ctx.length && +d.ctx < +f.ctx[0]) ok = false;
      if (ok && words.length) {
        var hay = (d.name + " " + d.provider + " " + d.tags + " " + d.tier + " " + d.weights).toLowerCase();
        ok = words.every(function (w) { return hay.indexOf(w) > -1; });
      }
      r.hidden = !ok;
      if (ok) shown++;
    });
    count.textContent = shown + (shown === 1 ? " model" : " models");
    writeUrl(f, term, prov);
  }
  function writeUrl(f, term, prov) {
    var p = new URLSearchParams();
    if (term) p.set("q", term);
    if (prov) p.set("provider", prov);
    Object.keys(f).forEach(function (k) { if (f[k].length) p.set(k, f[k].join(",")); });
    if (sortKey) p.set("sort", (sortDir < 0 ? "-" : "") + sortKey);
    var s = p.toString();
    history.replaceState(null, "", window.location.pathname + (s ? "?" + s : ""));
  }
  function sortBy(key, dir) {
    sortKey = key; sortDir = dir;
    var numeric = key !== "name" && key !== "released";
    rows.sort(function (a, b) {
      var x = a.dataset[key], y = b.dataset[key];
      if (numeric) {
        x = x === "" ? Infinity * dir : +x; y = y === "" ? Infinity * dir : +y;
        return (x - y) * dir || a.dataset.name.localeCompare(b.dataset.name);
      }
      return x.localeCompare(y) * dir;
    });
    rows.forEach(function (r) { tbody.appendChild(r); });
    Array.prototype.forEach.call(table.tHead.querySelectorAll("th[aria-sort]"), function (th) {
      var b = th.querySelector("button.sort");
      th.setAttribute("aria-sort", b && b.getAttribute("data-sort") === key ? (dir > 0 ? "ascending" : "descending") : "none");
    });
  }
  Array.prototype.forEach.call(table.querySelectorAll("button.sort"), function (b) {
    b.addEventListener("click", function () {
      var k = b.getAttribute("data-sort");
      var dir = sortKey === k ? -sortDir : (k === "released" || k === "ctx" ? -1 : 1);
      sortBy(k, dir); apply();
    });
  });
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      c.setAttribute("aria-pressed", c.getAttribute("aria-pressed") === "true" ? "false" : "true");
      apply();
    });
  });
  q.addEventListener("input", apply);
  provider.addEventListener("change", apply);
  document.getElementById("dir-reset").addEventListener("click", function () {
    q.value = ""; provider.value = "";
    chips.forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
    apply();
  });

  /* compare selection */
  var checks = Array.prototype.slice.call(table.querySelectorAll(".cmp-check"));
  function updateBar() {
    var sel = checks.filter(function (c) { return c.checked; }).map(function (c) { return c.value; });
    bar.hidden = sel.length === 0;
    barText.textContent = sel.length + " of 4 selected" + (sel.length < 2 ? ": pick at least two" : "");
    barGo.href = "compare.html?models=" + sel.join(",");
    barGo.setAttribute("aria-disabled", sel.length < 2 ? "true" : "false");
    checks.forEach(function (c) { c.disabled = !c.checked && sel.length >= 4; });
  }
  checks.forEach(function (c) { c.addEventListener("change", updateBar); });
  barGo.addEventListener("click", function (e) { if (barGo.getAttribute("aria-disabled") === "true") e.preventDefault(); });
  document.getElementById("cmp-clear").addEventListener("click", function () { checks.forEach(function (c) { c.checked = false; }); updateBar(); });

  /* restore state from the URL */
  if (params.get("q")) q.value = params.get("q");
  if (params.get("provider")) provider.value = params.get("provider");
  ["weights", "tier", "status", "mods", "reasoning", "ctx"].forEach(function (g) {
    var v = params.get(g);
    if (!v) return;
    v.split(",").forEach(function (val) {
      chips.forEach(function (c) { if (c.getAttribute("data-filter") === g && c.getAttribute("data-value") === val) c.setAttribute("aria-pressed", "true"); });
    });
  });
  var s = params.get("sort");
  if (s) sortBy(s.replace(/^-/, ""), s.charAt(0) === "-" ? -1 : 1);
  apply();
})();
