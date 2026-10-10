/* Prompt library: text filter and category chips. Copy buttons are handled by app.js. */
(function () {
  "use strict";
  var q = document.getElementById("pr-q"), count = document.getElementById("pr-count"), empty = document.getElementById("pr-empty");
  if (!q) return;
  var cards = Array.prototype.slice.call(document.querySelectorAll(".prompt-card"));
  var groups = Array.prototype.slice.call(document.querySelectorAll(".prompt-group"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".filters .chip-toggle[data-cat]"));
  function run() {
    var t = q.value.toLowerCase().trim();
    var cats = chips.filter(function (c) { return c.getAttribute("aria-pressed") === "true"; }).map(function (c) { return c.getAttribute("data-cat"); });
    var n = 0;
    cards.forEach(function (el) {
      var ok = (!t || el.getAttribute("data-text").indexOf(t) > -1 || el.textContent.toLowerCase().indexOf(t) > -1) &&
        (!cats.length || cats.indexOf(el.getAttribute("data-cat")) > -1);
      el.hidden = !ok; if (ok) n++;
    });
    groups.forEach(function (g) { g.hidden = !g.querySelector(".prompt-card:not([hidden])"); });
    count.textContent = n + (n === 1 ? " prompt" : " prompts");
    empty.hidden = n > 0;
  }
  q.addEventListener("input", run);
  chips.forEach(function (c) { c.addEventListener("click", function () { c.setAttribute("aria-pressed", c.getAttribute("aria-pressed") === "true" ? "false" : "true"); run(); }); });
})();
