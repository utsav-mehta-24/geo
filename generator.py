"""Page generator: baseline pages and query-personalized refreshed pages.

Everything rendered comes from OBSERVED brand copy (products.json) or is a
deterministic restatement of structured attributes. No prices are rendered in
JSON-LD (café pricing is a synthetic model, Atelier price is unconfirmed —
rule 2: never default to the optimistic value). No ratings/reviews exist, so
none are fabricated.
"""
import json

DOTS = lambda n: "●" * n + "○" * (5 - n)

BASE_URL = "https://kathai.example"   # placeholder domain


# ----------------------------------------------------------------- FAQ build

def build_faqs(p: dict) -> list[tuple[str, str]]:
    """Answerable core FAQs, derived from structured attributes (observed).
    Questions whose answers depend on unconfirmed formulation are excluded
    rather than answered with guesses."""
    faqs = [
        (f"What does {p['name']} taste like?",
         f"{p['taste_profile'].title()}. {p['description']}"),
        (f"How sweet is {p['name']}?",
         f"Sweetness is {p['sweetness']} out of 5, with chocolate intensity "
         f"{p['intensity']} out of 5 and a {p['body'].lower()} body."),
        (f"Should I have {p['name']} with milk or black?",
         f"Both work: have it with {' or '.join(p['have_it']).lower()}."),
        (f"Can I drink {p['name']} iced?",
         ("Yes — it can be served hot or iced."
          if "Iced" in p["serve"] else
          "It is served hot.")),
        (f"When is the best moment for {p['name']}?",
         f"Best enjoyed: {', '.join(p['best_moment']).lower()}."),
        ("How do I prepare it?",
         "Three steps: OPEN your Kathai, POUR the recommended amount of milk "
         "or water, then MELT — heat, mix and enjoy."),
    ]
    return faqs


FAMILY_FAQS = [
    ("Is Kathai good for a family outing?",
     "Yes — the Kathai Atelier is a 90-minute guided hot chocolate session "
     "for up to 15 guests at 100 Feet Road, Indiranagar, Bengaluru, where "
     "your cup is made in front of you and you taste, compare and create a "
     "melt of your own."),
    ("Which flavour should we pick for a group?",
     "Salora (sea salt caramel) is the crowd-favourite comfort pick; Solé "
     "and Moss suit explorers, and Red Noir suits dessert lovers — so a "
     "group can mix across the range."),
]


# -------------------------------------------------------------- JSON-LD

def product_jsonld(p: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["seo"]["h1"],
        "description": p["seo"]["meta_description"],
        "brand": {"@type": "Brand", "name": "KATHAI"},
        "image": [f"{BASE_URL}/img/{p['id']}-pack.jpg",
                  f"{BASE_URL}/img/{p['id']}-hero.jpg"],
        "sku": f"KATHAI-{p['id'].upper()}",
        "url": f"{BASE_URL}/products/{p['seo']['slug']}",
        "category": "Hot Chocolate",
        "isVariantOf": {"@type": "ProductGroup", "name": "KATHAI Hot Chocolate",
                        "productGroupID": "KATHAI-CORE"},
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Chocolate intensity", "value": f"{p['intensity']}/5"},
            {"@type": "PropertyValue", "name": "Sweetness", "value": f"{p['sweetness']}/5"},
            {"@type": "PropertyValue", "name": "Serve", "value": " / ".join(p["serve"])},
        ],
        # NOTE: offers/price intentionally omitted — pricing unvalidated.
        # NOTE: aggregateRating intentionally omitted — no reviews exist.
    }


def faq_jsonld(faqs: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }


def breadcrumb_jsonld(p: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "KATHAI", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": p["collection"].title(),
             "item": f"{BASE_URL}/collections/{p['collection'].lower().replace(' ', '-')}"},
            {"@type": "ListItem", "position": 3, "name": p["name"]},
        ],
    }


# ------------------------------------------------------------------- styles

