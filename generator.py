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


ATELIER_ADDRESS = "KATHAI, 100 Feet Road, Indiranagar, Bengaluru"

# Five-senses copy from Campaign Deck V4, slide 8 (observed).
ATELIER_SENSES = [
    ("Sight", "Your cup is made in front of you, from pour to finish."),
    ("Smell", "Cocoa melting slowly, filling the room."),
    ("Sound", "A soft soundscape of santoor, bansuri, jal tarang, celesta and piano."),
    ("Touch", "A warm ceramic cup and a slow, velvety texture."),
    ("Taste", "Taste, compare and create a melt of your own."),
]

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


# ------------------------------------------------- intent personalization
# Each facet contributes: a hero line (first matching facet wins), an
# above-the-fold occasion section, and FAQs that go first in FAQPage schema.
# Copy is restated from observed brand material only. Atelier price and
# session timings are unconfirmed in the deck, so neither is rendered.

def _moments(p): return ", ".join(m.lower() for m in p["best_moment"])


def _atelier_section(heading: str) -> str:
    senses = "".join(f"<li><strong>{s}</strong> — {t}</li>" for s, t in ATELIER_SENSES)
    return f"""
<section class="occasion"><h2>{heading}</h2>
<p>A 90-minute guided hot chocolate experience for up to 15 guests at
{ATELIER_ADDRESS}. Everyone — from the cautious sipper to the flavour
explorer — tastes, compares and creates a melt of their own.</p>
<ul class="senses">{senses}</ul>
<p><em>Weekend sessions · booking details on request.</em></p></section>"""


def _section(heading: str, body: str) -> str:
    return f'\n<section class="occasion"><h2>{heading}</h2>{body}</section>'


def _family(p):
    hero = (f"Bringing the whole crew? {p['name']} is the cup everyone can agree on — "
            "and the Atelier turns it into an experience you do together."
            if "Crowd Favourite" in p["tags"] else
            f"Bringing the whole crew? Put {p['name']} ({p['taste_profile'].lower()}) "
            "on the table and let everyone mix across the range.")
    return hero, ("atelier", "Make it a family moment — The KATHAI Atelier"), FAMILY_FAQS


def _experience(p):
    hero = f"Looking for more than a cup? Taste {p['name']} the way it's made — at the KATHAI Atelier."
    faq = ("What happens at the KATHAI Atelier?",
           "A 90-minute guided session for up to 15 guests at " + ATELIER_ADDRESS +
           " that engages all five senses: " +
           " ".join(f"{s}: {t}" for s, t in ATELIER_SENSES))
    return hero, ("atelier", "The KATHAI Atelier — one experience, all five senses"), [faq]


def _gift(p):
    hero = f"Gifting this Diwali? KATHAI is a story in every cup — and {p['name']}'s is: {p['vibe']}"
    body = (f"<p><em>Kathai</em> is the deep, rich brown of fine cacao; <em>katha</em> "
            f"means story. {p['name']} — {p['taste_profile'].lower()} — is a cup with "
            f"its own: {p['hook']}</p><p>To give an experience instead, the KATHAI "
            f"Atelier runs Diwali-weekend sessions at {ATELIER_ADDRESS}. "
            "<em>Session timings and price to be confirmed.</em></p>")
    faq = (f"Why give {p['name']} for Diwali?",
           f"KATHAI means a story in every cup. {p['name']} is "
           f"{p['taste_profile'].lower()}: {p['description']}")
    return hero, ("html", _section("A Diwali story in every cup", body)), [faq]


def _focus(p):
    fits = "Work Mode" in p["tags"] or {"Work", "Study"} & set(p["best_moment"])
    hero = ("Deadline mode: this is the cup built for it." if fits else
            f"Need to focus? {p['name']}'s best moments are {_moments(p)}.")
    caffeine = ("<p><em>Caffeine per serving will be published once the final "
                "formulation is confirmed.</em></p>"
                if "caffeine_per_serving" in p.get("pending", {}) else "")
    body = f"<p>{p['description']}</p><p><strong>The Vibe:</strong> {p['vibe']}</p>{caffeine}"
    faq = (f"When is {p['name']} best for studying or work?",
           f"{p['name']}'s best moments are {_moments(p)}. Chocolate intensity "
           f"{p['intensity']}/5, body: {p['body'].lower()}.")
    return hero, ("html", _section("Your lock-in cup", body)), [faq]


