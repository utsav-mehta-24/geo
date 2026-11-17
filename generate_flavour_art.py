"""Build the eight flavour-specific SVG illustrations used by the demo site."""
from pathlib import Path


ROOT = Path(__file__).parent / "static" / "flavours"

# Original, compact editorial illustrations: each scene pairs a ceramic cup of
# cocoa with the flavour's defining ingredient, using its own palette and motif.
ART = {
    "sole": ("Solé", "#f2d88f", "#4b281d", "#f5e8c9", "#f2c431", "#fff8e8", "lemon", "coconut"),
    "moss": ("Moss", "#c7d1a1", "#34281d", "#e8ead5", "#71834a", "#f5f1dc", "matcha", "leaves"),
    "salora": ("Salora", "#d9a66e", "#44251d", "#f1dfcb", "#bc783e", "#fff1dc", "caramel", "salt"),
    "red-noir": ("Red Noir", "#c57c81", "#241a1c", "#ead1cb", "#ab3343", "#f7e5dd", "strawberry", "berry"),
    "midnight-sun": ("Midnight Sun", "#e5a34c", "#261c1b", "#f0d8b6", "#ed8d1c", "#fff0d4", "orange", "citrus"),
    "rush-e": ("Rush E", "#aa7959", "#241a17", "#e2c6a1", "#75432e", "#f2e3ce", "espresso", "cardamom"),
    "picante": ("Picante", "#c45b3b", "#321c18", "#e6c5ad", "#c93925", "#f5e1cd", "chilli", "pepper"),
    "macro-melt": ("Macro Melt", "#a6a27f", "#3b2a20", "#e2d5bd", "#8c744e", "#f5eddf", "cocoa", "oats"),
}


def svg(name, bg, cocoa, cup, accent, cream, ingredient, garnish):
    fruit = {
        "lemon": '<circle cx="171" cy="168" r="38" fill="#f2c431"/><circle cx="171" cy="168" r="28" fill="#ffe58b"/><path d="M171 140v56M144 154l54 28M144 182l54-28" stroke="#fff8d8" stroke-width="3"/>',
        "matcha": '<path d="M151 194Q135 145 171 119Q207 150 181 196Q169 162 151 194Z" fill="#71834a"/><path d="M157 183l20-47" stroke="#dce3bd" stroke-width="3"/>',
        "caramel": '<path d="M142 131Q157 111 174 130T205 131L194 175Q172 194 150 173Z" fill="#bc783e"/><path d="M150 139q15-13 28 0t21 0" fill="none" stroke="#f1c38c" stroke-width="5"/>',
        "strawberry": '<path d="M171 133C151 116 132 132 142 151L169 190Q173 194 178 187L201 151C211 132 190 117 171 133Z" fill="#ab3343"/><path d="M170 133q-2-17 14-20M170 134q-14-16-24-9" fill="none" stroke="#617348" stroke-width="6"/>',
        "orange": '<circle cx="171" cy="165" r="39" fill="#ed8d1c"/><circle cx="171" cy="165" r="29" fill="#ffc760"/><path d="M171 136v58M142 165h58M151 145l40 40M191 145l-40 40" stroke="#fff0d4" stroke-width="3"/>',
        "espresso": '<ellipse cx="157" cy="163" rx="19" ry="29" transform="rotate(28 157 163)" fill="#75432e"/><ellipse cx="187" cy="169" rx="19" ry="29" transform="rotate(28 187 169)" fill="#8d5638"/><path d="M147 145q12 18 20 35M177 151q12 18 20 35" stroke="#c99a6c" stroke-width="3"/>',
        "chilli": '<path d="M144 137Q174 121 198 142Q182 151 185 173Q169 194 151 177Q167 167 144 137Z" fill="#c93925"/><path d="M144 138q-8-14 4-21" fill="none" stroke="#617348" stroke-width="6"/>',
        "cocoa": '<path d="M171 127C147 135 142 166 171 193C200 166 195 135 171 127Z" fill="#8c744e"/><path d="M171 132v55m0-35q-12-16-21-15m21 29q13-17 21-16" fill="none" stroke="#d9c8a7" stroke-width="3"/>',
    }[ingredient]
    secondary = {
        "coconut": '<path d="M222 178a23 23 0 1 1-46 0a23 23 0 0 1 46 0Z" fill="#76513a"/><path d="M180 178a19 19 0 0 1 38 0Z" fill="#fff4dc"/>',
        "leaves": '<path d="M207 207q-1-42 35-56q1 37-35 56Z" fill="#617348"/><path d="M209 202l26-42" stroke="#dce3bd" stroke-width="3"/>',
        "salt": '<path d="m217 157 5 8-8 4-5-8Zm12 20 5 7-8 5-5-8Zm-21 17 5 8-8 4-5-8Z" fill="#fffaf1"/>',
        "berry": '<circle cx="216" cy="176" r="13" fill="#632b3b"/><circle cx="233" cy="192" r="11" fill="#8c3044"/>',
        "citrus": '<path d="M211 125q18 4 25-11q-17-5-25 11Z" fill="#617348"/><path d="M208 130l24-13" stroke="#d9e0b7" stroke-width="3"/>',
        "cardamom": '<ellipse cx="219" cy="173" rx="8" ry="16" transform="rotate(-28 219 173)" fill="#89905b"/><path d="M213 165l12 16m-15-6 16-5" stroke="#e0d6aa" stroke-width="2"/>',
        "pepper": '<path d="M215 161q-8-16 9-20q14 6 8 19q-8 12-4 24q-18-3-13-23Z" fill="#d34a2e"/>',
        "oats": '<path d="M213 198q2-36 23-53m-17 34-11-9m18-6 12 3m-18 17 13 3" fill="none" stroke="#c8b48c" stroke-width="4" stroke-linecap="round"/>',
    }[garnish]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450" role="img" aria-label="{name} flavour illustration">
