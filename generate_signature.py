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
    req = Request(XML_URL, headers={"User-Agent": "SERVPRO-d2jsp-signature/1.0"})
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
                result[int(parts[0])] = int(parts[1])
            except ValueError:
                pass
    return result

def load_font(size):
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]:
        p = Path(fp)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()

def main():
    raw = fetch_xml()
    root = ET.fromstring(raw)

    wprof = parse_prof(root.findtext("wprof", ""))
    sprof = parse_prof(root.findtext("sprof", ""))

    dagger = wprof.get(0, 0)
    axe = wprof.get(3, 0)
    sword = wprof.get(2, 0)
    transmuting = sprof.get(3, 0)

    img = Image.open(BG).convert("RGBA").resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)

    patches = [
        (126, 118, 138, 133),
        (183, 118, 195, 133),
        (240, 118, 252, 133),
        (299, 118, 311, 133),
    ]
    for box in patches:
        draw.rectangle(box, fill=(8, 8, 8, 255))

    font = load_font(14)
    values = [
        (132, 125, dagger),
        (189, 125, axe),
        (246, 125, sword),
        (305, 125, transmuting),
    ]
    for cx, cy, val in values:
        text = str(val)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=1)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = cx - tw // 2
        y = cy - th // 2 - 1
        draw.text((x, y), text, font=font, fill=(255, 220, 0, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0, 255))

    img.convert("RGB").save(OUT, "PNG", optimize=True)

if __name__ == "__main__":
    main()
