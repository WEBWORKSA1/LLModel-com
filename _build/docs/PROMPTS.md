# LLModel.com: phase-wise build prompts

Copy each phase into an AI coding assistant in order. Every phase states its goal, what to build and how to check it. The repository you are reading was built with these prompts; use them to rebuild, extend or audit it.

**Fixed inputs used in every phase**

- Domain: LLModel.com. Repository: `webworksa1/LLModel-com`, hosted free on GitHub Pages.
- Google AdSense publisher ID `ca-pub-6620975821265271`. Head tag, exactly:
  `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6620975821265271" crossorigin="anonymous"></script>`
- Top of every page, linked to `https://web.works/contact`: "Contact, if you are interested in this website / domain name / sponsorship / advertisement / partnership".
- One inbox receives every form. It must never appear anywhere on the site, in page source or in plain text in the repository.

---

## Phase 0: strategy

> Act as a product strategist for LLModel.com, a new independent site about large language models. Compare five concepts (AI tool directory, news and newsletter, benchmark leaderboard, learning hub, and a decision engine of model directory, comparisons and calculators that feeds B2B lead referrals). For each, estimate demand from public keyword data, revenue per 1,000 visits from AdSense RPM ranges and developer ad-block rates, lead values from B2B cost-per-lead and AI project budgets, and sponsorship prices from AI directories and newsletters. Cite every number and label estimates. Pick one concept, write a 12-month revenue model with conservative, base and aggressive scenarios, and list the risks. Output RESEARCH.md.

Done when: one concept is chosen with numbers, and the revenue table shows which stream dominates.

## Phase 1: competitive teardown

> Visit at least 35 sites in the LLM niche across five groups: leaderboards and benchmarks (LMArena, Artificial Analysis, LiveBench, Scale SEAL, Vellum, Epoch AI, OpenRouter rankings, Aider, SWE-bench); AI directories (There's An AI For That, Futurepedia, Toolify, Future Tools, TopAI.tools, AI Agent Index, Product Hunt AI, G2 LLM category, AIMultiple); model platforms (Hugging Face, Together AI, Groq, Replicate, Ollama, LM Studio, Mistral, Cohere, Fireworks, OpenAI pricing, Gemini API docs); learning and newsletters (DeepLearning.AI, Prompting Guide, Learn Prompting, The Rundown AI, Ben's Bites, Simon Willison, Latent Space); and calculators (DocsBot pricing calculator, APXML VRAM calculator, tiktokenizer, GPT for Work calculator, PricePerToken). For each record: features and interactive elements, forms and the exact fields they ask, monetization with prices, content and SEO patterns, design, and one idea to adopt. Paraphrase only. Rank the 12 most valuable patterns, list every price point with its source, and list the gaps no one fills. Save to research files and summarize in RESEARCH.md.

Done when: 35+ sites are covered, each with fields captured, and the ranked pattern list maps to pages you will build.

## Phase 2: information architecture

> Design the sitemap for a flat static site (all pages at the root, relative links only, so it works at a GitHub Pages project URL and on the custom domain). Include: home; model directory; one page per model; one page per provider; providers index; compare tool; 12 head-to-head comparison pages; tunable rankings; LLM timeline; tools hub with 7 tools (API cost calculator, token counter, VRAM calculator, model picker, context window visualizer, prompt builder, self-host vs API break-even); guides hub with 14 guides; glossary; videos; prompt library; resources; 10 use-case shortlists (coding, agents, long documents, cheapest APIs, longest context, open weights, run locally, multimodal, reasoning, customer support); revenue pages (expert-help lead funnel, list your product, advertise, support, contests and official rules, careers, newsletter); trust pages (about, contact, editorial policy, privacy, terms, disclaimer, trademark and copyright); search; HTML site map; 404; thank-you. Define navigation, footer columns, breadcrumbs, and which pages carry ads.

Done when: every page has a slug, a purpose, a primary call to action and an ad decision (no AdSense on 404 and thank-you pages).

## Phase 3: design system

