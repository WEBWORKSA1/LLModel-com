/* Guide pages: reading progress and the active table-of-contents link. */
(function () {
  "use strict";
  var article = document.getElementById("article");
  var bar = document.getElementById("read-progress");
  if (!article) return;
  var links = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  var heads = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); }).filter(Boolean);
  var ticking = false;
  function update() {
    ticking = false;
    var rect = article.getBoundingClientRect();
    var total = article.offsetHeight - window.innerHeight;
    var done = Math.min(1, Math.max(0, -rect.top / (total > 0 ? total : 1)));
    if (bar) bar.style.width = (done * 100).toFixed(1) + "%";
    var current = null;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i].getBoundingClientRect().top < 140) current = heads[i];
    }
    links.forEach(function (a) {
      var on = current && a.getAttribute("href") === "#" + current.id;
      a.classList.toggle("is-active", !!on);
      if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
    });
  }
  window.addEventListener("scroll", function () { if (!ticking) { ticking = true; window.requestAnimationFrame(update); } }, { passive: true });
  window.addEventListener("resize", update);
  update();
})();
