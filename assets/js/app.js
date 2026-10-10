/* LLModel.com core script: theme, navigation, search, forms, ads, videos, copy, consent. */
(function () {
  "use strict";
  var SITE = window.SITE || {};
  var doc = document;
  var $ = function (s, r) { return (r || doc).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); };
  var store = {
    get: function (k, area) { try { return (area || window.localStorage).getItem(k); } catch (e) { return null; } },
    set: function (k, v, area) { try { (area || window.localStorage).setItem(k, v); } catch (e) { /* storage unavailable */ } }
  };

  /* ---------------- helpers shared with tool scripts ---------------- */
  var LLM = window.LLM = window.LLM || {};
  LLM.$ = $; LLM.$$ = $$; LLM.store = store;
  LLM.params = new URLSearchParams(window.location.search);
  LLM.esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  LLM.money = function (v) {
    if (v == null || isNaN(v)) return "—";
    if (v === 0) return "$0";
    if (v < 0.01) return "<$0.01";
    if (v < 10) return "$" + v.toFixed(2);
    if (v < 100000) return "$" + Math.round(v).toLocaleString("en-US");
    if (v < 1e7) return "$" + (v / 1000).toFixed(v < 1e6 ? 1 : 0).replace(/\.0$/, "") + "K";
    return "$" + (v / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
  };
  LLM.price = function (v) {
    if (v == null) return "—";
    if (v >= 1) return "$" + (Math.round(v * 100) / 100).toString().replace(/(\.\d)$/, "$10");
    var s = v.toFixed(3).replace(/0+$/, "");
    if (s.split(".")[1].length < 2) s = v.toFixed(2);
    return "$" + s;
  };
  LLM.tokens = function (n) {
    if (!n) return "—";
    if (n % 1024 === 0) {
      var k = n / 1024;
      if (k >= 1024) { var mm = k / 1024; return (mm === Math.round(mm) ? mm : mm.toFixed(2).replace(/0+$/, "").replace(/\.$/, "")) + "M"; }
      return k + "K";
    }
    if (n >= 1e6) return (n / 1e6).toFixed(2).replace(/0+$/, "").replace(/\.$/, "") + "M";
    if (n >= 1000) return Math.round(n / 1000) + "K";
    return String(n);
  };
  LLM.date = function (d) {
    var M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], p = String(d || "").split("-");
    if (p.length === 3) return M[+p[1] - 1] + " " + (+p[2]) + ", " + p[0];
    if (p.length === 2) return M[+p[1] - 1] + " " + p[0];
    return p[0] || "Unknown";
  };
  LLM.num = function (n, d) { return Number(n).toLocaleString("en-US", { maximumFractionDigits: d == null ? 0 : d }); };
  LLM.toast = function (msg) {
    var t = doc.createElement("div");
    t.className = "toast"; t.setAttribute("role", "status"); t.textContent = msg;
    doc.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 2600);
  };
  LLM.copy = function (text, done) {
    var ok = function () { LLM.toast(done || "Copied to clipboard"); };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(ok, function () { fallback(); });
    } else { fallback(); }
    function fallback() {
      var ta = doc.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      doc.body.appendChild(ta); ta.select();
      try { doc.execCommand("copy"); ok(); } catch (e) { LLM.toast("Press Ctrl+C to copy"); }
      ta.remove();
    }
  };
  LLM.track = function (name, params) {
    if (typeof window.gtag === "function") { try { window.gtag("event", name, params || {}); } catch (e) { /* ignore */ } }
  };

  /* ---------------- theme ---------------- */
  $$("[data-theme-toggle]").forEach(function (b) {
    b.addEventListener("click", function () {
      var cur = doc.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      doc.documentElement.setAttribute("data-theme", cur);
      store.set("llm-theme", cur);
    });
  });

  /* ---------------- mobile menu ---------------- */
  var menuBtn = $(".menu-btn"), mobileNav = $("#mobile-nav");
  if (menuBtn && mobileNav) {
    menuBtn.addEventListener("click", function () {
      var open = mobileNav.classList.toggle("is-open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
      menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
  }

  /* ---------------- search palette ---------------- */
  var palette = $("#palette"), pInput = $("#palette-input"), pList = $("#palette-list");
  var index = null, results = [], sel = 0, lastFocus = null;
  function loadIndex() {
    if (index) return Promise.resolve(index);
    return fetch("assets/data/search.json").then(function (r) { return r.json(); }).then(function (d) { index = d; return d; })
      .catch(function () { index = []; return index; });
  }
  LLM.loadSearchIndex = loadIndex;
  function score(e, words, q) {
    var t = e.t.toLowerCase(), hay = (t + " " + e.d + " " + (e.k || "") + " " + e.y).toLowerCase(), s = 0;
    for (var i = 0; i < words.length; i++) { if (hay.indexOf(words[i]) === -1) return -1; }
    if (t === q) s += 100;
    if (t.indexOf(q) === 0) s += 50;
    if (t.indexOf(q) > -1) s += 25;
    words.forEach(function (w) { if (t.indexOf(w) > -1) s += 8; });
    s += { Model: 6, Tool: 7, Guide: 5, Comparison: 4, Provider: 4, Page: 3, Glossary: 2 }[e.y] || 0;
    return s;
  }
  LLM.searchIndex = function (q, limit) {
    q = (q || "").toLowerCase().trim();
    if (!index) return [];
    if (!q) return index.filter(function (e) { return e.y === "Tool" || e.y === "Guide"; }).slice(0, limit || 8);
    var words = q.split(/\s+/);
    return index.map(function (e) { return { e: e, s: score(e, words, q) }; })
      .filter(function (x) { return x.s >= 0; }).sort(function (a, b) { return b.s - a.s; })
      .slice(0, limit || 12).map(function (x) { return x.e; });
  };
  function renderResults() {
    if (!results.length) { pList.innerHTML = '<li class="palette__empty">No matches. Try a model name, a tool or a term like "context window".</li>'; return; }
    pList.innerHTML = results.map(function (e, i) {
      return '<li><a href="' + LLM.esc(e.u) + '" role="option" id="po-' + i + '" aria-selected="' + (i === sel) + '"><span class="p-title">' +
        LLM.esc(e.t) + '</span><span class="p-type">' + LLM.esc(e.y) + '</span><span class="p-desc">' + LLM.esc(e.d) + "</span></a></li>";
    }).join("");
    pInput.setAttribute("aria-activedescendant", "po-" + sel);
  }
  function openPalette() {
    if (!palette) return;
    lastFocus = doc.activeElement;
    palette.hidden = false; pInput.value = ""; sel = 0;
    loadIndex().then(function () { results = LLM.searchIndex(""); renderResults(); });
    setTimeout(function () { pInput.focus(); }, 0);
  }
  function closePalette() {
    if (!palette || palette.hidden) return;
    palette.hidden = true;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  if (palette) {
    $$("[data-open-search]").forEach(function (b) { b.addEventListener("click", openPalette); });
    palette.addEventListener("click", function (e) { if (e.target === palette) closePalette(); });
    pInput.addEventListener("input", function () { sel = 0; results = LLM.searchIndex(pInput.value); renderResults(); });
    pInput.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); sel = Math.min(sel + 1, results.length - 1); renderResults(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(sel - 1, 0); renderResults(); }
      else if (e.key === "Enter") { e.preventDefault(); if (results[sel]) window.location.href = results[sel].u; else window.location.href = "search.html?q=" + encodeURIComponent(pInput.value); }
      else if (e.key === "Escape") { closePalette(); }
      else if (e.key === "Tab") { e.preventDefault(); }
    });
    doc.addEventListener("keydown", function (e) {
      var tag = (e.target.tagName || "").toLowerCase();
      var typing = tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable;
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) { e.preventDefault(); openPalette(); }
      else if (e.key === "/" && !typing && palette.hidden) { e.preventDefault(); openPalette(); }
      else if (e.key === "Escape") { closePalette(); }
    });
  }

  /* ---------------- campaign capture ---------------- */
  (function () {
    var keys = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"];
    keys.forEach(function (k) { var v = LLM.params.get(k); if (v) store.set("llm-" + k, v, window.sessionStorage); });
    if (!store.get("llm-landing", window.sessionStorage)) {
      store.set("llm-landing", window.location.pathname, window.sessionStorage);
      if (doc.referrer && doc.referrer.indexOf(window.location.host) === -1) store.set("llm-ref", doc.referrer, window.sessionStorage);
    }
    LLM.campaign = function () {
      var o = {};
      keys.forEach(function (k) { var v = store.get("llm-" + k, window.sessionStorage); if (v) o[k] = v; });
      var l = store.get("llm-landing", window.sessionStorage), r = store.get("llm-ref", window.sessionStorage);
      if (l) o.landing_page = l;
      if (r) o.referrer = r;
      return o;
    };
  })();

  /* ---------------- inbox routing (never rendered) ---------------- */
  function route() {
    if (SITE.formAlias) return SITE.formAlias;
    var r = window.__r || [], k = window.__k || "", out = "";
    for (var i = 0; i < r.length; i++) out += String.fromCharCode(r[i] ^ k.charCodeAt(i % k.length));
    return out;
  }
  $$("[data-mailto]").forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var subj = a.getAttribute("data-mailto") || "Message from LLModel.com";
      window.location.href = "mail" + "to:" + route() + "?subject=" + encodeURIComponent(subj);
    });
  });

  /* ---------------- forms ---------------- */
  var loadedAt = Date.now();
  var SUBJECTS = {
    newsletter: "New subscriber: The LLM Brief", lead: "New LLM project lead", contact: "Contact form message",
    advertise: "Advertising inquiry", listing: "Product listing request", pledge: "Support pledge", contest: "Contest entry",
    careers: "Job application", checklist: "Checklist request", sponsor: "Prize sponsorship inquiry"
  };
  function serialize(form) {
    var data = {}, fd = new FormData(form);
    fd.forEach(function (v, k) {
      if (k === "_honey") return;
      if (typeof v !== "string") return;
      v = v.trim();
      if (data[k]) data[k] = data[k] + ", " + v; else data[k] = v;
    });
    return data;
  }
  function fieldError(field, msg) {
    field.setAttribute("aria-invalid", "true");
    var id = (field.id || field.name) + "-err", el = doc.getElementById(id);
    if (!el) {
      el = doc.createElement("p"); el.className = "field-error"; el.id = id;
      var host = field.closest(".field") || field.parentNode;
      host.appendChild(el);
    }
    el.textContent = msg;
    field.setAttribute("aria-describedby", id);
  }
  function clearErrors(scope) {
    $$("[aria-invalid]", scope).forEach(function (f) { f.removeAttribute("aria-invalid"); });
    $$(".field-error", scope).forEach(function (e) { e.remove(); });
  }
  LLM.validate = function (scope) {
    clearErrors(scope);
    var first = null;
    $$("input, select, textarea", scope).forEach(function (f) {
      if (f.disabled || f.type === "hidden" || f.classList.contains("hp")) return;
      if (f.type === "radio" || f.type === "checkbox") {
        if (f.required && f.type === "checkbox" && !f.checked) { fieldError(f, "Please tick this box to continue."); first = first || f; }
        return;
      }
      if (!f.checkValidity()) {
        var msg = f.validity.valueMissing ? "This field is required." : f.validity.typeMismatch && f.type === "email" ? "Enter an email address like name@company.com." :
          f.validity.typeMismatch && f.type === "url" ? "Enter a full link starting with https://" : f.validationMessage || "Check this field.";
        fieldError(f, msg); first = first || f;
      }
    });
    $$("fieldset[data-required-group]", scope).forEach(function (fs) {
      if (!$("input:checked", fs)) {
        var anchor = $("input", fs); first = first || anchor;
        var p = doc.createElement("p"); p.className = "field-error"; p.textContent = "Choose at least one option."; fs.appendChild(p);
      }
    });
    if (first) { first.focus(); return false; }
    return true;
  };
  LLM.submit = function (form, extra) {
    var type = form.getAttribute("data-form") || "contact";
    var status = $(".form-status", form);
    var btn = $('button[type="submit"]', form);
    var hp = $('input[name="_honey"]', form);
    if (hp && hp.value) return Promise.resolve(false);
    if (Date.now() - loadedAt < 1500) { if (status) { status.className = "form-status is-err"; status.textContent = "That was quick. Please check the form and submit again."; } return Promise.resolve(false); }
    var data = serialize(form);
    Object.keys(extra || {}).forEach(function (k) { data[k] = extra[k]; });
    var camp = LLM.campaign ? LLM.campaign() : {};
    Object.keys(camp).forEach(function (k) { data[k] = camp[k]; });
    data._subject = (form.getAttribute("data-subject") || SUBJECTS[type] || "Website form") + (data.topic ? ": " + data.topic : "");
    data._template = "table";
    data._captcha = "false";
    data["Form"] = type;
    data["Page"] = window.location.href.split("#")[0];
    data["Submitted"] = new Date().toISOString();
    if (btn) { btn.disabled = true; btn.setAttribute("data-label", btn.textContent); btn.textContent = "Sending…"; }
    if (status) { status.className = "form-status"; status.textContent = ""; }
    return fetch("https://formsubmit.co/ajax/" + route(), {
      method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(data)
    }).then(function (r) { return r.json().catch(function () { return {}; }); }).then(function (res) {
      var ok = res && (res.success === true || res.success === "true");
      if (!ok) throw new Error((res && res.message) || "Submission failed");
      LLM.track("generate_lead", { form_type: type });
      var msg = form.getAttribute("data-success") || "Thanks, it's in. We'll be in touch soon.";
      if (form.hasAttribute("data-replace")) {
        var box = doc.createElement("div");
        box.className = "form-success"; box.setAttribute("role", "status"); box.tabIndex = -1;
        box.innerHTML = '<h3>' + LLM.esc(form.getAttribute("data-success-title") || "Received") + "</h3><p>" + LLM.esc(msg) + "</p>";
        form.replaceWith(box); box.focus();
      } else if (status) {
        status.className = "form-status is-ok"; status.textContent = msg; form.reset();
      }
      return true;
    }).catch(function () {
      if (status) {
        status.className = "form-status is-err";
        status.innerHTML = 'We couldn’t send that just now. Please try again in a minute, or <a href="contact.html" data-mailto="' +
          LLM.esc(data._subject) + '">email us instead</a>.';
        var a = $("[data-mailto]", status);
        if (a) a.addEventListener("click", function (e) { e.preventDefault(); window.location.href = "mail" + "to:" + route() + "?subject=" + encodeURIComponent(data._subject); });
      }
      return false;
    }).then(function (ok) {
      if (btn && btn.isConnected) { btn.disabled = false; btn.textContent = btn.getAttribute("data-label") || "Send"; }
      return ok;
    });
  };
  $$("form[data-form]").forEach(function (form) {
    if (form.hasAttribute("data-custom")) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!LLM.validate(form)) return;
      LLM.submit(form);
    });
  });
  /* prefill fields from the URL: contact.html?topic=correction */
  $$("form[data-prefill]").forEach(function (form) {
    LLM.params.forEach(function (v, k) {
      var f = form.elements[k];
      if (!f || !v) return;
      if (f.tagName === "SELECT" || f.type === "text" || f.type === "hidden" || f.tagName === "TEXTAREA") f.value = v;
    });
  });
  /* character counters */
  $$("textarea[maxlength]").forEach(function (t) {
    var c = doc.createElement("p"); c.className = "counter"; c.setAttribute("aria-hidden", "true");
    var max = +t.getAttribute("maxlength");
    var upd = function () { c.textContent = t.value.length + " / " + max; };
    t.insertAdjacentElement("afterend", c); upd(); t.addEventListener("input", upd);
  });

  /* ---------------- ad slots ---------------- */
  var slots = (SITE.adsense && SITE.adsense.slots) || {};
  $$(".ad-slot[data-ad]").forEach(function (box) {
    var conf = slots[box.getAttribute("data-ad")] || slots.content;
    if (!conf) return;
    if (typeof conf === "string") conf = { id: conf };
    var ins = doc.createElement("ins");
    ins.className = "adsbygoogle";
    ins.style.display = "block";
    ins.setAttribute("data-ad-client", SITE.adsense.client);
    ins.setAttribute("data-ad-slot", conf.id);
    ins.setAttribute("data-ad-format", conf.format || "auto");
    if (conf.layout) ins.setAttribute("data-ad-layout", conf.layout);
    ins.setAttribute("data-full-width-responsive", "true");
    var fill = $(".ad-fill", box);
    fill.innerHTML = ""; fill.appendChild(ins);
    $(".ad-label", box).textContent = "Advertisement";
    box.setAttribute("aria-label", "Advertisement");
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) { /* ad blocked */ }
  });

  /* ---------------- video facades ---------------- */
  doc.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".video__btn");
    if (!btn) return;
    var wrap = btn.closest(".video"), id = wrap.getAttribute("data-yt");
    var f = doc.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) + "?autoplay=1&rel=0";
    f.title = btn.getAttribute("aria-label").replace(/^Play video: /, "");
    f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    f.allowFullscreen = true; f.loading = "lazy";
    f.referrerPolicy = "strict-origin-when-cross-origin";
    wrap.innerHTML = ""; wrap.appendChild(f);
    LLM.track("video_play", { video_id: id });
  });
  var ytSlot = $("#yt-channel-slot");
  if (ytSlot && SITE.youtube && SITE.youtube.channel) {
    ytSlot.innerHTML = '<div class="panel" style="display:flex;flex-wrap:wrap;gap:1rem;align-items:center;justify-content:space-between;margin-top:2rem">' +
      "<p><strong>Watch our own explainers.</strong> New videos on models, prices and tools.</p>" +
      '<a class="btn btn--primary" target="_blank" rel="noopener" href="' + LLM.esc(SITE.youtube.channel) + '?sub_confirmation=1">Subscribe on YouTube</a></div>';
  }

  /* ---------------- copy buttons ---------------- */
  doc.addEventListener("click", function (e) {
    var t = e.target.closest && e.target.closest("[data-copy-target],[data-copy-link],[data-copy-text]");
    if (!t) return;
    if (t.hasAttribute("data-copy-link")) { LLM.copy(window.location.href.split("#")[0], "Link copied"); return; }
    if (t.hasAttribute("data-copy-text")) { LLM.copy(t.getAttribute("data-copy-text")); return; }
    var el = doc.getElementById(t.getAttribute("data-copy-target"));
    if (!el) return;
    var src = el.matches("pre, textarea, code, output") ? el : $("pre, textarea, output", el) || el;
    LLM.copy(src.value != null && src.tagName === "TEXTAREA" ? src.value : src.textContent, "Prompt copied");
  });

  /* ---------------- affiliate links (resources) ---------------- */
  var aff = SITE.affiliates || {};
  $$("a[data-aff]").forEach(function (a) {
    var k = a.getAttribute("data-aff");
    if (k && aff[k]) { a.href = aff[k]; a.rel = "sponsored noopener"; }
  });

  /* ---------------- donation buttons ---------------- */
  var don = SITE.donate || {};
  var anyDonate = false;
  $$("[data-donate]").forEach(function (a) {
    var k = a.getAttribute("data-donate");
    if (don[k]) { a.hidden = false; anyDonate = true; a.setAttribute("data-href", don[k]); a.href = don[k].replace("{amount}", ""); }
  });
  $$("[data-donate-wrap]").forEach(function (w) { w.hidden = !anyDonate; });
  LLM.donateLinks = don;

  /* ---------------- privacy choices (Google consent message) ---------------- */
  $$("[data-privacy-choices]").forEach(function (b) {
    b.addEventListener("click", function () {
      var fc = window.googlefc;
      if (fc && fc.callbackQueue) {
        fc.callbackQueue.push(function () { if (typeof fc.showRevocationMessage === "function") fc.showRevocationMessage(); });
      } else { window.location.href = "privacy.html#cookies"; }
    });
  });

  /* ---------------- analytics (optional) ---------------- */
  if (SITE.ga4 && /^G-[A-Z0-9]+$/.test(SITE.ga4)) {
    var s = doc.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + SITE.ga4;
    doc.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", SITE.ga4, { anonymize_ip: true });
  }
})();
