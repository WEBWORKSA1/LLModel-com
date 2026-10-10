/* Token counter: heuristic estimate, exact o200k count on demand, per-model input cost. */
(function () {
  "use strict";
  var D = window.LLM_DATA, L = window.LLM;
  if (!D || !L) return;
  var text = document.getElementById("tc-text"), stats = document.getElementById("tc-stats"), view = document.getElementById("tc-view");
  var tbody = document.querySelector("#tc-table tbody"), status = document.getElementById("tc-status"), exactBtn = document.getElementById("tc-exact");
  var TOKENIZER = "https://cdn.jsdelivr.net/npm/gpt-tokenizer@4.0.0/esm/encoding/o200k_base.js";
  var enc = null, loading = false, exactCount = null, timer = null;
  var PICKS = ["gpt-6-astra", "gpt-6-1-sol", "gpt-6-luna", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "gemini-3-1-pro",
    "gemini-3-8-flash", "grok-4-7", "deepseek-v4-pro", "qwen3-8-max", "mistral-large-4", "kimi-k3", "gpt-oss-120b"];
  var models = PICKS.map(function (s) { return D.models.filter(function (m) { return m.s === s; })[0]; }).filter(function (m) { return m && m.i != null; });

  function estimate(t) {
    var cjk = (t.match(/[぀-ヿ㐀-䶿一-鿿가-힯]/g) || []).length;
    var other = (t.match(/[^\x00-\x7f]/g) || []).length - cjk;
    var ascii = t.length - cjk - Math.max(0, other);
    var symbols = (t.match(/[{}\[\]()<>;=_\/\\|`~^$#@*+-]/g) || []).length;
    var codeish = ascii > 0 && symbols / ascii > 0.06;
    return Math.round(ascii / (codeish ? 3.3 : 4) + cjk * 1.0 + Math.max(0, other) / 2);
  }
  function render() {
    var t = text.value;
    var chars = t.length, words = (t.trim().match(/\S+/g) || []).length, lines = t ? t.split(/\n/).length : 0;
    var est = estimate(t);
    var tokens = exactCount != null ? exactCount : est;
    stats.innerHTML =
      '<div><div class="k">Characters</div><div class="v">' + L.num(chars) + "</div></div>" +
      '<div><div class="k">Words</div><div class="v">' + L.num(words) + "</div></div>" +
      '<div><div class="k">Estimated tokens</div><div class="v">' + L.num(est) + '</div><div class="k">about 4 characters each</div></div>' +
      '<div><div class="k">Exact (OpenAI o200k)</div><div class="v">' + (exactCount != null ? L.num(exactCount) : "—") + '</div><div class="k">' +
      (exactCount != null && words ? (exactCount / words).toFixed(2) + " tokens per word" : "run the exact count") + "</div></div>";
    tbody.innerHTML = models.map(function (m) {
      var once = tokens * m.i / 1e6;
      var share = m.c ? tokens / m.c * 100 : null;
      return '<tr><td class="m-name"><a href="' + m.u + '">' + L.esc(m.n) + '</a><span class="m-sub">' + L.esc(m.pn) + ", " + L.price(m.i) + " per 1M input</span></td>" +
        '<td class="num">' + (once < 0.0001 ? "<$0.0001" : "$" + once.toFixed(once < 0.01 ? 5 : 4)) + '</td><td class="num">' + L.money(once * 1000) + "</td>" +
        '<td class="num">' + (share == null ? "—" : (share < 0.01 ? "<0.01" : share.toFixed(share < 1 ? 2 : 1)) + "%") + "</td></tr>";
    }).join("");
  }
  function exact() {
    if (!enc) return;
    var ids = enc.encode(text.value);
    exactCount = ids.length;
    var max = 3000, html = "";
    for (var i = 0; i < Math.min(ids.length, max); i++) {
      html += "<span>" + L.esc(enc.decode([ids[i]])).replace(/\n/g, "↵\n") + "</span>";
    }
    if (ids.length > max) html += '<em class="muted"> … ' + L.num(ids.length - max) + " more tokens not shown</em>";
    view.innerHTML = html || "<span>Type or paste some text.</span>";
    render();
  }
  exactBtn.addEventListener("click", function () {
    if (enc) { exact(); return; }
    if (loading) return;
    loading = true; status.textContent = "Loading the tokenizer…"; exactBtn.disabled = true;
    import(TOKENIZER).then(function (mod) {
      enc = mod; status.textContent = "Exact counts update as you type."; exactBtn.textContent = "Exact counting is on"; exact();
      L.track("tokenizer_loaded", {});
    }).catch(function () {
      status.textContent = "Couldn't load the tokenizer (offline or blocked). The estimate still works.";
      exactBtn.disabled = false; loading = false;
    });
  });
  text.addEventListener("input", function () {
    if (!enc) exactCount = null;
    clearTimeout(timer);
    timer = setTimeout(function () { if (enc) exact(); else render(); }, enc ? 180 : 60);
  });
  if (L.params.get("from") === "builder") {
    var saved = L.store.get("llm-prompt", window.sessionStorage);
    if (saved) text.value = saved;
  }
  document.getElementById("tc-clear").addEventListener("click", function () { text.value = ""; exactCount = enc ? 0 : null; view.innerHTML = "<span>Type or paste some text.</span>"; render(); text.focus(); });
  render();
})();