> Create a distinctive design system grounded in the subject. Palette from viridis, the colormap of ML plots (#440154 to #fde725), on cool plot-paper (#f4f6fb) with deep violet ink; a dark theme to match. Type: Archivo with its width axis for UI and headlines, Newsreader for long-form reading, Martian Mono for tokens and code. The single recurring motif is text split into tokens: the wordmark is two token chips, LL and Model; the hero is an interactive next-token sampler with a temperature slider whose candidates route visitors by intent. Avoid templated defaults: no identical card grids with soft shadows, no all-caps eyebrows, no gradient washes, one orchestrated animation only. Build components: partner bar, sticky header with search and theme toggle, buttons, tables, spec grid, badges, panels, lead band, forms, multi-step funnel, ad slot, video facade, FAQ, table of contents, callouts, tool layout, bar charts, timeline, glossary, prompt cards, rate cards, footer, search palette, toast. Meet WCAG AA contrast, visible focus, reduced motion and phone widths.

Done when: one stylesheet covers every component in light and dark, and screenshots at 1440px and 390px look intentional.

## Phase 4: generator and layout

> Write a Python static site generator in `_build/` (ignored by Jekyll). Pages are HTML with a JSON metadata block in an HTML comment. The layout adds: title, description, canonical on the custom domain, robots, the AdSense meta tag and loader (except on 404 and thank-you), Open Graph and Twitter tags, favicon and manifest links, Google Fonts, the stylesheet with a content hash, a theme script that runs before paint, JSON-LD (Organization on every page, BreadcrumbList, plus page-specific types), the partner bar, header, breadcrumbs, footer with a privacy-choices button, and the search palette. Support placeholders for shared components (ad slots, lead band, newsletter, FAQ, release strip, snapshot table, tools index, featured guides, video grid, timeline teaser, directory, shortlist pills, rankings, comparisons list). Generate sitemap.xml, robots.txt, ads.txt (`google.com, pub-6620975821265271, DIRECT, f08c47fec0942fa0`), llms.txt, site.webmanifest and a search index. Delete stale pages on each build.

Done when: `python3 _build/build.py` renders every page with no unknown placeholders.

## Phase 5: verified data

> Build the data layer as JSON. Models: about 55 current LLMs from about 17 providers, split into closed and open-weight teams, with slug, name, provider, family, release date, status, weights, license, total and active parameters, architecture, context window, max output, input, output and cached-input prices per million tokens, price notes, input and output modalities, reasoning and tool-use flags, an editorial tier, best-for tags, a factual summary, strengths, trade-offs, access channels, official and pricing URLs, sources and a verified date. For open models, add the Hugging Face repo and layers, KV heads, head size and hidden size from config.json. Verify everything against provider documentation as of today; set unknown values to null and say why. Also build: providers, a 50-65 event timeline with primary sources, 25 YouTube videos each verified through the oEmbed endpoint with original summaries, a 150+ term glossary with cross-links, 60 prompt templates and a 100-item resources list with official URLs.

Done when: every JSON file validates, every price has a source and a date, and no video fails oEmbed.

## Phase 6: directory, models, providers, comparisons, rankings

> Generate: the directory with filters (provider, weights, tier, status, inputs, reasoning, 1M+ context), sortable columns, search, URL state and a compare tray; a page per model with specs, real monthly costs for three workloads, strengths and trade-offs, where it fits, a weights-memory table for open models, four alternatives, sources and a generated FAQ; a page per provider; 12 comparison pages with a short verdict, a highlighted spec table, workload costs, "choose A if" lists and FAQ; 10 shortlists with original intros, selection guidance and FAQ; a rankings page with a published value-index formula and live weight sliders; and the timeline grouped by year.

Done when: all numbers on these pages are computed from the data, and every page links to its sources.

## Phase 7: tools

> Build seven browser-only tools with clear explanations and FAQs below each: (1) API cost calculator with presets, caching share, batch toggle, weights filter, pinned models, ranked bars, CSV download and shareable URLs; (2) token counter with a heuristic estimate, an exact count using the gpt-tokenizer o200k encoding loaded on demand from jsDelivr, colored token view and per-model input cost; (3) VRAM calculator for weights, KV cache and overhead with quantization options, attention-type adjustments for hybrid, latent and state-space models, and a hardware fit table; (4) a five-question model picker with hard filters, weighted scoring and reasons; (5) context window visualizer with conversions and a log-scale model comparison; (6) prompt builder with templates, tags, JSON schemas and download; (7) self-host vs API break-even with replicas, utilization and an SVG chart. Every tool links into the lead form with its inputs pre-filled.

Done when: each tool works with no errors, restores state from the URL and explains its formula.

## Phase 8: content

> Write 14 original guides of 1,800-2,600 words: what an LLM is, how LLMs work, how to choose an LLM, open vs closed models, running LLMs locally, RAG, fine-tuning vs RAG vs prompting, API pricing, prompt engineering, benchmarks, security and privacy, AI agents, context windows and hallucinations. Each guide has key takeaways, sources, FAQs, related tools and a next-steps section; verify every current fact against primary sources and date anything volatile. Insert ad slots between sections and the matching video automatically.

Done when: each guide passes the content rules (original, sourced, no hype words, no invented statistics) and its JSON metadata validates.

## Phase 9: monetization

> Wire every revenue stream. AdSense: loader on every content page, the account meta tag, ads.txt, and named ad slots that show house promos until slot IDs are pasted into `config.js`. Lead generation: a four-step funnel (goal; stage, timeline, budget and spend; deployment, data sensitivity and compliance; contact details with consent and an opt-in for partner introductions), A/B/C lead scoring, pre-fill from tools, a lead band on every content page and a sidebar call to action. Listings and advertising: a rate card with founding prices and inquiry forms. Reader support: amount and frequency, allocation (operations, hiring, contests, marketing), payment buttons that appear only when links are configured, and a pledge form fallback. Contests: a skill-based challenge with five published tasks, scoring, prizes, dates, an entry form and official rules with a Quebec clause. Careers and newsletter pages with forms. All forms post through FormSubmit's AJAX endpoint, with a honeypot, timing check and campaign data; the inbox is assembled at submit time from an XOR-obfuscated array and is never rendered.

Done when: every form validates, shows success or a helpful error, and the build contains no trace of the inbox.

## Phase 10: trust and legal

> Write about, contact (with a topic selector and a hidden-address email link), editorial policy (data verification, how tiers and rankings work, AI use, sponsored content, how the site makes money, independence, corrections), privacy policy (forms and FormSubmit, hosting logs, AdSense cookies and opt-outs, Google's consent message, optional analytics, YouTube privacy-enhanced embeds, Google Fonts, sharing, retention, GDPR, Quebec Law 25 and CCPA rights, children, transfers), terms (governed by Quebec law), disclaimer, and a trademark and copyright notice: LLModel is a descriptive domain name; no claim to the generic terms LLM or large language model; no affiliation with any provider or with projects of similar names, such as the llmodel library in GPT4All; nominative use of third-party marks, no logos; copyright and takedown process.

Done when: every page links to these from the footer and none of them makes a claim the operator can't keep.

## Phase 11: SEO and performance

> Give every page a unique title under 70 characters where possible, a 140-160 character description and a canonical URL on llmodel.com. Add JSON-LD: WebSite with SearchAction on home, Article on guides, FAQPage wherever there is a FAQ, WebApplication on tools, ItemList on shortlists, DefinedTermSet on the glossary, VideoObject where upload dates are known, BreadcrumbList everywhere. Render the social image and icons from SVG with the brand fonts. Keep JavaScript per page small, lazy-load YouTube behind a thumbnail facade, and load the tokenizer only on demand.

Done when: sitemap.xml lists every indexable page and the social image renders at 1200 by 630.

## Phase 12: QA

> Write `_build/tests/qa.py` to check every page for: the partner bar, the exact AdSense tag (absent on 404 and thank-you), the AdSense meta tag, one h1, title and description lengths, canonical, valid JSON-LD, duplicate ids, image alt text, broken internal links and anchors, forms without honeypots or status regions, unrendered placeholders; the inbox in any encoding anywhere in the repository; ads.txt and robots.txt content; sitemap coverage; and JavaScript syntax. Then screenshot key pages at 1440px and 390px in both themes and fix what looks wrong.

Done when: the script prints "No problems found." and the screenshots pass a design review.

## Phase 13: deploy

> Push the repository, sources and built site, to `main` of `webworksa1/LLModel-com`. Create the `gh-pages` branch from `main` and confirm GitHub Pages serves it (Settings > Pages > Deploy from a branch > `gh-pages` / root). If your GitHub access allows workflow files, add an Actions workflow that renders the images, builds, runs QA and publishes to `gh-pages` on every push; otherwise rebuild locally and merge `main` into `gh-pages` after each change. Upload the PNG images if your tooling can't push binary files. Then: point LLModel.com at GitHub Pages (A records 185.199.108.153 to 185.199.111.153, `www` CNAME to `webworksa1.github.io`), set `custom_domain` in `_build/site.json`, rebuild and enforce HTTPS; submit a form once to activate FormSubmit and paste the alias into `config.js`; add the site to AdSense with Auto ads and Google's consent message; verify the domain in Search Console and submit the sitemap.

Done when: the live URL loads, forms deliver, and AdSense review is requested on the custom domain.

## Phase 14: growth

> Plan the next 90 days: re-verify model data every month and on every major release; add a comparison page for each new flagship pairing; add shortlists for new use cases with search demand; publish the contest answer key and winners; send the newsletter weekly; pitch featured listings to the vendors in the directory; recruit three implementation partners per lead category (RAG, agents, self-hosting) with written referral terms; and track leads by tier and source to double down on the tools and pages that convert.

Done when: each item has an owner, a date and a metric.
