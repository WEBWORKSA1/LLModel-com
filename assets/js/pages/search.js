/* Full search results page, using the same index as the search palette. */
(function () {
  "use strict";
  var L = window.LLM;
  if (!L || !L.loadSearchIndex) return;
  var q = document.getElementById("sr-q"), list = document.getElementById("sr-results"), count = document.getElementById("sr-count");
  function run() {
    var term = q.value.trim();
    if (!term) { count.textContent = "Type a word to search."; list.innerHTML = ""; return; }
    var res = L.searchIndex(term, 50);
    count.textContent = res.length ? res.length + " results for “" + term + "”" : "No results for “" + term + "”. Try a shorter or different word.";
    list.innerHTML = res.map(function (e) {
      return '<li><a class="row" href="' + L.esc(e.u) + '"><span class="row__title">' + L.esc(e.t) + '</span><span class="row__desc">' + L.esc(e.d) +
        '</span><span class="row__meta">' + L.esc(e.y) + "</span></a></li>";
    }).join("");
  }
  q.value = L.params.get("q") || "";
  L.loadSearchIndex().then(run);
  q.addEventListener("input", function () {
    run();
    history.replaceState(null, "", window.location.pathname + (q.value ? "?q=" + encodeURIComponent(q.value) : ""));
  });
  q.focus();
})();
