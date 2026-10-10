/* Model picker: hard filters, then a weighted score. */
(function () {
  "use strict";
  var D = window.LLM_DATA, L = window.LLM;
  var form = document.getElementById("pk-form");
  if (!D || !L || !form) return;
  var out = document.getElementById("pk-out"), actions = document.getElementById("pk-actions"), more = document.getElementById("pk-more");
  var USE = {
    general: { tags: ["chat", "agents", "reasoning", "writing"], label: "general assistance" },
    coding: { tags: ["coding", "agents"], label: "coding" },
    support: { tags: ["customer support", "high volume", "low latency", "chat"], label: "customer support" },
    documents: { tags: ["long documents", "research", "data extraction"], label: "questions over documents" },
    agents: { tags: ["agents", "reasoning", "coding"], label: "agents and automation" },
    writing: { tags: ["writing", "chat", "multilingual"], label: "writing" },
    extraction: { tags: ["data extraction", "high volume", "low latency"], label: "data extraction" },
    research: { tags: ["research", "reasoning", "long documents"], label: "research and analysis" }
  };
  var W = {
    quality: { use: 0.3, tier: 0.55, price: 0.1, speed: 0.05 },
    balanced: { use: 0.35, tier: 0.3, price: 0.25, speed: 0.1 },
    cost: { use: 0.3, tier: 0.15, price: 0.5, speed: 0.05 },
    speed: { use: 0.3, tier: 0.1, price: 0.25, speed: 0.35 }
  };
  var TIER = { frontier: 1, advanced: 0.8, efficient: 0.55, compact: 0.35 };
  var SPEED = { frontier: 0.3, advanced: 0.55, efficient: 0.85, compact: 1 };
  var TL = { frontier: "frontier", advanced: "advanced", efficient: "efficient", compact: "compact" };

  function val(name) { var x = form.querySelector('input[name="' + name + '"]:checked'); return x ? x.value : ""; }
  function blended(m) { return m.i == null || m.o == null ? null : (3 * m.i + m.o) / 4; }

  function run() {
    var use = val("use"), prio = val("prio"), deploy = val("deploy"), inputs = val("inputs"), ctx = +val("ctx");
    var tags = USE[use].tags, w = W[prio];
    var pool = D.models.filter(function (m) {
      if (m.st === "legacy") return false;
      if (deploy === "self-host" && m.w !== "open") return false;
      if (inputs === "image" && m.mi.indexOf("image") === -1) return false;
      if (inputs === "av" && m.mi.indexOf("audio") === -1 && m.mi.indexOf("video") === -1) return false;
      if (ctx && (m.c || 0) < ctx) return false;
      return true;
    });
    var priced = pool.map(blended).filter(function (x) { return x != null; }).map(Math.log);
    var lo = Math.min.apply(null, priced), hi = Math.max.apply(null, priced);
    var scored = pool.map(function (m) {
      var hits = tags.filter(function (t) { return m.bf.indexOf(t) > -1; });
      var useS = hits.length ? 0.5 + 0.5 * hits.length / tags.length : 0;
      var b = blended(m);
      var priceS = b == null ? 0.4 : 1 - (Math.log(b) - lo) / ((hi - lo) || 1);
      var speedS = SPEED[m.t] + (m.bf.indexOf("low latency") > -1 ? 0.15 : 0);
      var s = w.use * useS + w.tier * TIER[m.t] + w.price * priceS + w.speed * Math.min(1, speedS);
      if (deploy === "prefer-open" && m.w === "open") s += 0.08;
      if (m.st === "preview") s -= 0.04;
      return { m: m, s: s, hits: hits, b: b };
    }).sort(function (a, b) { return b.s - a.s; });

    if (!scored.length) {
      out.innerHTML = '<p class="empty">No model in our directory meets all five answers. Loosen one requirement, usually context length or audio and video input.</p>';
      actions.innerHTML = ""; more.innerHTML = ""; return;
    }
    var top = scored.slice(0, 3);
    out.innerHTML = '<ol class="rowlist" style="list-style:none">' + top.map(function (x, i) {
      var m = x.m, why = [];
      if (x.hits.length) why.push("its provider positions it for " + x.hits.join(" and "));
      why.push(TL[m.t] + " tier");
      if (x.b != null) why.push(L.price(m.i) + " input and " + L.price(m.o) + " output per million tokens");
      else why.push("no confirmed per-token price; usually self-hosted");
      if (m.c) why.push(L.tokens(m.c) + " context");
      if (m.w === "open") why.push("open weights (" + (m.l || "open license") + ")");
      return '<li style="padding:1rem 0"><p style="font-size:var(--fs-14);color:var(--ink-3)">' + ["Top pick", "Second pick", "Third pick"][i] + "</p>" +
        '<p style="font-weight:700;font-size:var(--fs-21)"><a href="' + m.u + '">' + L.esc(m.n) + '</a> <span class="small muted" style="font-weight:400">' + L.esc(m.pn) + "</span></p>" +
        '<p class="small" style="margin-top:.3rem">Why: ' + L.esc(why.join("; ")) + ".</p></li>";
    }).join("") + "</ol>";
    var ids = top.map(function (x) { return x.m.s; }).join(",");
    actions.innerHTML = '<a class="btn btn--primary btn--sm" href="compare.html?models=' + ids + '">Compare these three</a>' +
      '<a class="btn btn--ghost btn--sm" href="llm-cost-calculator.html?models=' + ids + '">Price them</a>' +
      '<a class="btn btn--ghost btn--sm" href="hire-llm-experts.html?need=choose-model&amp;usecase=' + use + "&amp;deploy=" + deploy + "&amp;models=" + ids + '&amp;from=picker">Get an expert to check this shortlist</a>';
    more.innerHTML = scored.slice(3, 7).map(function (x) {
      return '<li><a href="' + x.m.u + '">' + L.esc(x.m.n) + "</a> (" + L.esc(x.m.pn) + ")</li>";
    }).join("");
    L.track("picker_result", { use: use, prio: prio, deploy: deploy });
  }
  form.addEventListener("change", run);
  ["use", "prio", "deploy", "inputs", "ctx"].forEach(function (k) {
    var v = L.params.get(k);
    if (v) { var x = form.querySelector('input[name="' + k + '"][value="' + v + '"]'); if (x) x.checked = true; }
  });
  run();
})();