CSS = """
:root{--choc:#3b2314;--cream:#f6efe7;--gold:#c99b5f;--ink:#241a12}
*{box-sizing:border-box;margin:0}body{font-family:Georgia,'Times New Roman',serif;
background:var(--cream);color:var(--ink);line-height:1.55}
header{background:var(--choc);color:var(--cream);padding:28px 24px}
header .brand{letter-spacing:.35em;font-size:13px;color:var(--gold)}
h1{font-size:30px;margin-top:6px}main{max-width:760px;margin:0 auto;padding:24px}
.hook{font-style:italic;font-size:19px;color:#6b4a2d;margin:14px 0}
.profile{letter-spacing:.18em;font-size:12px;color:var(--gold);font-weight:700}
section{margin:26px 0}h2{font-size:20px;border-bottom:2px solid var(--gold);
padding-bottom:6px;margin-bottom:12px}
.taste-scores td{padding:5px 14px 5px 0;font-size:15px}
.answer-block{background:#fff;border-left:4px solid var(--gold);padding:12px 16px;
margin:10px 0;border-radius:0 8px 8px 0}
.answer-block h3{font-size:15px;margin-bottom:4px}
.occasion{background:var(--choc);color:var(--cream);padding:18px;border-radius:10px}
.occasion h2{color:var(--gold);border-color:var(--gold)}
.prep-steps{display:flex;gap:12px}.prep-steps div{flex:1;background:#fff;
padding:12px;border-radius:8px;text-align:center;font-size:14px}
.gallery{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.gallery img{width:100%;aspect-ratio:1;object-fit:cover;background:#e8dccb;
border-radius:8px}
.vibe{font-size:17px;font-style:italic}.tags span{display:inline-block;
background:#efe3d2;border-radius:20px;padding:3px 12px;font-size:12px;margin:3px}
footer{font-size:12px;color:#8a7762;padding:20px 24px;max-width:760px;margin:0 auto}
"""


def img(p: dict, variant: str, alt: str) -> str:
    return f'<img src="img/{p["id"]}-{variant}.jpg" alt="{alt}" loading="lazy">'


# ------------------------------------------------------------ page builders

def baseline_page(p: dict) -> str:
    """What a naive render of the docx gives you: copy + meta, nothing else."""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{p['seo']['title']}</title>
<meta name="description" content="{p['seo']['meta_description']}">
<style>{CSS}</style></head>
<body><header><div class="brand">KATHAI</div><h1>{p['seo']['h1']}</h1></header>
<main>
<p class="profile">{p['taste_profile']}</p>
<p class="hook">{p['hook']}</p>
{img(p, 'pack', p['seo']['image_alt'])}
<section><p>{p['description']}</p>
<p class="vibe"><strong>The Vibe:</strong> {p['vibe']}</p></section>
<div class="tags">{''.join(f'<span>{t}</span>' for t in p['tags'])}</div>
</main>
<footer>KATHAI · Crafted for your moments.</footer></body></html>"""


def refined_page(p: dict, query: str | None = None,
                 facets: list[str] | None = None) -> str:
    facets = facets or []
    faqs = build_faqs(p)

    # ---- personalization: intent-led blocks come first
    occasion_html = ""
    personal_note = ""
    if "family" in facets or "experience" in facets:
        faqs = FAMILY_FAQS + faqs
        occasion_html = """
