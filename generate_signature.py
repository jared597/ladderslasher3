from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

XML_URL = "https://ladderslasher.d2jsp.org/xmlChar.php?i=568115"
OUT_W, OUT_H = 400, 150

ROOT = Path(__file__).resolve().parent
BG = ROOT / "assets" / "signature_background.png"
OUT = ROOT / "signature.png"

def fetch_xml():
    req = Request(XML_URL, headers={"User-Agent": "SERVPRO-d2jsp-signature/2.0"})
    with urlopen(req, timeout=20) as r:
        return r.read()

def parse_prof(raw):
    result = {}
    if not raw:
        return result
    for entry in raw.strip().split(";"):
        if not entry:
            continue
        parts = [p.strip() for p in entry.split(",")]
        if len(parts) >= 2:
            try:
                prof_id = int(parts[0])
                rank = int(parts[1])
                progress = int(parts[2]) if len(parts) >= 3 else 0
                result[prof_id] = {"rank": rank, "progress": progress}
            except ValueError:
                pass
    return result

def requirement_for_rank(rank):
    return (rank + 1) * 1000

def percent_to_next(rank, progress):
    required = requirement_for_rank(rank)
    if required <= 0:
        return 0.0
    return max(0.0, min((progress / required) * 100.0, 100.0))

def get_prof(data, prof_id):
    return data.get(prof_id, {"rank": 0, "progress": 0})

def load_font(size):
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]:
        p = Path(fp)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()

def draw_centered(draw, center_x, y, text, font, fill, stroke=0, stroke_fill=(0,0,0,255)):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    width = bbox[2] - bbox[0]
    draw.text((center_x - width // 2, y), text, font=font, fill=fill,
              stroke_width=stroke, stroke_fill=stroke_fill)

def main():
    raw = fetch_xml()
    xml_root = ET.fromstring(raw)

    wprof = parse_prof(xml_root.findtext("wprof", ""))
    sprof = parse_prof(xml_root.findtext("sprof", ""))

    sword = get_prof(wprof, 0)
    axe = get_prof(wprof, 2)
    dagger = get_prof(wprof, 3)
    transmuting = get_prof(sprof, 3)

    items = [dagger, axe, sword, transmuting]

    img = Image.open(BG).convert("RGBA").resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)

    patches = [
        (126, 118, 141, 134),
        (183, 118, 198, 134),
        (240, 118, 255, 134),
        (299, 118, 314, 134),
    ]
    for box in patches:
        draw.rectangle(box, fill=(8, 8, 8, 255))

    rank_font = load_font(13)
    pct_font = load_font(8)
    centers = [132, 189, 246, 305]

    for center_x, prof in zip(centers, items):
        rank = prof["rank"]
        progress = prof["progress"]
        pct = percent_to_next(rank, progress)

        draw_centered(
            draw, center_x, 119, str(rank), rank_font,
            fill=(255, 220, 0, 255), stroke=2, stroke_fill=(0, 0, 0, 255)
        )

        draw_centered(
            draw, center_x, 135, f"{pct:.1f}%", pct_font,
            fill=(255, 255, 255, 255), stroke=1, stroke_fill=(0, 0, 0, 255)
        )

    img.convert("RGB").save(OUT, "PNG", optimize=True)

if __name__ == "__main__":
    main()
