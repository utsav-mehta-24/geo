"""Demo (batch): run one query end to end and write before/after pages.

BEFORE state (seeded, realistic heterogeneous site — a demo scenario):
  - Rush E, Red Noir, Moss and Solé already have structurally refined pages.
  - Everything else, including Salora, is a naive render of the docx copy.
AFTER state:
  - The pipeline picks the best intent-fit product, regenerates its page
    personalized to the query, and re-ranks. Only that one page changes.

For real-time rendering (any query, per request) run `server.py` instead.
Usage:  python demo.py ["your query"]
"""
import json
import sys

from pipeline import BEFORE_PAGES, HERE, run

# Keep the demo usable from Windows terminals that still default to cp1252.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

QUERY = (" ".join(sys.argv[1:]).strip()
         or "I want hot chocolate with my family and need an experience")
OUT = HERE / "out"

report, pages_after = run(QUERY)

for name, pages in (("before", BEFORE_PAGES), ("after", pages_after)):
    (OUT / name).mkdir(parents=True, exist_ok=True)
    for pid, html in pages.items():
        (OUT / name / f"{pid}.html").write_text(html, encoding="utf-8")
(OUT / "report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

fmt = lambda rr: "\n".join(
    f"  {r['rank']}. {r['name']:<14} index {r['query_rank_index']:>5}  "
    f"(visibility {r['visibility_index']:>5}, intent {r['intent_match']})"
    for r in rr["results"])
print(f"QUERY: {QUERY}\nFACETS: {report['parsed_intent_facets']}\n")
print("BEFORE:\n" + fmt(report["before"]))
if report["refreshed"]:
    d = report["delta"]
    print(f"\nRefresh target: {report['refresh_target_name']} ({report['refresh_target']})")
    print("\nAFTER (only the target page was regenerated):\n" + fmt(report["after"]))
    print(f"\nDelta: rank {d['target_rank']['before']} → {d['target_rank']['after']}, "
          f"visibility {d['target_visibility_index']['before']} → "
          f"{d['target_visibility_index']['after']}")
else:
    print("\n" + report["note"])
print(f"\nNOTE: {report['scenario_note']}")
print("CAVEAT: " + report["caveat"])
