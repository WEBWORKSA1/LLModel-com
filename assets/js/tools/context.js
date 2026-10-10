/* Context window visualizer. */
(function () {
  "use strict";
  var D = window.LLM_DATA, L = window.LLM;
  if (!D || !L) return;
  var $ = function (id) { return document.getElementById(id); };
  var tokensEl = $("cw-tokens"), modelEl = $("cw-model"), ratioEl = $("cw-ratio");
  var REFS = [
    ["A printed page", 500], ["A long email", 1000], ["A 20-page report", 10000], ["Harry Potter and the Philosopher's Stone", 77000],
    ["War and Peace (English)", 587000], ["Complete works of Shakespeare", 884000]
  ];
  var cur = D.models.filter(function (m) { return m.st !== "legacy" && m.c; });
  cur.sort(function (a, b) { return a.n.localeCompare(b.n); }).forEach(function (m) {
    var o = document.createElement("option"); o.value = m.s; o.textContent = m.n + " (" + L.tokens(m.c) + ")"; modelEl.appendChild(o);
  });
  var flagships = ["gpt-6-astra", "claude-opus-5-5", "gemini-3-1-pro", "grok-4-7", "deepseek-v4-pro", "qwen3-8-max", "mistral-large-4",
    "llama-4-scout", "gpt-oss-120b", "gemma-4-31b", "phi-4-reasoning-vision-15b", "olmo-3-1-32b-think"];
  var flag = flagships.map(function (s) { return D.models.filter(function (m) { return m.s === s; })[0]; }).filter(Boolean);

  function render() {
    var t = Math.max(1, parseInt(tokensEl.value, 10) || 1), r = parseFloat(ratioEl.value);
    $("cw-ratio-out").textContent = r.toFixed(2);
    var words = t * r;
    $("cw-words").textContent = L.num(Math.round(words / (words > 10000 ? 1000 : 10)) * (words > 10000 ? 1000 : 10)) + " words";
    var cells = [
      ["Pages", words / 500, "at 500 words a page"], ["Novels", words / 90000, "at 90,000 words each"],
      ["Meeting hours", words / 9000, "of transcript at 150 words a minute"], ["Lines of code", t / 10, "at about 10 tokens a line"]
    ];
    $("cw-grid").innerHTML = cells.map(function (c) {
      var v = c[1] >= 100 ? L.num(Math.round(c[1])) : c[1] >= 10 ? c[1].toFixed(0) : c[1].toFixed(1);
      return '<div><div class="k">' + c[0] + '</div><div class="v">' + v + '</div><div class="k">' + c[2] + "</div></div>";
    }).join("");
    var maxW = Math.max(words, REFS[REFS.length - 1][1]);
    $("cw-refs").innerHTML = [["Your context", words, true]].concat(REFS).map(function (x) {
      var fits = x[2] ? "" : (words >= x[1] ? Math.floor(words / x[1]) + "× fits" : Math.round(words / x[1] * 100) + "% fits");
      return '<li><span class="b-name"' + (x[2] ? ' style="color:var(--link)"' : "") + ">" + L.esc(x[0]) + '</span><span class="b-track"><span class="b-fill" style="width:' +
        Math.max(0.8, x[1] / maxW * 100).toFixed(1) + "%;background:" + (x[2] ? "var(--v9)" : "var(--v3)") + '"></span></span><span class="b-val">' +
        (x[2] ? L.num(Math.round(x[1])) + " w" : fits) + "</span></li>";
    }).join("");
    var lmin = Math.log10(4096), lmax = Math.log10(Math.max(t, 12e6));
    var pos = function (v) { return Math.max(0.5, (Math.log10(v) - lmin) / (lmax - lmin) * 100); };
    $("cw-models").innerHTML = flag.map(function (m) {
      return '<li><span class="b-name"><a href="' + m.u + '">' + L.esc(m.n) + '</a></span><span class="b-track" style="position:relative"><span class="b-fill" style="width:' +
        pos(m.c).toFixed(1) + "%;background:" + (m.c >= t ? "var(--v5)" : "var(--rule-2)") + '"></span><span aria-hidden="true" style="position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--ink);left:' +
        pos(t).toFixed(1) + '%"></span></span><span class="b-val">' + L.tokens(m.c) + "</span></li>";
    }).join("");
    Array.prototype.forEach.call(document.querySelectorAll("#cw-sizes button"), function (b) { b.setAttribute("aria-pressed", +b.getAttribute("data-t") === t ? "true" : "false"); });
    history.replaceState(null, "", window.location.pathname + "?tokens=" + t);
  }
  Array.prototype.forEach.call(document.querySelectorAll("#cw-sizes button"), function (b) {
    b.addEventListener("click", function () { tokensEl.value = b.getAttribute("data-t"); modelEl.value = ""; render(); });
  });
  modelEl.addEventListener("change", function () {
    var m = D.models.filter(function (x) { return x.s === modelEl.value; })[0];
    if (m) { tokensEl.value = m.c; render(); }
  });
  tokensEl.addEventListener("input", function () { modelEl.value = ""; render(); });
  ratioEl.addEventListener("input", render);
  if (L.params.get("tokens")) tokensEl.value = L.params.get("tokens");
  render();
})();
