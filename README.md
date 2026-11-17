# KATHAI GEO pipeline — AI ranking refinement + personalized pages

Answers two questions:
1. **How do we refine AI-answer-engine ranking?** Score every product page on
   the structural signals answer engines consume, find the gap, fix the page.
2. **How do we personalize pages per query?** Parse the query into intent
   facets, regenerate the page with intent-led content, re-rank.

## Files
- `data/products.json` — 8 flavours, structured from Kathai_Flavours.docx (observed brand copy).
- `provenance.py` — tier tags, blocked-claims list, mandatory score caveat.
- `ranking.py` — visibility scorer (scores the rendered HTML payload, not intent):
  - Structured data /30 — Product, FAQPage, Breadcrumb JSON-LD
  - FAQ coverage /20 — quotable Q&A pairs
  - Answerability /25 — direct-answer blocks, taste scores, occasion, prep
  - Media /15 — six-part visual system + alt text
  - Claim safety /10 — deducts unsubstantiated claims; fabricated ratings zero it
  - Intent conditioning: `final = visibility × (0.5 + 0.5 × intent_match)`
- `generator.py` — `baseline_page()` (naive render) and `refined_page(product, query, facets)`.
  `personalize()` builds intent-led blocks for every facet (family, experience, gift,
  focus, calm, adventure, dessert, fitness, evening) from observed copy only.
- `pipeline.py` — shared query → facets → rank → refresh best-fit page → re-rank, cached per facet set.
- `server.py` — **real-time rendering**: a standard-library HTTP server that runs the pipeline per request.
- `demo.py` — batch run of one query; writes `out/before/`, `out/after/`, `out/report.json`.

## Run

`charmap` is a built-in Python codec, not a pip package. The demo writes HTML
and JSON as UTF-8 explicitly, so it does not depend on the Windows console or
system default encoding.

Install the [Python install manager](https://www.python.org/downloads/windows/),
then install the latest stable Python release (Python 3.15.2 as of November
17, 2026):

```powershell
py install 3.15
py -3.15 --version
```

Then run the demo with that interpreter:

```
py -3.15 demo.py                                  # default query
py -3.15 demo.py "a Diwali gift for my parents"   # any query
```

### Real-time server

```
py -3.15 server.py              # http://127.0.0.1:8000
```

Open the URL, type a query: the intent is parsed, all eight pages are ranked, the
best-fit page is regenerated for that intent and re-ranked, and the rendered page
appears beside the ranking (debounced as you type). No API keys or third-party
packages are needed.

| Route | Returns |
|---|---|
| `GET /` | Before / after console (`static/console.html`; edits apply on refresh, no restart) |
| `GET /api/personalize?q=…` | JSON: facets, before/after ranking, delta, caveat, timing |
| `GET /page/<id>?q=…` | The product page as served for that query (`X-Kathai-Intent`, `X-Kathai-Personalized` headers) |
| `GET /page/<id>` | The seeded "before" page |

Personalized variants keep `<link rel="canonical">` on the base product URL.
Images are placeholder SVGs until the six-part visual assets exist.

## Guardrails (per kathai-provenance)
- Scores are **ordinal indices**, never probabilities; `readiness_caveat()` ships with every ranking.
- No `aggregateRating`/reviews in JSON-LD — none exist.
- No prices in JSON-LD — café pricing is a synthetic model, Atelier price unconfirmed.
- "High protein", caffeine mg, protein g: blocked until formulation confirms; FAQs that would need them are excluded, not guessed.
- Scoring reads the rendered payload (rule 4: payload, not prompt).
- The demo "before" state is seeded, clearly labelled as such.

## Decisions (2026-11-17)
- **Word count reads visible text only.** The scorer counted CSS inside `<style>`
  as page words, so naive pages got answerability points they hadn't earned. Fixed:
  `<style>`/`<script>` are stripped first. Baseline pages drop 14.5 → 12.5; the
  query-1 headline is now Salora rank 5 → 1, visibility **12.5 → 96.0**
  (previously reported as 14.5 → 96.0).
- **Intent keywords match whole words.** Substring matching made "workout"
  fire the focus facet via "work". Keywords now match as whole words (optional plural).
- **Focus no longer matches the "Bold" tag** (it made Picante tie Rush E for study
  queries). **Calm gains `adventure_max: 3`** (calm ≠ adventurous; stops Picante winning
  "calm evening").
- **Refresh target = best intent fit**, ties to the weaker page — even if it already
  ranks 1 (its page is still refreshed for the query). Previously: best fit that was not rank 1.
- **Atelier price (₹1,799) and Diwali session timings are not rendered** — the deck marks
  both as to be confirmed.

These are judgement calls made while building the live server, not measured outcomes.

## Extending
- New query → `demo.py` with a different `QUERY`; add facets in `ranking.INTENT_FACETS`.
- Real signals: swap the seeded before-state for fetched live pages; plug validated
  consumer data in as `Provenance.VALIDATED` when a real panel exists.
"# geo" 
