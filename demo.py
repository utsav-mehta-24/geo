"""Demo: query 1 — 'I want hot chocolate with my family and need an experience'.

BEFORE state (realistic heterogeneous site):
  - Rush E and Red Noir already have structurally refined pages (the hype
    flavours got attention first).
  - Everything else, including Salora, is a naive render of the docx copy.
AFTER state:
  - The pipeline identifies the best intent-fit product whose page is
    underperforming, regenerates that page personalized to the query, and
    re-ranks. Only that one page changes.
"""
import json
import pathlib
import sys

from generator import baseline_page, refined_page
from ranking import rank, parse_intent

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
# Keep the demo usable from Windows terminals that still default to cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
(OUT / "before").mkdir(parents=True, exist_ok=True)
(OUT / "after").mkdir(parents=True, exist_ok=True)

data = json.loads((HERE / "data" / "products.json").read_text(encoding="utf-8"))
products = data["products"]
QUERY = "I want hot chocolate with my family and need an experience"
PRE_OPTIMIZED = {"rush-e", "red-noir", "moss", "sole"}  # pages that already got attention

# ---- BEFORE
pages_before = {}
for p in products:
    html = refined_page(p) if p["id"] in PRE_OPTIMIZED else baseline_page(p)
    pages_before[p["id"]] = html
    (OUT / "before" / f"{p['id']}.html").write_text(html, encoding="utf-8")

before = rank(products, pages_before, QUERY)

# ---- pick the refresh target: best intent fit that is NOT already rank 1
facets = parse_intent(QUERY)
target = next(r for r in sorted(before["results"],
                                key=lambda r: -r["intent_match"])
              if r["rank"] != 1)

# ---- AFTER: regenerate only the target page, personalized to the query
pages_after = dict(pages_before)
tprod = next(p for p in products if p["id"] == target["id"])
pages_after[target["id"]] = refined_page(tprod, QUERY, facets)
for pid, html in pages_after.items():
    (OUT / "after" / f"{pid}.html").write_text(html, encoding="utf-8")

after = rank(products, pages_after, QUERY)

report = {
    "query": QUERY,
    "parsed_intent_facets": facets,
    "refresh_target": target["id"],
    "before": before,
    "after": after,
    "delta": {
        "target_rank": {
            "before": next(r["rank"] for r in before["results"] if r["id"] == target["id"]),
            "after": next(r["rank"] for r in after["results"] if r["id"] == target["id"]),
        },
        "target_visibility_index": {
            "before": next(r["visibility_index"] for r in before["results"] if r["id"] == target["id"]),
            "after": next(r["visibility_index"] for r in after["results"] if r["id"] == target["id"]),
        },
    },
}
(OUT / "report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

fmt = lambda rr: "\n".join(
    f"  {r['rank']}. {r['name']:<14} index {r['query_rank_index']:>5}  "
    f"(visibility {r['visibility_index']:>5}, intent {r['intent_match']})"
    for r in rr["results"])
print(f"QUERY: {QUERY}\nFACETS: {facets}\n")
print("BEFORE:\n" + fmt(before))
print(f"\nRefresh target: {tprod['name']} ({target['id']})")
print("\nAFTER (only the target page was regenerated):\n" + fmt(after))
print(f"\nDelta: rank {report['delta']['target_rank']['before']} → "
      f"{report['delta']['target_rank']['after']}, visibility "
      f"{report['delta']['target_visibility_index']['before']} → "
      f"{report['delta']['target_visibility_index']['after']}")
print("\nCAVEAT: " + before["caveat"])