<defs><linearGradient id="bg" x2="0.9" y2="1"><stop stop-color="{bg}"/><stop offset="1" stop-color="{cream}"/></linearGradient><linearGradient id="drink" x2="0" y2="1"><stop stop-color="#784735"/><stop offset="1" stop-color="{cocoa}"/></linearGradient><filter id="shadow" x="-.3" y="-.3" width="1.6" height="1.8"><feGaussianBlur stdDeviation="9"/></filter></defs>
<rect width="600" height="450" rx="26" fill="url(#bg)"/><circle cx="300" cy="207" r="153" fill="{accent}" opacity=".13"/><path d="M59 347Q300 307 541 347V450H59Z" fill="{cocoa}" opacity=".08"/>
<ellipse cx="300" cy="345" rx="125" ry="20" fill="{cocoa}" opacity=".18" filter="url(#shadow)"/>
<path d="M252 139q-18-31 0-53m42 52q-16-31 1-53m40 53q-17-30 1-50" fill="none" stroke="{cream}" stroke-width="7" stroke-linecap="round" opacity=".7"/>
<path d="M210 174h178l-19 142q-4 30-34 30h-72q-30 0-34-30Z" fill="{cup}"/><path d="M388 205h26q38 2 27 48q-8 31-45 28" fill="none" stroke="{cup}" stroke-width="18"/><ellipse cx="299" cy="178" rx="89" ry="22" fill="#d7b796"/><ellipse cx="299" cy="176" rx="76" ry="15" fill="url(#drink)"/><path d="M263 176q35-15 71 0q-35 14-71 0Z" fill="{accent}" opacity=".85"/>
<path d="M245 212h108" stroke="#fff" stroke-opacity=".5" stroke-width="3"/><circle cx="269" cy="235" r="4" fill="{cream}" opacity=".65"/><circle cx="338" cy="260" r="3" fill="{cream}" opacity=".65"/>
{fruit}{secondary}<text x="300" y="397" text-anchor="middle" font-family="Georgia,serif" font-size="28" fill="{cocoa}" letter-spacing="2">{name.upper()}</text><text x="300" y="422" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="{cocoa}" opacity=".65" letter-spacing="3">KATHAI · FLAVOUR STUDY</text></svg>'''


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for pid, spec in ART.items():
        (ROOT / f"{pid}.svg").write_text(svg(*spec), encoding="utf-8")
    print(f"Generated {len(ART)} flavour illustrations in {ROOT}")


if __name__ == "__main__":
    main()
