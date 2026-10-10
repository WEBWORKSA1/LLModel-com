/* Self-host vs API break-even calculator with an SVG chart. */
(function () {
  "use strict";
  var D = window.LLM_DATA, L = window.LLM;
  var form = document.getElementById("be-form");
  if (!D || !L || !form) return;
  var $ = function (id) { return document.getElementById(id); };
  var HOURS = 730, PREFILL = 0.1;
  var priced = D.models.filter(function (m) { return m.i != null && m.o != null && m.st !== "legacy"; })
    .sort(function (a, b) { return a.n.localeCompare(b.n); });
  $("be-model").innerHTML = '<option value="">Custom prices</option>' + priced.map(function (m) {
    return '<option value="' + m.s + '">' + L.esc(m.n) + " (" + L.price(m.i) + " / " + L.price(m.o) + ")</option>";
  }).join("");
  function setModel(s) {
    var m = priced.filter(function (x) { return x.s === s; })[0];
    if (m) { $("be-pin").value = m.i; $("be-pout").value = m.o; }
  }
  var start = L.params.get("model") && priced.some(function (m) { return m.s === L.params.get("model"); }) ? L.params.get("model") : "gpt-6-1-sol";
  if (!priced.some(function (m) { return m.s === start; })) start = priced[0].s;
  $("be-model").value = start; setModel(start);

  function n(id) { var v = parseFloat($(id).value); return isNaN(v) || v < 0 ? 0 : v; }
  function calc(scale) {
    var inT = n("be-in") * 1e6 * scale, outT = n("be-out") * 1e6 * scale;
    var api = inT / 1e6 * n("be-pin") + outT / 1e6 * n("be-pout");
    var cap = Math.max(1, n("be-tps")) * 3600 * HOURS * (n("be-util") / 100);
    var need = outT + PREFILL * inT;
    var replicas = Math.max(1, Math.ceil(need / cap));
    var self = replicas * Math.max(1, Math.round(n("be-gpus"))) * n("be-gpu") * HOURS + n("be-ops");
    return { api: api, self: self, replicas: replicas, cap: cap, need: need };
  }
  function breakEven() {
    var lo = 0.001, hi = 1000, f = function (s) { var c = calc(s); return c.api - c.self; };
    if (f(hi) < 0) return null;
    if (f(lo) > 0) return lo;
    for (var i = 0; i < 60; i++) { var mid = Math.sqrt(lo * hi); if (f(mid) > 0) hi = mid; else lo = mid; }
    return hi;
  }
  function chart() {
    var W = 640, H = 260, pad = { l: 56, r: 14, t: 12, b: 34 };
    var xs = [], i;
    for (i = 0; i <= 120; i++) xs.push(Math.pow(10, -2 + i * 4 / 120));
    var pts = xs.map(function (s) { var c = calc(s); return [s, c.api, c.self]; });
    var maxY = Math.max.apply(null, pts.map(function (p) { return Math.min(Math.max(p[1], p[2]), calc(1).self * 6 + calc(1).api * 1.2); }));
    var X = function (s) { return pad.l + (Math.log10(s) + 2) / 4 * (W - pad.l - pad.r); };
    var Y = function (v) { return H - pad.b - Math.min(v, maxY) / maxY * (H - pad.t - pad.b); };
    var line = function (k, color) {
      return '<path fill="none" stroke="' + color + '" stroke-width="2.5" d="' + pts.map(function (p, j) { return (j ? "L" : "M") + X(p[0]).toFixed(1) + "," + Y(p[k]).toFixed(1); }).join("") + '"/>';
    };
    var ticks = [0.01, 0.1, 1, 10, 100].map(function (s) {
      return '<line class="axis" x1="' + X(s) + '" x2="' + X(s) + '" y1="' + pad.t + '" y2="' + (H - pad.b) + '" stroke-dasharray="2 4"/>' +
        '<text x="' + X(s) + '" y="' + (H - 12) + '" text-anchor="middle">' + (s < 1 ? s + "×" : s + "×") + "</text>";
    }).join("");
    var yt = [0, 0.5, 1].map(function (f) {
      return '<text x="' + (pad.l - 8) + '" y="' + (Y(maxY * f) + 4) + '" text-anchor="end">' + L.money(maxY * f) + "</text>";
    }).join("");
    var be = breakEven(), beMark = "";
    if (be && be > 0.01 && be < 100) {
      beMark = '<circle cx="' + X(be) + '" cy="' + Y(calc(be).api) + '" r="5" fill="var(--v9)" stroke="var(--ink)" stroke-width="1.5"/>';
    }
    $("be-chart").innerHTML = '<svg viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="xMidYMid meet">' + ticks + yt +
      '<line class="axis" x1="' + pad.l + '" x2="' + (W - pad.r) + '" y1="' + (H - pad.b) + '" y2="' + (H - pad.b) + '"/>' +
      line(1, "var(--v3)") + line(2, "var(--v6)") +
      '<line x1="' + X(1) + '" x2="' + X(1) + '" y1="' + pad.t + '" y2="' + (H - pad.b) + '" stroke="var(--ink)" stroke-width="1.5"/>' + beMark +
      '<text x="' + (W - pad.r) + '" y="' + (H - 1) + '" text-anchor="end">Monthly volume, multiple of yours (log scale)</text></svg>';
    return be;
  }
  function render() {
    $("be-util-out").textContent = $("be-util").value + "%";
    var c = calc(1), be = chart();
    var diff = c.api - c.self;
    $("be-verdict").textContent = diff > 0 ? "Self-hosting saves " + L.money(diff) + "/mo" : "The API is cheaper by " + L.money(-diff) + "/mo";
    var beText = be == null ? "Not within 1,000× your volume" : be <= 0.001 ? "Below your volume" : (be < 1 ? "At " + Math.round(be * 100) + "% of your volume" : "At " + (be < 10 ? be.toFixed(1) : Math.round(be)) + "× your volume");
    $("be-grid").innerHTML =
      '<div><div class="k">API bill</div><div class="v">' + L.money(c.api) + '</div><div class="k">per month</div></div>' +
      '<div><div class="k">Self-host bill</div><div class="v">' + L.money(c.self) + '</div><div class="k">' + c.replicas + " replica" + (c.replicas > 1 ? "s" : "") + ", ops included</div></div>" +
      '<div><div class="k">Replica load</div><div class="v">' + Math.round(c.need / (c.cap * c.replicas) * 100) + '%</div><div class="k">of capacity at your utilization</div></div>' +
      '<div><div class="k">Break-even</div><div class="v" style="font-size:var(--fs-18)">' + beText + "</div></div>";
  }
  $("be-model").addEventListener("change", function () { setModel(this.value); render(); });
  ["be-pin", "be-pout"].forEach(function (id) { $(id).addEventListener("input", function () { $("be-model").value = ""; }); });
  form.addEventListener("input", render);
  render();
})();