def _calm(p):
    hero = f"Slowing down? {p['name']}: {p['vibe']}"
    body = (f"<p>{p['description']}</p><p>Sweetness {p['sweetness']}/5 · "
            f"{p['body']} body · best for {_moments(p)}.</p>")
    faq = (f"Is {p['name']} a calm, slow-moment drink?",
           f"{p['name']} is {p['taste_profile'].lower()}, best for {_moments(p)}. {p['vibe']}")
    return hero, ("html", _section("A slow-moment cup", body)), [faq]


def _adventure(p):
    heat = f" Heat {p['heat']}/3." if p.get("heat") else ""
    hero = f"Want something different? {p['name']} sits at adventure level {p['adventure']}/5."
    body = f"<p>{p['description']}</p><p>Adventure level {DOTS(p['adventure'])}{heat}</p>"
    faq = (f"How adventurous is {p['name']}?",
           f"Adventure level {p['adventure']}/5.{heat} {p['taste_profile'].title()}.")
    return hero, ("html", _section("Something with a kick", body)), [faq]


def _dessert(p):
    hero = f"Dessert mode: {p['name']} — {p['taste_profile'].lower()}."
    dessert = (p.get("serves") or {}).get("Dessert Mode")
    extra = f"<p><strong>Dessert Mode:</strong> {dessert}</p>" if dessert else ""
    body = f"<p>{p['description']}</p><p>Sweetness {DOTS(p['sweetness'])}</p>{extra}"
    faq = (f"Is {p['name']} good as a dessert drink?",
           f"Sweetness is {p['sweetness']}/5 and its best moments are {_moments(p)}."
           + (f" Try Dessert Mode: {dessert}." if dessert else ""))
    return hero, ("html", _section("Dessert mode", body)), [faq]


def _fitness(p):
    protein_pending = "protein_per_serving" in p.get("pending", {})
    hero = (f"After the gym? {p['name']} is KATHAI's protein-oriented hot chocolate — "
            "hitting your macros doesn't have to taste like punishment."
            if "Protein" in p["tags"] else
            f"After the gym? {p['name']} isn't our protein pick — Macro Melt is.")
    note = ("<p><em>Protein per serving will be published once the final "
            "formulation is confirmed.</em></p>" if protein_pending else "")
    body = f"<p>{p['description']}</p><p>Best moments: {_moments(p)}.</p>{note}"
    faq = (f"Can I have {p['name']} after a workout?",
           f"Its best moments are {_moments(p)}."
           + (" Protein per serving will be published once the final formulation "
              "is confirmed." if protein_pending else ""))
    return hero, ("html", _section("Post-workout", body)), [faq]


def _evening(p):
    hero = f"Evening plans? {p['name']}: {p['vibe']}"
    body = f"<p>{p['description']}</p><p>Best moments: {_moments(p)}.</p>"
    faq = (f"Is {p['name']} an evening drink?",
           f"{p['name']}'s best moments are {_moments(p)}. {p['vibe']}")
    return hero, ("html", _section("After dark", body)), [faq]


FACET_BUILDERS = {
    "family": _family, "experience": _experience, "gift": _gift,
    "focus": _focus, "calm": _calm, "adventure": _adventure,
    "dessert": _dessert, "fitness": _fitness, "evening": _evening,
}


def personalize(p: dict, facets: list[str]) -> tuple[str, str, list]:
    """Return (hero_html, sections_html, intent_faqs) for the query facets."""
    hero, sections, faqs, atelier_done, seen_q = "", [], [], False, set()
    for f in facets:
        h, (kind, payload), fq = FACET_BUILDERS[f](p)
        hero = hero or f"<p class='hook personal'>{h}</p>"
        if kind == "atelier":
            if not atelier_done:
                sections.append(_atelier_section(payload))
                atelier_done = True
        else:
            sections.append(payload)
        for q, a in fq:
            if q not in seen_q:
                seen_q.add(q)
                faqs.append((q, a))
    return hero, "".join(sections), faqs


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
.occasion+.occasion{margin-top:14px}.senses{margin:10px 0 10px 18px;font-size:15px}
.personal{color:var(--choc);font-weight:600}
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

    # ---- personalization: intent-led blocks come first (above the fold,
    # and first in FAQPage schema)
    personal_note, occasion_html, intent_faqs = personalize(p, facets)
    faqs = intent_faqs + faqs

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
