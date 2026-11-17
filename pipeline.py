"""Shared GEO pipeline: query → intent facets → rank → refresh best-fit page → re-rank.

Used by demo.py (batch) and server.py (real-time, per request). The work for a
given facet set is deterministic, so results are cached by facet set; every
uncached request genuinely regenerates and re-scores the page.
"""
import copy
import json
import pathlib
import time
from functools import lru_cache

import ai
from generator import baseline_page, refined_page
from provenance import readiness_caveat
from ranking import parse_intent, rank

HERE = pathlib.Path(__file__).parent
DATA = json.loads((HERE / "data" / "products.json").read_text(encoding="utf-8"))
PRODUCTS = DATA["products"]
BY_ID = {p["id"]: p for p in PRODUCTS}

# Seeded "before" site — a demo scenario, NOT fetched from a live site.
PRE_OPTIMIZED = {"rush-e", "red-noir", "moss", "sole"}
SCENARIO_NOTE = (
    "Demo scenario: the 'before' site is seeded (Solé, Moss, Red Noir and Rush E "
    "have structured pages; the rest are naive copy renders). It is not a "
    "measured live site.")
BEFORE_PAGES = {
    p["id"]: refined_page(p) if p["id"] in PRE_OPTIMIZED else baseline_page(p)
    for p in PRODUCTS
}


def pick_target(results: list[dict]) -> dict:
    """Best intent fit; ties broken by current rank (the weaker page first)."""
    return min(results, key=lambda r: (-r["intent_match"], -r["rank"]))


@lru_cache(maxsize=256)
def _before_for_facets(facets: tuple[str, ...]):
    before = rank(PRODUCTS, BEFORE_PAGES, "", list(facets))
    target = pick_target(before["results"])["id"] if facets else None
    return before, target


def _row(ranking: dict, pid: str) -> dict:
    return next(r for r in ranking["results"] if r["id"] == pid)


def run(query: str, use_ai: bool = True) -> tuple[dict, dict[str, str]]:
    """Run the pipeline for one query. Returns (report, pages_after).

    With use_ai and a key configured, the target page's personalised copy
    comes from the AI variant store (exact/similar queries reuse a
    variant). If AI is off or fails, the deterministic template is used and the
    report's content_source says why.
    """
    t0 = time.perf_counter()
    facets = tuple(parse_intent(query))
    before, target_id = _before_for_facets(facets)
    before = copy.deepcopy(before)
    after, page, content = None, None, {"source": "none"}
    if target_id:
        prod, variant = BY_ID[target_id], None
        if use_ai and ai.enabled():
            try:
                variant = ai.get_variant(query, prod, list(facets))
                content = {"source": "ai", "match": variant["match"]["how"],
                           "similarity": variant["match"]["similarity"],
                           "variant_id": variant["id"], "model": variant["model"],
                           "provenance": variant["provenance"]}
            except ai.AIError as e:
                content = {"source": "template", "ai_error": str(e)}
        else:
            content = {"source": "template",
                       "reason": "AI disabled" if not use_ai else "no OPENROUTER_API_KEY"}
        page = refined_page(prod, None, list(facets), ai=variant)
        after = rank(PRODUCTS, {**BEFORE_PAGES, target_id: page}, "", list(facets))
    cached = content.get("match") in ("exact", "similar")

    report = {
        "query": query,
        "parsed_intent_facets": list(facets),
        "refreshed": target_id is not None,
        "refresh_target": target_id,
        "before": before,
        "after": after or before,
        "content": content,
        "caveat": readiness_caveat(),
        "scenario_note": SCENARIO_NOTE,
    }
    for r in (report["before"], report["after"]):
        r["query"] = query
    if target_id:
        b, a = _row(before, target_id), _row(after, target_id)
        report["refresh_target_name"] = BY_ID[target_id]["name"]
        report["delta"] = {
            "target_rank": {"before": b["rank"], "after": a["rank"]},
            "target_visibility_index": {"before": b["visibility_index"],
                                        "after": a["visibility_index"]},
            "target_query_rank_index": {"before": b["query_rank_index"],
                                        "after": a["query_rank_index"]},
        }
    else:
        report["note"] = ("No intent recognised, so no page was refreshed. Try "
                          "words like family, experience, gift, Diwali, study, "
                          "calm, spicy, dessert, workout or evening.")
    report["timing_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    report["cached"] = cached

    pages_after = dict(BEFORE_PAGES)
    if target_id:
        pages_after[target_id] = page
    return report, pages_after
