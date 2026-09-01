from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CHARACTER / FILE SETTINGS
# ============================================================

XML_URL = "https://ladderslasher.d2jsp.org/xmlChar.php?i=568115"

OUTPUT_WIDTH = 400
OUTPUT_HEIGHT = 150

ROOT = Path(__file__).resolve().parent
BACKGROUND_FILE = ROOT / "assets" / "signature_background.png"
OUTPUT_FILE = ROOT / "signature.png"


# ============================================================
# XML
# ============================================================

def fetch_xml():
    request = Request(
        XML_URL,
        headers={
            "User-Agent": "SERVPRO-d2jsp-LadderSlasher-signature/2.0"
        }
    )

    with urlopen(request, timeout=20) as response:
        return response.read()


# ============================================================
# PROFICIENCY PARSING
# ============================================================

def parse_proficiencies(raw):
    result = {}

    if not raw:
        return result

    for entry in raw.strip().split(";"):

        if not entry:
            continue

        parts = [part.strip() for part in entry.split(",")]

        try:
            prof_id = int(parts[0])
            rank = int(parts[1])

            progress = int(parts[2]) if len(parts) >= 3 else 0

            result[prof_id] = {
                "rank": rank,
                "progress": progress
            }

        except (ValueError, IndexError):
            continue

    return result


def get_prof(data, prof_id):
    return data.get(
        prof_id,
        {
            "rank": 0,
            "progress": 0
        }
    )


# ============================================================
# PROFICIENCY PERCENTAGE
# ============================================================

def requirement_for_next_rank(rank):
    return (rank + 1) * 1000


def percentage_to_next_rank(rank, progress):

    required = requirement_for_next_rank(rank)

    if required <= 0:
        return 0.0

    percentage = (progress / required) * 100

    return max(
        0.0,
        min(percentage, 100.0)
    )


# ============================================================
# FONT HANDLING
# ============================================================

def get_font(size):

    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    ]

    for font_path in possible_fonts:

        if Path(font_path).exists():

            return ImageFont.truetype(
                font_path,
                size=size
            )

    return ImageFont.load_default()


# ============================================================
# TEXT DRAWING
# ============================================================

def draw_centered_text(
    draw,
    center_x,
    y,
    text,
    font,
    fill,
    stroke_width=0,
    stroke_fill=(0, 0, 0, 255)
):

    bounding_box = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=stroke_width
    )

    text_width = (
        bounding_box[2]
        - bounding_box[0]
    )

    x = center_x - (text_width // 2)

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Fetch live Ladder Slasher XML
    # --------------------------------------------------------

    raw_xml = fetch_xml()

    xml = ET.fromstring(raw_xml)


    # --------------------------------------------------------
    # Dynamic character information
    # --------------------------------------------------------

    character_name = xml.findtext(
        "name",
        "SERVPRO"
    )

    character_level = xml.findtext(
        "level",
        "?"
    )

    core_value = xml.findtext(
        "core",
        "0"
    )

    if core_value == "0":
        core_name = "Original"
    else:
        core_name = "Hardcore"


    # --------------------------------------------------------
    # Parse proficiency data
    # --------------------------------------------------------

    weapon_profs = parse_proficiencies(
        xml.findtext("wprof", "")
    )

    skill_profs = parse_proficiencies(
        xml.findtext("sprof", "")
    )


    # --------------------------------------------------------
    # SERVPRO confirmed proficiency mappings
    # --------------------------------------------------------

    dagger = get_prof(
        weapon_profs,
        3
    )

    axe = get_prof(
        weapon_profs,
        2
    )

    sword = get_prof(
        weapon_profs,
        0
    )

    transmuting = get_prof(
        skill_profs,
        3
    )


    proficiencies = [
        dagger,
        axe,
        sword,
        transmuting
    ]


    # --------------------------------------------------------
    # Load background
    # --------------------------------------------------------

    image = Image.open(
        BACKGROUND_FILE
    ).convert("RGBA")

    image = image.resize(
        (
            OUTPUT_WIDTH,
            OUTPUT_HEIGHT
        ),
        Image.Resampling.LANCZOS
    )

    draw = ImageDraw.Draw(
        image
    )


    # --------------------------------------------------------
    # Fonts
    # --------------------------------------------------------

    name_font = get_font(18)

    info_font = get_font(8)

    rank_font = get_font(11)

    percent_font = get_font(7)


    # --------------------------------------------------------
    # Dynamic Character Name
    # --------------------------------------------------------

    draw_centered_text(
        draw,
        210,
        9,
        character_name,
        name_font,
        fill=(255, 220, 0, 255),
        stroke_width=2,
        stroke_fill=(0, 0, 0, 255)
    )


    # --------------------------------------------------------
    # Dynamic Level + Core
    # --------------------------------------------------------

    character_info = (
        f"Level {character_level} | "
        f"Core: {core_name}"
    )

    draw_centered_text(
        draw,
        210,
        31,
        character_info,
        info_font,
        fill=(255, 255, 255, 255),
        stroke_width=1,
        stroke_fill=(0, 0, 0, 255)
    )


    # --------------------------------------------------------
    # Proficiency locations
    #
    # Background should already contain:
    #
    # DAGGER
    # AXE
    # SWORD
    # TRANSMUTING
    #
    # Python only draws rank + percentage.
    # --------------------------------------------------------

    proficiency_centers = [
        132,   # Dagger
        189,   # Axe
        246,   # Sword
        305    # Transmuting
    ]


    # --------------------------------------------------------
    # Draw live ranks + percentages
    # --------------------------------------------------------

    for center_x, proficiency in zip(
        proficiency_centers,
        proficiencies
    ):

        rank = proficiency["rank"]

        progress = proficiency["progress"]

        percentage = percentage_to_next_rank(
            rank,
            progress
        )


        # Rank
        draw_centered_text(
            draw,
            center_x,
            104,
            str(rank),
            rank_font,
            fill=(255, 220, 0, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255)
        )


        # Percentage
        percent_text = (
            f"{percentage:.1f}%"
        )

        draw_centered_text(
            draw,
            center_x,
            134,
            percent_text,
            percent_font,
            fill=(255, 255, 255, 255),
            stroke_width=1,
            stroke_fill=(0, 0, 0, 255)
        )


    # --------------------------------------------------------
    # Save finished signature
    # --------------------------------------------------------

    image.convert("RGB").save(
        OUTPUT_FILE,
        "PNG",
        optimize=True
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
