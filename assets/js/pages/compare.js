/* Compare tool: up to four models side by side, state in ?models=a,b,c */
(function () {
  "use strict";
  var D = window.LLM_DATA, L = window.LLM;
  if (!D || !L) return;
  var wrap = document.getElementById("cmp-selects"), out = document.getElementById("cmp-out");
  var full = document.getElementById("cmp-full"), calc = document.getElementById("cmp-calc");
  var by = {}; D.models.forEach(function (m) { by[m.s] = m; });
  var MOD = { text: "Text", image: "Images", audio: "Audio", video: "Video", pdf: "PDF" };
  var TIER = { frontier: "Frontier", advanced: "Advanced", efficient: "Efficient", compact: "Compact" };
  var STATUS = { current: "Current", preview: "Preview", legacy: "Legacy" };
  var SCEN = [
    ["Support chatbot", "30,000 conversations, 2,000 in + 400 out", 30000, 2000, 400],
    ["Document summaries", "2,000 documents, 12,000 in + 800 out", 2000, 12000, 800],
    ["Coding agent", "1,000 tasks, 60,000 in + 6,000 out", 1000, 60000, 6000]
  ];
  var groups = {};
  D.models.slice().sort(function (a, b) { return a.n.localeCompare(b.n); }).forEach(function (m) {
    (groups[m.pn] = groups[m.pn] || []).push(m);
  });
  var provNames = Object.keys(groups).sort();
  var selects = [];
  for (var i = 0; i < 4; i++) {
    var lab = document.createElement("div");
    lab.className = "field";
    var id = "cmp-s" + i;
    var html = '<label for="' + id + '">Model ' + (i + 1) + (i > 1 ? ' <span class="muted">(optional)</span>' : "") + '</label><select class="select" id="' + id + '"><option value="">' + (i > 1 ? "None" : "Choose a model") + "</option>";
    provNames.forEach(function (p) {
      html += '<optgroup label="' + L.esc(p) + '">' + groups[p].map(function (m) { return '<option value="' + m.s + '">' + L.esc(m.n) + (m.st === "legacy" ? " (legacy)" : "") + "</option>"; }).join("") + "</optgroup>";
    });
    lab.innerHTML = html + "</select>";
    wrap.appendChild(lab);
    selects.push(lab.querySelector("select"));
  }
  var init = (L.params.get("models") || "").split(",").filter(function (s) { return by[s]; }).slice(0, 4);
  if (init.length < 2) init = ["claude-opus-5-5", "gpt-6-astra", "gemini-3-1-pro"].filter(function (s) { return by[s]; });
  init.forEach(function (s, i) { selects[i].value = s; });

  function blended(m) { return m.i == null || m.o == null ? null : (3 * m.i + m.o) / 4; }
  function cost(m, n, tin, tout) { return m.i == null || m.o == null ? null : n * (tin * m.i + tout * m.o) / 1e6; }
  function best(ms, f, lower) {
    var vals = ms.map(f).filter(function (v) { return v != null; });
    if (vals.length < 2) return null;
    var b = lower ? Math.min.apply(null, vals) : Math.max.apply(null, vals);
    if (vals.every(function (v) { return v === b; })) return null;
    return b;
  }
  function numRow(label, ms, f, fmt, lower) {
    var b = best(ms, f, lower);
    return "<tr><th scope=\"row\">" + label + "</th>" + ms.map(function (m) {
      var v = f(m);
      return '<td class="num' + (b != null && v === b ? " best" : "") + '">' + (v == null ? "—" : fmt(v)) + "</td>";
    }).join("") + "</tr>";
  }
  function txtRow(label, ms, f) {
    return "<tr><th scope=\"row\">" + label + "</th>" + ms.map(function (m) { return "<td>" + f(m) + "</td>"; }).join("") + "</tr>";
  }
  function params(m) {
    if (!m.pt) return "Undisclosed";
    var b = function (x) { return x >= 1000 ? (x / 1000).toFixed(2).replace(/0+$/, "").replace(/\.$/, "") + "T" : x + "B"; };
    return m.pa && m.pa !== m.pt ? b(m.pt) + " total, " + b(m.pa) + " active" : b(m.pt);
  }
  function render() {
    var sel = selects.map(function (s) { return s.value; }).filter(Boolean);
    sel = sel.filter(function (s, i) { return sel.indexOf(s) === i; });
    history.replaceState(null, "", window.location.pathname + (sel.length ? "?models=" + sel.join(",") : ""));
    calc.href = "llm-cost-calculator.html" + (sel.length ? "?models=" + sel.join(",") : "");
    var pre = null;
    if (sel.length === 2) {
      D.comparisons.forEach(function (c) { if ((c[0] === sel[0] && c[1] === sel[1]) || (c[0] === sel[1] && c[1] === sel[0])) pre = c[2]; });
    }
    full.hidden = !pre; if (pre) full.href = pre + ".html";
    if (sel.length < 2) { out.innerHTML = '<p class="empty">Pick at least two models to compare.</p>'; return; }
    var ms = sel.map(function (s) { return by[s]; });
    var head = "<thead><tr><th></th>" + ms.map(function (m) { return '<th><a href="' + m.u + '">' + L.esc(m.n) + "</a></th>"; }).join("") + "</tr></thead>";
    var body = [
      txtRow("Provider", ms, function (m) { return L.esc(m.pn); }),
      txtRow("Released", ms, function (m) { return L.date(m.r); }),
      txtRow("Status", ms, function (m) { return '<span class="badge badge--' + m.st + '">' + STATUS[m.st] + "</span>"; }),
      txtRow("Weights", ms, function (m) { return (m.w === "open" ? '<span class="badge badge--open">Open</span>' : '<span class="badge badge--closed">Closed</span>') + ' <span class="small muted">' + L.esc(m.l || "") + "</span>"; }),
      txtRow("Tier", ms, function (m) { return TIER[m.t]; }),
      numRow("Context window", ms, function (m) { return m.c; }, L.tokens, false),
      numRow("Max output", ms, function (m) { return m.mo; }, L.tokens, false),
      numRow("Input per 1M tokens", ms, function (m) { return m.i; }, L.price, true),
      numRow("Output per 1M tokens", ms, function (m) { return m.o; }, L.price, true),
      numRow("Cached input per 1M", ms, function (m) { return m.ci; }, L.price, true),
      numRow("Blended price (3:1)", ms, blended, L.price, true),
      txtRow("Inputs", ms, function (m) { return m.mi.map(function (x) { return MOD[x] || x; }).join(", "); }),
      txtRow("Reasoning mode", ms, function (m) { return m.rs ? "Yes" : "No"; }),
      txtRow("Tool calling", ms, function (m) { return m.tu ? "Yes" : "Not documented"; }),
      txtRow("Parameters", ms, params),
      txtRow("Positioned for", ms, function (m) { return '<span class="small">' + L.esc(m.bf.join(", ")) + "</span>"; })
    ].join("");
    var scen = SCEN.map(function (s) {
      return numRow(s[0] + '<span class="m-sub">' + s[1] + "</span>", ms, function (m) { return cost(m, s[2], s[3], s[4]); }, L.money, true);
    }).join("");
    out.innerHTML = '<div class="table-wrap"><table class="table cmp">' + head + "<tbody>" + body +
      '<tr><th colspan="' + (ms.length + 1) + '" style="background:var(--surface-2)">Monthly cost at list price</th></tr>' + scen + "</tbody></table></div>" +
      '<p class="small muted" style="margin-top:.6rem">Highlighted: lowest price or highest limit in the row. List prices, standard tier, checked ' + L.date(D.updated) + ". Notes on long-prompt surcharges and discounts are on each model page.</p>";
  }
  selects.forEach(function (s) { s.addEventListener("change", render); });
  document.getElementById("cmp-share").addEventListener("click", function () { L.copy(window.location.href, "Link copied"); });
  render();
})();
