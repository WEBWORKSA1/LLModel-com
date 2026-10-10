/* Rankings: the same value index as the server-rendered list, with live weights. */
(function () {
  "use strict";
  var D = window.LLM_DATA, L = window.LLM;
  var list = document.getElementById("rank-list");
  if (!D || !L || !list) return;
  var KEYS = ["capability", "price", "context", "openness", "multimodal", "recency"];
  var PRESETS = {
    balanced: { capability: 40, price: 25, context: 10, openness: 10, multimodal: 5, recency: 10 },
    capability: { capability: 80, price: 0, context: 5, openness: 0, multimodal: 5, recency: 10 },
    value: { capability: 35, price: 50, context: 10, openness: 0, multimodal: 0, recency: 5 },
    selfhost: { capability: 35, price: 15, context: 5, openness: 45, multimodal: 0, recency: 0 },
    longctx: { capability: 30, price: 15, context: 50, openness: 0, multimodal: 0, recency: 5 }
  };
  var TIER = { frontier: 1, advanced: 0.75, efficient: 0.5, compact: 0.3 };
  var TL = { frontier: "Frontier", advanced: "Advanced", efficient: "Efficient", compact: "Compact" };
  var inputs = {}; KEYS.forEach(function (k) { inputs[k] = document.getElementById("w-" + k); });
  var openOnly = document.getElementById("lb-open"), more = document.getElementById("lb-more"), countEl = document.getElementById("lb-count");
  var showAll = false;
  function dnum(d) { var p = (d + "-01-01").split("-"); return (+p[0]) * 372 + (+p[1]) * 31 + (+p[2]); }
  function blended(m) { return (3 * m.i + m.o) / 4; }

  function scores(w) {
    var ms = D.models.filter(function (m) { return m.st !== "legacy" && m.i != null && m.o != null; });
    var lp = ms.map(function (m) { return Math.log(blended(m)); });
    var lc = ms.filter(function (m) { return m.c; }).map(function (m) { return Math.log(m.c); });
    var dn = ms.map(function (m) { return dnum(m.r); });
    var mn = function (a) { return Math.min.apply(null, a); }, mx = function (a) { return Math.max.apply(null, a); };
    var tot = KEYS.reduce(function (a, k) { return a + w[k]; }, 0) || 1;
    var out = ms.map(function (m) {
      var s = {
        capability: TIER[m.t] + (m.rs ? 0.05 : 0),
        price: 1 - (Math.log(blended(m)) - mn(lp)) / ((mx(lp) - mn(lp)) || 1),
        context: m.c ? (Math.log(m.c) - mn(lc)) / ((mx(lc) - mn(lc)) || 1) : 0,
        openness: m.w === "open" ? 1 : 0,
        multimodal: Math.min(1, m.mi.filter(function (x) { return x !== "text"; }).length / 3),
        recency: (dnum(m.r) - mn(dn)) / ((mx(dn) - mn(dn)) || 1)
      };
      var sc = KEYS.reduce(function (a, k) { return a + w[k] * Math.min(1, s[k]); }, 0) / tot * 100;
      return { m: m, sc: sc };
    });
    return out.sort(function (a, b) { return b.sc - a.sc; });
  }
  function weights() { var w = {}; KEYS.forEach(function (k) { w[k] = +inputs[k].value; }); return w; }
  function render() {
    KEYS.forEach(function (k) { inputs[k].nextElementSibling.textContent = inputs[k].value; });
    var res = scores(weights());
    if (openOnly.checked) res = res.filter(function (x) { return x.m.w === "open"; });
    countEl.textContent = res.length + " models scored";
    var shown = showAll ? res : res.slice(0, 25);
    list.innerHTML = shown.map(function (x) {
      var m = x.m;
      return '<li><span class="rk-name"><a href="' + m.u + '">' + L.esc(m.n) + "</a><small>" + L.esc(m.pn) + ", " + TL[m.t] + ", " +
        L.price(m.i) + " / " + L.price(m.o) + '</small></span><span class="b-track" style="height:12px;border-radius:3px;background:var(--surface-2);overflow:hidden"><span class="b-fill" style="display:block;height:100%;width:' +
        x.sc.toFixed(0) + '%;background:var(--v4)"></span></span><span class="rk-score">' + x.sc.toFixed(0) + "</span></li>";
    }).join("");
    more.hidden = res.length <= 25;
    more.textContent = showAll ? "Show top 25" : "Show all " + res.length + " models";
  }
  KEYS.forEach(function (k) {
    inputs[k].addEventListener("input", function () {
      Array.prototype.forEach.call(document.querySelectorAll("#lb-presets button"), function (b) { b.setAttribute("aria-pressed", "false"); });
      render();
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll("#lb-presets button"), function (b) {
    b.addEventListener("click", function () {
      var p = PRESETS[b.getAttribute("data-preset")];
      KEYS.forEach(function (k) { inputs[k].value = p[k]; });
      Array.prototype.forEach.call(document.querySelectorAll("#lb-presets button"), function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      if (b.getAttribute("data-preset") === "selfhost") openOnly.checked = true;
      render();
    });
  });
  openOnly.addEventListener("change", render);
  more.addEventListener("click", function () { showAll = !showAll; render(); });
  render();
})();
