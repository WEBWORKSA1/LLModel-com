# LLModel.com content spec (read before writing anything)

LLModel.com is an independent, vendor-neutral field guide to large language models: a model directory,
comparisons, calculators, plain-English guides, a glossary and curated videos. Readers are developers,
technical founders, product managers, CTOs, analysts and curious professionals. Today's date is
2026-10-10. The site must pass Google AdSense review, so every page has to be original, substantive,
accurate and genuinely useful.

## Non-negotiable rules

1. Original writing only. Never copy or closely paraphrase another site's sentences or structure.
   Quotations are allowed only when the exact wording matters, at most one per source, under 15 words.
2. Accuracy over confidence. The LLM field changes monthly. Before stating any current fact (latest model
   names, prices, context windows, release dates, benchmark leaders, who offers what), verify it with
   WebSearch/WebFetch against a primary source (provider docs, official blog, paper, model card).
   If you can't verify a figure, write around it ("several frontier models now accept 1M+ tokens")
   rather than inventing one. Never fabricate statistics, studies, quotes, customer stories or people.
3. Prefer durable explanations. Use dated phrasing for anything volatile ("as of October 2026").
4. No medical, legal or financial advice. Security/privacy content is general guidance.
5. Never mention or display any email address. Never invent contact details.
6. Plain, expert, practical tone. Second person ("you"). Short paragraphs (2-4 sentences). Concrete
   examples, numbers that are worked out, and decision criteria. No filler openers ("In today's
   fast-paced world"), no hype words ("revolutionary", "game-changer", "unleash", "delve").
   American English. Sentence-case headings.

## HTML conventions for guide bodies

Guides are saved as `/home/claude/llmodel/_build/src/guides/<slug>.html`. Each file starts with a JSON
metadata block inside an HTML comment that begins with `<!--meta` and ends with `-->`, followed by the
body HTML. The JSON must parse with Python's `json.loads` (double quotes, no trailing commas, no comments).

```
<!--meta
{
  "slug": "what-is-a-large-language-model",
  "title": "What Is a Large Language Model? A Plain-English Guide",
  "h1": "What is a large language model?",
  "description": "140-158 character meta description with the main keyword near the start.",
  "category": "Fundamentals",
  "level": "Beginner",
  "updated": "2026-10-10",
  "keywords": ["large language model", "what is an llm", "llm meaning"],
  "summary": "Two sentences used on cards and in search results.",
  "key_takeaways": ["Takeaway one.", "Takeaway two.", "Takeaway three.", "Takeaway four."],
  "faq": [
    {"q": "Question people actually search?", "a": "Plain-text answer, 40-90 words, no HTML."}
  ],
  "sources": [
    {"title": "Attention Is All You Need (Vaswani et al., 2017)", "url": "https://arxiv.org/abs/1706.03762"}
  ],
  "related_tools": ["llm-cost-calculator", "token-counter"],
  "related_guides": ["how-llms-work", "how-to-choose-an-llm"]
}
-->
<p>Opening paragraph that states what the reader will learn and why it matters.</p>
<h2 id="what-an-llm-is">What an LLM is</h2>
<p>...</p>
```

Field rules: `category` is one of Fundamentals, Choosing & buying, Building, Running & deploying,
Safety & quality. `level` is Beginner, Intermediate or Advanced. 4-6 `key_takeaways`. 4-6 `faq` items.
4-10 `sources`, primary sources preferred (papers, official docs, official blogs). `related_tools` and
`related_guides` use slugs from the lists below.

Allowed body tags: `p`, `h2` and `h3` (each with a unique kebab-case `id`), `ul`, `ol`, `li`, `strong`,
`em`, `a`, `code`, `pre` (wrap code as `<pre><code>...</code></pre>`, escape `<` `>` `&`), `table` with
`thead`/`tbody`/`tr`/`th`/`td`, `div class="callout tip"`, `div class="callout note"`,
`div class="callout warn"` (each callout contains one or more `p`), and `div class="checklist"` containing
a `ul`. No `h1` (the template adds it), no images, no inline styles, no scripts, no iframes, no ad markers
(ads are inserted automatically between sections). Aim for 6-10 `h2` sections. Each guide includes:
a short practical checklist or decision table, a "Common mistakes" section, and a final "Next steps"
section that links to 2-3 relevant tools or guides. Where it fits naturally (once, never pushy), link to
`hire-llm-experts.html` for readers who want hands-on help.

External links: plain `<a href="https://...">text</a>`; the build adds rel/target attributes.
Internal links: relative file names exactly as listed below.

## Internal pages you may link to

Core: `models.html` (LLM directory), `leaderboard.html` (LLM rankings & value index), `compare.html`
(side-by-side comparison), `providers.html` (LLM providers), `llm-timeline.html` (history of LLMs),
`tools.html`, `guides.html`, `glossary.html`, `videos.html`, `prompts.html` (prompt library),
`resources.html` (tools, frameworks, courses, papers), `hire-llm-experts.html` (get expert help),
`newsletter.html`.

Tools (slug = file name without .html):
- `llm-cost-calculator` - API cost calculator (tokens x requests x model prices)
- `token-counter` - count/estimate tokens in text and cost per model
- `vram-calculator` - GPU memory needed to run an open model locally (weights + KV cache)
- `llm-picker` - short quiz that recommends models for a use case and budget
- `context-window-visualizer` - what fits in 8K, 128K, 1M tokens
- `prompt-builder` - assemble a structured prompt (role, task, context, format, constraints)
- `self-host-vs-api-calculator` - break-even between GPU hosting and paying per token

Guides (slug = file name without .html):
`what-is-a-large-language-model`, `how-llms-work`, `how-to-choose-an-llm`, `open-source-vs-closed-llms`,
`run-llms-locally`, `rag-explained`, `fine-tuning-vs-rag-vs-prompting`, `llm-api-pricing-explained`,
`prompt-engineering-guide`, `llm-benchmarks-explained`, `llm-security-and-privacy`, `ai-agents-explained`,
`context-windows-explained`, `llm-hallucinations`

Glossary anchors: link a term as `glossary.html#<slug>` using ONLY these slugs (the glossary guarantees them; the build
points each link at the topic page that holds the full definition, such as `glossary-training.html#<slug>`):
large-language-model, token, tokenization, byte-pair-encoding, context-window, transformer, attention,
embedding, parameters, pretraining, fine-tuning, instruction-tuning, rlhf, dpo, inference, temperature,
top-p, logits, hallucination, rag, vector-database, chunking, prompt-engineering, system-prompt,
few-shot-prompting, chain-of-thought, reasoning-model, mixture-of-experts, quantization, gguf, lora,
distillation, kv-cache, latency, throughput, benchmark, mmlu, open-weights, multimodal, ai-agent,
tool-calling, structured-outputs, prompt-injection, guardrails, grounding, prompt-caching, batch-api,
model-context-protocol, small-language-model, foundation-model, scaling-laws, alignment, synthetic-data,
speculative-decoding, perplexity, vram, model-card, llm-as-a-judge, evaluation
