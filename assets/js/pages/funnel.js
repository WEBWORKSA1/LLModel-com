/* Lead funnel: four steps, per-step validation, prefill from tools, lead scoring. */
(function () {
  "use strict";
  var L = window.LLM, form = document.getElementById("funnel");
  if (!L || !form) return;
  var steps = Array.prototype.slice.call(form.querySelectorAll(".funnel-step"));
  var marks = Array.prototype.slice.call(document.querySelectorAll("#fn-steps li"));
  var cur = 0;
  function show(i) {
    cur = Math.max(0, Math.min(steps.length - 1, i));
    steps.forEach(function (s, j) { s.hidden = j !== cur; });
    marks.forEach(function (m, j) {
      m.classList.toggle("is-current", j === cur); m.classList.toggle("is-done", j < cur);
      if (j === cur) m.setAttribute("aria-current", "step"); else m.removeAttribute("aria-current");
    });
    var h = steps[cur].querySelector("h2");
    if (h) { h.tabIndex = -1; h.focus({ preventScroll: true }); }
    var top = document.getElementById("fn-steps").getBoundingClientRect().top + window.scrollY - 90;
    if (window.scrollY > top) window.scrollTo({ top: top, behavior: "smooth" });
    L.track("lead_step", { step: cur + 1 });
  }
  form.addEventListener("click", function (e) {
    if (e.target.closest("[data-next]")) { if (L.validate(steps[cur])) show(cur + 1); }
    else if (e.target.closest("[data-prev]")) show(cur - 1);
  });
  /* choosing a goal moves on automatically */
  Array.prototype.forEach.call(form.querySelectorAll('input[name="need"]'), function (r) {
    r.addEventListener("change", function () { setTimeout(function () { if (cur === 0) show(1); }, 180); });
  });

  /* prefill from links on tools and pages */
  var p = L.params;
  function check(name, val) { var x = form.querySelector('input[name="' + name + '"][value="' + val + '"]'); if (x) x.checked = true; }
  if (p.get("need")) check("need", p.get("need"));
  if (p.get("spend")) check("spend", p.get("spend"));
  if (p.get("deploy")) check("deploy", p.get("deploy") === "self-host" ? "on-prem" : p.get("deploy") === "prefer-open" ? "private-cloud" : p.get("deploy"));
  var models = p.get("models") || p.get("model");
  if (models) {
    var names = models.split(",").map(function (s) { return s.replace(/-/g, " "); });
    form.elements.models.value = names.join(", ");
    form.elements.model.value = models;
  }
  form.elements.source.value = p.get("from") || "direct";
  form.elements.usecase.value = p.get("usecase") || "";
  if (p.get("need")) show(1);

  var SCORE = {
    budget: { "under-5k": 5, "5k-15k": 15, "15k-50k": 25, "50k-150k": 35, "150k-plus": 40, "not-sure": 10 },
    timeline: { asap: 20, "1-3-months": 15, "3-6-months": 8, "6-months-plus": 3 },
    stage: { exploring: 4, prototype: 10, production: 15 },
    team_size: { "1-10": 4, "11-50": 8, "51-250": 12, "251-1000": 14, "1000-plus": 15 },
    spend: { none: 2, "under-500": 4, "500-5000": 7, "5000-50000": 9, "50000-plus": 10 }
  };
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!L.validate(steps[cur])) return;
    var fd = new FormData(form), score = 0;
    Object.keys(SCORE).forEach(function (k) { score += SCORE[k][fd.get(k)] || 0; });
    var tier = score >= 65 ? "A" : score >= 40 ? "B" : "C";
    form.setAttribute("data-subject", "New LLM project lead [" + tier + "] " + (fd.get("need") || ""));
    L.submit(form, { lead_score: String(score), lead_tier: tier }).then(function (ok) {
      if (!ok) return;
      form.hidden = true;
      document.getElementById("fn-steps").hidden = true;
      var done = document.getElementById("fn-done");
      done.hidden = false; done.focus();
      L.track("generate_lead", { form_type: "lead", lead_tier: tier });
    });
  });
})();
