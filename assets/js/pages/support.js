/* Support page: "other" amount field and amount-aware donation links. */
(function () {
  "use strict";
  var wrap = document.getElementById("sp-amounts"), other = document.getElementById("sp-other-wrap"), otherIn = document.getElementById("sp-other");
  if (!wrap) return;
  var links = (window.LLM && window.LLM.donateLinks) || (window.SITE && window.SITE.donate) || {};
  function amount() {
    var r = wrap.querySelector("input:checked");
    if (!r) return "";
    return r.value === "other" ? (otherIn.value || "") : r.value;
  }
  function update() {
    var isOther = (wrap.querySelector("input:checked") || {}).value === "other";
    other.hidden = !isOther; otherIn.required = isOther;
    var a = amount();
    Array.prototype.forEach.call(document.querySelectorAll("[data-donate]"), function (el) {
      var tpl = links[el.getAttribute("data-donate")];
      if (tpl) el.href = tpl.replace("{amount}", encodeURIComponent(a));
    });
  }
  wrap.addEventListener("change", update);
  otherIn.addEventListener("input", update);
  update();
})();
