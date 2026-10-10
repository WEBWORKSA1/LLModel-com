/* VRAM calculator: weights + KV cache + overhead, and which hardware fits. */
(function () {
  "use strict";
  var D = window.LLM_DATA, L = window.LLM;
  if (!D || !L) return;
  var $ = function (id) { return document.getElementById(id); };
  var CTX = [2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576];
  var FACTORS = { full: 1, hybrid: 0.25, latent: 0.1, ssm: 0.11 };
  var NOTES = {
    full: "Uses the standard formula with no reduction.",
    hybrid: D.kvNotes.hybrid, latent: D.kvNotes.latent, ssm: D.kvNotes.ssm
  };
  var HW = [
    ["NVIDIA RTX 3060", 12, "gpu"], ["NVIDIA RTX 4060 Ti 16 GB", 16, "gpu"], ["NVIDIA RTX 3090 / 4090", 24, "gpu"], ["NVIDIA RTX 5090", 32, "gpu"],
    ["NVIDIA RTX 6000 Ada", 48, "gpu"], ["NVIDIA RTX PRO 6000 Blackwell", 96, "gpu"], ["NVIDIA L4", 24, "gpu"], ["NVIDIA L40S", 48, "gpu"],
    ["NVIDIA A100 80 GB", 80, "gpu"], ["NVIDIA H100 80 GB", 80, "gpu"], ["NVIDIA H200", 141, "gpu"], ["NVIDIA B200", 180, "gpu"],
    ["AMD Instinct MI300X", 192, "gpu"], ["AMD Instinct MI325X", 256, "gpu"],
    ["Mac with 16 GB unified memory", 16, "mac"], ["Mac with 32 GB", 32, "mac"], ["Mac with 64 GB", 64, "mac"],
    ["Mac with 128 GB", 128, "mac"], ["Mac with 256 GB", 256, "mac"], ["Mac with 512 GB", 512, "mac"]
  ];
  var el = { model: $("vr-model"), params: $("vr-params"), prec: $("vr-prec"), ctx: $("vr-ctx"), ctxOut: $("vr-ctx-out"), batch: $("vr-batch"),
    kvp: $("vr-kvp"), att: $("vr-att"), attNote: $("vr-att-note"), layers: $("vr-layers"), kvh: $("vr-kvh"), hd: $("vr-hd"), kvf: $("vr-kvf"),
    total: $("vr-total"), brk: $("vr-break"), moe: $("vr-moe"), gpus: document.querySelector("#vr-gpus tbody") };
  var open = D.models.filter(function (m) { return m.w === "open" && m.pt; }).sort(function (a, b) { return a.pt - b.pt; });
  var kvFactor = 1, current = null;
  el.model.innerHTML = '<option value="">Custom model</option>' + open.map(function (m) {
    return '<option value="' + m.s + '">' + L.esc(m.n) + " (" + (m.pt >= 1000 ? (m.pt / 1000).toFixed(1) + "T" : m.pt + "B") + ")</option>";
  }).join("");

  function choose(slug) {
    current = open.filter(function (m) { return m.s === slug; })[0] || null;
    if (current) {
      el.params.value = current.pt;
      if (current.a) { el.layers.value = current.a.layers; el.kvh.value = current.a.kv_heads; el.hd.value = current.a.head_dim; }
      el.att.value = current.att || "full";
      kvFactor = current.kvf || 1;
      if (current.c) {
        var maxIdx = 0; CTX.forEach(function (c, i) { if (c <= current.c) maxIdx = i; });
        el.ctx.max = maxIdx; if (+el.ctx.value > maxIdx) el.ctx.value = maxIdx;
      }
    } else {
      el.ctx.max = CTX.length - 1; kvFactor = FACTORS[el.att.value];
    }
  }
  function gb(x) { return x >= 100 ? Math.round(x) + " GB" : x >= 10 ? x.toFixed(1) + " GB" : x.toFixed(2) + " GB"; }
  function render() {
    var P = Math.max(0, parseFloat(el.params.value) || 0), bits = parseFloat(el.prec.value);
    var ctx = CTX[+el.ctx.value], batch = Math.max(1, parseInt(el.batch.value, 10) || 1), kvb = parseFloat(el.kvp.value);
    el.ctxOut.textContent = L.tokens(ctx);
    var weights = P * bits / 8;
    var factor = current && current.att === el.att.value ? kvFactor : FACTORS[el.att.value];
    el.kvf.textContent = factor < 1 ? factor + " of the standard estimate" : "1 (standard)";
    el.attNote.textContent = NOTES[el.att.value] || "";
    var kv = 2 * (+el.layers.value) * (+el.kvh.value) * (+el.hd.value) * ctx * batch * kvb * factor / 1e9;
    var hasArch = !current || !!current.a;
    if (!hasArch) kv = NaN;
    var over = 0.8 + weights * 0.06;
    var total = weights + (isNaN(kv) ? 0 : kv) + over;
    el.total.textContent = gb(total) + (isNaN(kv) ? " + KV cache" : "");
    var max = Math.max(weights, isNaN(kv) ? 0 : kv, over);
    var row = function (name, v, color, note) {
      return '<li><span class="b-name">' + name + '</span><span class="b-track"><span class="b-fill" style="width:' + (isNaN(v) ? 0 : Math.max(1, v / max * 100)).toFixed(1) +
        "%;background:" + color + '"></span></span><span class="b-val">' + (isNaN(v) ? "n/a" : gb(v)) + "</span></li>" + (note ? '<li class="small muted" style="display:block">' + note + "</li>" : "");
    };
    el.brk.innerHTML = row("Weights", weights, "var(--v2)") +
      row("KV cache", kv, "var(--v5)", isNaN(kv) ? "This model's config isn't published in a form we could use. Enter its layers, KV heads and head size to include the cache." : "") +
      row("Runtime overhead", over, "var(--v8)");
    if (current && current.pa && current.pa !== current.pt) {
      el.moe.textContent = "Mixture of experts: all " + current.pt + "B parameters must be in memory, but only about " + current.pa + "B are active per token, so it generates faster than a dense model of this size.";
    } else { el.moe.textContent = ""; }
    el.gpus.innerHTML = HW.map(function (h) {
      var usable = h[2] === "mac" ? h[1] * 0.75 : h[1] * 0.9;
      var n = Math.ceil(total / usable), fits;
      if (h[2] === "mac") fits = total <= usable ? '<span class="badge badge--current">Fits</span>' : '<span class="badge badge--legacy">Too small</span>';
      else if (n <= 1) fits = '<span class="badge badge--current">Fits on one</span>';
      else if (n <= 8) fits = '<span class="badge badge--preview">Needs ' + n + "</span>";
      else fits = '<span class="badge badge--legacy">Needs ' + n + "+</span>";
      return "<tr><td>" + h[0] + '</td><td class="num">' + h[1] + " GB</td><td>" + fits + "</td></tr>";
    }).join("");
    var p = new URLSearchParams();
    if (el.model.value) p.set("model", el.model.value); else p.set("params", el.params.value);
    p.set("bits", el.prec.value); p.set("ctx", CTX[+el.ctx.value]); if (batch > 1) p.set("batch", batch);
    history.replaceState(null, "", window.location.pathname + "?" + p.toString());
  }
  /* restore from URL */
  var startModel = L.params.get("model") || (open.filter(function (m) { return m.s === "gpt-oss-20b"; })[0] || open[0]).s;
  el.model.value = startModel; choose(startModel);
  if (!L.params.get("model") && L.params.get("params")) { el.model.value = ""; choose(""); el.params.value = L.params.get("params"); }
  if (L.params.get("bits")) el.prec.value = L.params.get("bits");
  else el.prec.value = "4.85";
  if (L.params.get("ctx")) { var i = CTX.indexOf(+L.params.get("ctx")); if (i > -1) el.ctx.value = i; }
  if (L.params.get("batch")) el.batch.value = L.params.get("batch");
  el.model.addEventListener("change", function () { choose(el.model.value); render(); });
  el.att.addEventListener("change", function () { if (current && el.att.value !== current.att) { /* user override */ } render(); });
  [el.params, el.prec, el.ctx, el.batch, el.kvp, el.layers, el.kvh, el.hd].forEach(function (x) {
    x.addEventListener("input", function () {
      if (x === el.params && el.model.value) { el.model.value = ""; current = null; }
      render();
    });
  });
  render();
})();
