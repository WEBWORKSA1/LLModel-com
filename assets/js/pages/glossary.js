/* Glossary: text filter and category chips. */
(function () {
  "use strict";
  var q = document.getElementById("gl-q"), count = document.getElementById("gl-count"), empty = document.getElementById("gl-empty");
  if (!q) return;
  var terms = Array.prototype.slice.call(document.querySelectorAll(".term"));
  var letters = Array.prototype.slice.call(document.querySelectorAll(".letter"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".filters .chip-toggle[data-cat]"));
  function run() {
    var t = q.value.toLowerCase().trim();
    var cats = chips.filter(function (c) { return c.getAttribute("aria-pressed") === "true"; }).map(function (c) { return c.getAttribute("data-cat"); });
    var n = 0;
    terms.forEach(function (el) {
      var ok = (!t || el.getAttribute("data-text").indexOf(t) > -1 || el.textContent.toLowerCase().indexOf(t) > -1) &&
        (!cats.length || cats.indexOf(el.getAttribute("data-cat")) > -1);
      el.hidden = !ok; if (ok) n++;
    });
    letters.forEach(function (h) {
      var box = h.nextElementSibling;
      var any = box && Array.prototype.some.call(box.querySelectorAll(".term"), function (x) { return !x.hidden; });
      h.hidden = !any; if (box) box.hidden = !any;
    });
    count.textContent = n + (n === 1 ? " term" : " terms");
    empty.hidden = n > 0;
  }
  q.addEventListener("input", run);
  chips.forEach(function (c) { c.addEventListener("click", function () { c.setAttribute("aria-pressed", c.getAttribute("aria-pressed") === "true" ? "false" : "true"); run(); }); });
})();
