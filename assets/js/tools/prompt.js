/* Prompt builder: assemble a structured prompt from form fields. */
(function () {
  "use strict";
  var L = window.LLM;
  var form = document.getElementById("pb-form");
  if (!L || !form) return;
  var $ = function (id) { return document.getElementById(id); };
  var out = $("pb-out"), count = $("pb-count");
  var F = ["role", "task", "context", "input", "format", "length", "schema", "tone", "reason", "rules", "examples"];
  var TPL = {
    blank: {},
    summary: { role: "an analyst who writes clear briefings for busy executives", task: "Summarize the document below.", context: "The summary will be read by a leadership team deciding whether to act on this document. They need the main points, the numbers that matter and any risks.", format: "Bullet points", length: "100 to 300 words", rules: "Only use facts stated in the document.\nQuote numbers exactly.\nEnd with one line on what decision this supports." },
    extract: { role: "a careful data-entry specialist", task: "Extract the fields listed below from the text.", format: "JSON", schema: "company_name: legal name as written\ninvoice_date: ISO 8601 date\ntotal_amount: number without currency symbol\ncurrency: ISO 4217 code", rules: "Use null for any field that isn't in the text.\nDon't guess or infer values.\nReturn only the JSON object." },
    review: { role: "a senior software engineer doing a code review", task: "Review the code below for bugs, security issues and readability problems.", context: "This code is about to be merged into a production service. The team values small, specific suggestions over rewrites.", format: "Numbered steps", rules: "Rank findings by severity.\nFor each finding, quote the line and suggest a fix.\nSay explicitly if you find no serious issues.", reason: "steps" },
    reply: { role: "a friendly, knowledgeable customer support agent", task: "Write a reply to the customer message below.", context: "Our refund window is 30 days from purchase. Refunds go back to the original payment method within 5 business days.", format: "An email", length: "Under 100 words", tone: "Friendly", rules: "Acknowledge the problem in the first sentence.\nNever promise anything not covered by the policy above.\nEnd with one clear next step." },
    product: { role: "a conversion copywriter for e-commerce", task: "Write a product description for the item below.", context: "Shoppers skim on mobile. They want to know what it is, who it's for and why it's better than the alternative.", format: "Paragraphs", length: "100 to 300 words", tone: "Persuasive", rules: "Lead with the main benefit, not the feature list.\nInclude three short bullet points of key specs.\nNo superlatives you can't back up." },
    actions: { role: "a project manager", task: "Turn the meeting notes below into a list of action items.", format: "A table", rules: "Columns: action, owner, due date, status.\nUse 'unassigned' when no owner is named.\nDon't add actions that weren't discussed." }
  };
  function v(id) { return ($("pb-" + id).value || "").trim(); }
  function build() {
    $("pb-schema-wrap").hidden = $("pb-format").value !== "JSON";
    var p = [];
    if (v("role")) p.push("You are " + v("role").replace(/^you are\s+/i, "").replace(/\.$/, "") + ".");
    p.push("<task>\n" + (v("task") || "[Describe the task]") + "\n</task>");
    if (v("context")) p.push("<context>\n" + v("context") + "\n</context>");
    if (v("input")) p.push("<input>\n" + v("input") + "\n</input>");
    if (v("examples")) p.push("<example_of_a_good_answer>\n" + v("examples") + "\n</example_of_a_good_answer>");
    var req = [];
    var fmt = $("pb-format").value;
    if (fmt === "JSON") {
      req.push("Respond with a single valid JSON object and nothing else.");
      var fields = v("schema").split(/\n+/).filter(Boolean);
      if (fields.length) req.push("Use exactly these fields:\n" + fields.map(function (f) { return "  - " + f.trim(); }).join("\n"));
    } else { req.push("Format: " + fmt.charAt(0).toLowerCase() + fmt.slice(1) + "."); }
    if (v("length")) req.push("Length: " + v("length").toLowerCase() + ".");
    if (v("tone")) req.push("Tone: " + v("tone").toLowerCase() + ".");
    v("rules").split(/\n+/).filter(Boolean).forEach(function (r) { req.push(r.replace(/^[-*]\s*/, "")); });
    if ($("pb-unsure").checked) req.push("If the input doesn't contain what you need, say so instead of guessing.");
    p.push("<requirements>\n" + req.map(function (r) { return "- " + r; }).join("\n") + "\n</requirements>");
    var reason = $("pb-reason").value;
    if (reason === "steps") p.push("Work through the problem step by step before you write the final answer.");
    if (reason === "final") p.push("Think it through as needed, then give only the final answer in the requested format.");
    if ($("pb-check").checked) p.push("Before you reply, check your answer against every requirement above and fix anything that doesn't comply.");
    var text = p.join("\n\n");
    out.textContent = text;
    var est = Math.round(text.length / 4);
    count.textContent = "About " + L.num(est) + " tokens, " + L.num((text.match(/\S+/g) || []).length) + " words";
    return text;
  }
  function load(name) {
    var t = TPL[name] || {};
    F.forEach(function (k) { var el = $("pb-" + k); if (!el) return; el.value = t[k] != null ? t[k] : (el.tagName === "SELECT" ? el.options[0].value : ""); });
    build();
  }
  $("pb-tpl").addEventListener("change", function () { load(this.value); });
  form.addEventListener("input", build);
  form.addEventListener("change", build);
  $("pb-reset").addEventListener("click", function () { $("pb-tpl").value = "blank"; load("blank"); });
  $("pb-dl").addEventListener("click", function () {
    var blob = new Blob([build()], { type: "text/plain" });
    var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "prompt.txt";
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  });
  $("pb-tc").addEventListener("click", function () {
    L.store.set("llm-prompt", build(), window.sessionStorage);
    window.location.href = "token-counter.html?from=builder";
  });
  load(L.params.get("template") || "summary");
  if (L.params.get("template")) $("pb-tpl").value = L.params.get("template");
  else $("pb-tpl").value = "summary";
})();
