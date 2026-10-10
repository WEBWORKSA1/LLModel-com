/* Home: the next-token sampler in the hero. Teaches temperature and routes people by intent. */
(function () {
  "use strict";
  var root = document.getElementById("ntp");
  if (!root) return;
  var list = document.getElementById("ntp-cands");
  var temp = document.getElementById("ntp-temp");
  var tempOut = document.getElementById("ntp-temp-out");
  var nextEl = document.getElementById("ntp-next");
  var answer = document.getElementById("ntp-answer");
  var sampleBtn = document.getElementById("ntp-sample");
  var buttons = Array.prototype.slice.call(list.querySelectorAll(".ntp__cand"));
  var base = buttons.map(function (b) { return parseFloat(b.getAttribute("data-p")); });
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var typing = null;

  function probs(t) {
    if (t <= 0.05) {
      var max = Math.max.apply(null, base);
      return base.map(function (p) { return p === max ? 1 : 0; });
    }
    var w = base.map(function (p) { return Math.pow(p, 1 / t); });
    var sum = w.reduce(function (a, b) { return a + b; }, 0);
    return w.map(function (x) { return x / sum; });
  }
  function render() {
    var t = parseFloat(temp.value);
    tempOut.textContent = t.toFixed(1);
    var p = probs(t);
    buttons.forEach(function (b, i) {
      b.querySelector(".ntp__bar").style.width = (p[i] * 100).toFixed(1) + "%";
      b.querySelector(".ntp__p").textContent = p[i].toFixed(2);
      b.setAttribute("aria-label", b.getAttribute("data-token") + ", probability " + p[i].toFixed(2));
    });
    return p;
  }
  function pick(i) {
    var b = buttons[i];
    buttons.forEach(function (x) { x.classList.toggle("is-picked", x === b); });
    var token = b.getAttribute("data-token");
    nextEl.hidden = false;
    if (typing) clearInterval(typing);
    if (reduce) { nextEl.textContent = token; }
    else {
      nextEl.textContent = "";
      var k = 0;
      typing = setInterval(function () {
        nextEl.textContent = token.slice(0, ++k);
        if (k >= token.length) { clearInterval(typing); typing = null; }
      }, 38);
    }
    answer.hidden = false;
    answer.innerHTML = "<p>" + b.getAttribute("data-say") + '</p><p><a href="' + b.getAttribute("data-href") + '">' +
      b.getAttribute("data-cta") + '</a> or <a href="' + b.getAttribute("data-href2") + '">' + b.getAttribute("data-cta2") + "</a></p>";
    if (window.LLM && window.LLM.track) window.LLM.track("hero_pick", { token: token });
  }
  buttons.forEach(function (b, i) { b.addEventListener("click", function () { pick(i); }); });
  temp.addEventListener("input", render);
  sampleBtn.addEventListener("click", function () {
    var p = render(), r = Math.random(), acc = 0;
    for (var i = 0; i < p.length; i++) { acc += p[i]; if (r <= acc) { pick(i); return; } }
    pick(p.length - 1);
  });

  /* one orchestrated entrance: bars grow from zero once */
  if (!reduce) {
    buttons.forEach(function (b) { b.querySelector(".ntp__bar").style.width = "0"; });
    requestAnimationFrame(function () { requestAnimationFrame(render); });
  } else { render(); }
})();
