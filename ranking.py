"""AI-visibility ranking engine.

Scores a rendered product page on the structural signals that answer engines
(AI search / assistants) actually consume, then conditions the ranking on a
user query intent. Scores are ordinal indices (see provenance.readiness_caveat).

Signals scored FROM THE PAGE PAYLOAD, not from what we intended to render —
same principle as grounding rule 4: check the payload, not the prompt.
"""
import json
import re
from dataclasses import dataclass, field

from provenance import Provenance, readiness_caveat, claim_is_blocked


# ---------------------------------------------------------------- extraction

def extract_jsonld(html: str) -> list[dict]:
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    out = []
    for b in blocks:
        try:
            out.append(json.loads(b))
        except json.JSONDecodeError:
            pass
    return out


def extract_signals(html: str) -> dict:
    lds = extract_jsonld(html)
    types = {ld.get("@type") for ld in lds}
    product_ld = next((l for l in lds if l.get("@type") == "Product"), None)
    faq_ld = next((l for l in lds if l.get("@type") == "FAQPage"), None)

    imgs = re.findall(r"<img\b[^>]*>", html)
    alts = [re.search(r'alt="([^"]*)"', i) for i in imgs]
    alt_ok = sum(1 for a in alts if a and len(a.group(1)) > 10)

    return {
        "jsonld_types": types,
        "product_ld": product_ld,
        "faq_ld": faq_ld,
        "faq_count": len((faq_ld or {}).get("mainEntity", [])),
        "images": len(imgs),
        "images_with_alt": alt_ok,
        "has_direct_answer_blocks": bool(
            re.search(r'class="answer-block"', html)),
        "has_taste_scores": bool(re.search(r'class="taste-scores"', html)),
        "has_occasion_block": bool(re.search(r'class="occasion"', html)),
        "has_prep_steps": bool(re.search(r'class="prep-steps"', html)),
        "has_breadcrumb": "BreadcrumbList" in types,
        "word_count": len(re.sub(r"<[^>]+>", " ", html).split()),
        "html": html,
    }


# ------------------------------------------------------------------- scoring

@dataclass
class ScoreCard:
    product_id: str
    structured_data: float = 0   # /30
    faq_coverage: float = 0      # /20
    answerability: float = 0     # /25
    media: float = 0             # /15
    claim_safety: float = 0      # /10
    notes: list = field(default_factory=list)
    provenance: str = Provenance.INFERRED.value

    @property
    def visibility_index(self) -> float:
        return round(self.structured_data + self.faq_coverage
                     + self.answerability + self.media + self.claim_safety, 1)


def score_page(product_id: str, html: str) -> ScoreCard:
    s = extract_signals(html)
    card = ScoreCard(product_id)

    # 1. Structured data (/30)
    pts = 0
    p = s["product_ld"]
    if p:
        pts += 8
        for k, v in (("description", 4), ("brand", 3), ("offers", 4),
                     ("image", 3)):
            if p.get(k):
                pts += v
        if claim_is_blocked(json.dumps(p)):
            card.notes.append("BLOCKED claim found in Product JSON-LD")
            pts = max(0, pts - 10)
    else:
        card.notes.append("no Product JSON-LD")
    if s["faq_ld"]:
        pts += 5
    if s["has_breadcrumb"]:
        pts += 3
    card.structured_data = min(pts, 30)

    # 2. FAQ coverage (/20) — rewards real Q&A pairs, capped at 8
    card.faq_coverage = min(s["faq_count"], 8) * 2.5
    if s["faq_count"] == 0:
        card.notes.append("no FAQ schema — answer engines get nothing quotable")

    # 3. Answerability (/25) — direct-answer content blocks
    pts = 0
    pts += 7 if s["has_direct_answer_blocks"] else 0
    pts += 5 if s["has_taste_scores"] else 0
    pts += 5 if s["has_occasion_block"] else 0
    pts += 4 if s["has_prep_steps"] else 0
    pts += 4 if s["word_count"] >= 250 else 2 if s["word_count"] >= 120 else 0
    card.answerability = min(pts, 25)

    # 4. Media (/15) — against the six-part visual standard
    pts = min(s["images"], 6) * 1.5
    pts += min(s["images_with_alt"], 6) * 1.0
    card.media = min(pts, 15)

    # 5. Claim safety (/10) — start full, deduct for unsubstantiated claims
    pts = 10
    body_text = re.sub(r"<script.*?</script>", "", s["html"], flags=re.S)
    for claim in ("high protein", "low sugar", "preservative-free"):
        if claim in body_text.lower():
            pts -= 4
            card.notes.append(f"unsubstantiated claim on page: '{claim}'")
    if "aggregateRating" in s["html"] or '"Review"' in s["html"]:
        pts -= 10
        card.notes.append("FABRICATED rating/review markup — remove")
    card.claim_safety = max(pts, 0)
    return card


