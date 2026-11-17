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
- `demo.py` — runs query 1 end to end; writes `out/before/`, `out/after/`, `out/report.json`.

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
py -3.15 demo.py
```

## Guardrails (per kathai-provenance)
- Scores are **ordinal indices**, never probabilities; `readiness_caveat()` ships with every ranking.
- No `aggregateRating`/reviews in JSON-LD — none exist.
- No prices in JSON-LD — café pricing is a synthetic model, Atelier price unconfirmed.
- "High protein", caffeine mg, protein g: blocked until formulation confirms; FAQs that would need them are excluded, not guessed.
- Scoring reads the rendered payload (rule 4: payload, not prompt).
- The demo "before" state is seeded, clearly labelled as such.

## Extending
- New query → `demo.py` with a different `QUERY`; add facets in `ranking.INTENT_FACETS`.
- Real signals: swap the seeded before-state for fetched live pages; plug validated
  consumer data in as `Provenance.VALIDATED` when a real panel exists.