<section class="occasion"><h2>Make it a family moment — The KATHAI Atelier</h2>
<p>A 90-minute guided hot chocolate experience for up to 15 guests at
KATHAI, 100 Feet Road, Indiranagar, Bengaluru. Your cup is made in front of
you, cocoa fills the room, and everyone — from the cautious sipper to the
flavour explorer — tastes, compares and creates a melt of their own.</p>
<p><em>Weekend sessions available · booking details on request.</em></p></section>"""
        personal_note = (f"<p class='hook'>Bringing the whole crew? "
                         f"{p['name']} is the cup everyone can agree on — and "
                         f"the Atelier turns it into an experience you do "
                         f"together.</p>")
    if "focus" in facets and "Work Mode" in p["tags"]:
        personal_note = ("<p class='hook'>Deadline mode: this is the cup "
                         "built for it.</p>")

    serves = ""
    if p.get("serves"):
        rows = "".join(f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>"
                       for k, v in p["serves"].items())
        serves = f"<section><h2>Make it yours</h2><table class='taste-scores'>{rows}</table></section>"

    heat = (f"<tr><td><strong>Heat</strong></td><td>{'🌶️' * p['heat']}</td></tr>"
            if p.get("heat") else "")

    lds = [product_jsonld(p), faq_jsonld(faqs), breadcrumb_jsonld(p)]
    ld_html = "\n".join(
        f'<script type="application/ld+json">{json.dumps(l, ensure_ascii=False)}</script>'
        for l in lds)

    faq_html = "".join(
        f'<div class="answer-block"><h3>{q}</h3><p>{a}</p></div>'
        for q, a in faqs)

    gallery = "".join([
        img(p, "pack", p["seo"]["image_alt"]),
        img(p, "hero", f"Finished cup of {p['name']} {p['composition'][0].lower()} hot chocolate showing texture and serving style"),
        img(p, "ingredients", f"Chocolate alongside {', '.join(c.lower() for c in p['composition'][1:]) or 'cocoa'} — the {p['name']} ingredient story"),
        img(p, "lifestyle", f"The mood of {p['name']}: {p['vibe'].rstrip('.')}"),
        img(p, "texture", f"Close-up of {p['name']} hot chocolate texture"),
        img(p, "prep", f"Preparing {p['name']}: open, pour, melt"),
    ])

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{p['seo']['title']}</title>
<meta name="description" content="{p['seo']['meta_description']}">
<link rel="canonical" href="{BASE_URL}/products/{p['seo']['slug']}">
<meta property="og:title" content="{p['seo']['title']}">
<meta property="og:description" content="{p['seo']['meta_description']}">
<meta property="og:image" content="{BASE_URL}/img/{p['id']}-hero.jpg">
{ld_html}
<style>{CSS}</style></head>
<body><header><div class="brand">KATHAI · {p['collection']}</div>
<h1>{p['seo']['h1']}</h1></header>
<main>
<p class="profile">{p['taste_profile']}</p>
<p class="hook">{p['hook']}</p>
{personal_note}
{occasion_html}
<section class="gallery-wrap"><div class="gallery">{gallery}</div></section>
<section><h2>The flavour</h2><p>{p['description']}</p>
<p class="vibe"><strong>The Vibe:</strong> {p['vibe']}</p></section>
<section><h2>Quick taste profile</h2><table class="taste-scores">
<tr><td><strong>Chocolate intensity</strong></td><td>{DOTS(p['intensity'])}</td></tr>
<tr><td><strong>Sweetness</strong></td><td>{DOTS(p['sweetness'])}</td></tr>
<tr><td><strong>Adventure level</strong></td><td>{DOTS(p['adventure'])}</td></tr>
{heat}
<tr><td><strong>Body</strong></td><td>{p['body']}</td></tr>
<tr><td><strong>Have it</strong></td><td>{' / '.join(p['have_it'])}</td></tr>
<tr><td><strong>Best moment</strong></td><td>{' / '.join(p['best_moment'])}</td></tr>
<tr><td><strong>Serve it</strong></td><td>{' / '.join(p['serve'])}</td></tr>
</table></section>
<section class="occasion-wrap"><h2>How to prepare</h2>
<div class="prep-steps"><div><strong>1 · OPEN</strong><br>Open your Kathai.</div>
<div><strong>2 · POUR</strong><br>Add milk or water.</div>
<div><strong>3 · MELT</strong><br>Heat, mix, enjoy.</div></div></section>
{serves}
<section><h2>Questions, answered</h2>{faq_html}</section>
<div class="tags">{''.join(f'<span>{t}</span>' for t in p['tags'])}</div>
</main>
<footer>KATHAI · Crafted for your moments. Nutritional details, caffeine and
protein figures will be published once the final formulation is confirmed.</footer>
</body></html>"""