# ------------------------------------------------------- intent conditioning

INTENT_FACETS = {
    "family":     {"keywords": ["family", "kids", "parents", "together", "group"],
                   "matches": {"tags": ["Comfort", "Crowd Favourite", "Dessert-Inspired", "Sweet + Salty"],
                               "best_moment": ["Anytime", "Dessert"],
                               "adventure_max": 3}},
    "experience": {"keywords": ["experience", "atelier", "session", "workshop", "event", "do together"],
                   "matches": {"atelier": True}},
    "gift":       {"keywords": ["gift", "diwali", "present", "hamper"],
                   "matches": {"tags": ["Comfort", "Crowd Favourite"]}},
    "focus":      {"keywords": ["study", "work", "deadline", "focus", "awake", "energy"],
                   "matches": {"tags": ["Work Mode", "Espresso", "Bold"], "best_moment": ["Work", "Study"]}},
    "calm":       {"keywords": ["relax", "calm", "quiet", "unwind", "slow"],
                   "matches": {"tags": ["Calm", "Ritual", "Earthy"]}},
    "adventure":  {"keywords": ["spicy", "different", "new", "adventurous", "kick"],
                   "matches": {"tags": ["Adventurous", "Spicy", "Unexpected Pairing"], "adventure_min": 4}},
    "dessert":    {"keywords": ["dessert", "sweet", "treat", "indulgent"],
                   "matches": {"tags": ["Dessert", "Dessert-Inspired", "Caramel"], "sweetness_min": 3}},
    "fitness":    {"keywords": ["protein", "workout", "gym", "macros", "fitness"],
                   "matches": {"tags": ["Protein", "Post-Workout", "Functional"]}},
    "evening":    {"keywords": ["evening", "night", "date"],
                   "matches": {"tags": ["Date Night", "After Dark"], "best_moment": ["Evening"]}},
}


def parse_intent(query: str) -> list[str]:
    q = query.lower()
    return [f for f, spec in INTENT_FACETS.items()
            if any(k in q for k in spec["keywords"])]


def intent_match(product: dict, facets: list[str]) -> tuple[float, list[str]]:
    """0–1 match of a product against parsed intent facets, with reasons."""
    if not facets:
        return 0.5, ["no intent facets parsed — neutral"]
    hits, reasons = 0.0, []
    for f in facets:
        m = INTENT_FACETS[f]["matches"]
        fh = 0.0
        if set(m.get("tags", [])) & set(product.get("tags", [])):
            fh = 1.0
            reasons.append(f"{f}: tag match {sorted(set(m['tags']) & set(product['tags']))}")
        if set(m.get("best_moment", [])) & set(product.get("best_moment", [])):
            fh = max(fh, 0.8)
            reasons.append(f"{f}: moment match")
        if "adventure_max" in m and product["adventure"] <= m["adventure_max"]:
            fh = max(fh, 0.6)
        if "adventure_min" in m and product["adventure"] >= m["adventure_min"]:
            fh = max(fh, 0.8)
        if "sweetness_min" in m and product["sweetness"] >= m["sweetness_min"]:
            fh = max(fh, 0.6)
        if m.get("atelier"):   # experience facet: brand-level, every product can
            fh = max(fh, 0.5)  # carry it, but only pages that surface it win —
                               # checked at page level below
        hits += fh
    return round(hits / len(facets), 3), reasons


def page_surfaces_experience(html: str) -> bool:
    return "Atelier" in html


def rank(products: list[dict], pages: dict[str, str], query: str) -> dict:
    """Rank product pages for a query. Returns ordered results + caveat."""
    facets = parse_intent(query)
    rows = []
    for prod in products:
        html = pages[prod["id"]]
        card = score_page(prod["id"], html)
        im, reasons = intent_match(prod, facets)
        # experience intent is only creditable if the PAGE surfaces it
        if "experience" in facets and page_surfaces_experience(html):
            im = min(1.0, im + 0.3)
            reasons.append("experience: page surfaces the Atelier")
        final = round(card.visibility_index * (0.5 + 0.5 * im), 1)
        rows.append({
            "id": prod["id"], "name": prod["name"],
            "visibility_index": card.visibility_index,
            "intent_match": im,
            "query_rank_index": final,
            "breakdown": {
                "structured_data": card.structured_data,
                "faq_coverage": card.faq_coverage,
                "answerability": card.answerability,
                "media": card.media,
                "claim_safety": card.claim_safety,
            },
            "reasons": reasons, "notes": card.notes,
            "provenance": Provenance.INFERRED.value,
        })
    rows.sort(key=lambda r: r["query_rank_index"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return {"query": query, "facets": facets, "results": rows,
            "caveat": readiness_caveat()}
