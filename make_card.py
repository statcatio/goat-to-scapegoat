"""
Generate the 1200x630 social preview card from the real aggregates.

The piece is met as a link in a feed, so the card is the first thing anyone
sees. It shows the finding rather than the title alone: the same team, two
finals, one number crossing zero.

    ./.venv/bin/python make_card.py    # writes card.png
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
W, H = 1200, 630
PAPER, INK, INK2 = (239, 243, 227), (28, 26, 20), (91, 86, 71)
RULE, ACCENT, NEG = (200, 205, 185), (60, 110, 159), (158, 74, 52)

BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)

agg = json.loads((ROOT / "data/public/aggregates.json").read_text())
fox22 = agg["datasets"]["fox_arg_fra_2022"]["by_team"]["argentina"]["mean"]
fox26 = agg["datasets"]["fox_arg_spa_2026"]["by_team"]["argentina"]["mean"]
total = sum(d["n_scored"] for d in agg["datasets"].values())

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

M = 72
d.line([(M, 74), (W - M, 74)], fill=INK, width=3)
d.text((M, 44), "THE SCAPEGOAT ALMANAC  ·  NO. 01", font=f(BOLD, 17), fill=INK2)

d.text((M, 118), "FROM GOAT", font=f(BOLD, 82), fill=INK)
d.text((M, 202), "TO SCAPEGOAT", font=f(BOLD, 82), fill=INK)

d.text((M, 312), "Did they change, or did we?", font=f(REG, 30), fill=INK2)

# the two figures, with a zero-centred bar under each
def gauge(x, y, year, opp, val, colour):
    d.text((x, y), str(year), font=f(BOLD, 30), fill=INK)
    d.text((x, y + 38), opp, font=f(REG, 17), fill=INK2)
    bx, by, bw, bh = x, y + 76, 400, 22
    d.rectangle([bx, by, bx + bw, by + bh], fill=(229, 234, 213))
    mid = bx + bw // 2
    w = int(abs(val) * (bw / 2))
    if val >= 0:
        d.rectangle([mid, by, mid + w, by + bh], fill=colour)
    else:
        d.rectangle([mid - w, by, mid, by + bh], fill=colour)
    d.line([(mid, by - 5), (mid, by + bh + 5)], fill=INK, width=2)
    txt = ("+" if val >= 0 else "−") + f"{abs(val):.2f}"
    d.text((bx + bw + 22, by - 6), txt, font=f(BOLD, 34), fill=colour)

gauge(M, 372, 2022, "final · vs France · won", fox22, ACCENT)
gauge(M + 560, 372, 2026, "final · vs Spain · lost", fox26, NEG)

d.line([(M, H - 96), (W - M, H - 96)], fill=RULE, width=2)
d.text((M, H - 74), f"Net sentiment toward Argentina  ·  {total:,} comments scored",
       font=f(REG, 21), fill=INK2)
d.text((W - M - 300, H - 74), "statcatio.github.io", font=f(BOLD, 21), fill=INK2)

out = ROOT / "card.png"
img.save(out, "PNG", optimize=True)
print(f"-> {out}  ({out.stat().st_size/1024:.0f} KB, {W}x{H})")
print(f"   figures drawn from aggregates: {fox22:+.2f} -> {fox26:+.2f}, n={total:,}")
