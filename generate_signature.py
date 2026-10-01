from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont, ImageOps


# ============================================================
# SERVPRO - LADDER SLASHER DYNAMIC SIGNATURE
# ============================================================

XML_URL = "https://ladderslasher.d2jsp.org/xmlChar.php?i=568115"

OUTPUT_WIDTH = 400
OUTPUT_HEIGHT = 150
MAX_FILE_SIZE = 70 * 1024

ROOT = Path(__file__).resolve().parent

BACKGROUND_FILE = (
    ROOT
    / "assets"
    / "signature_background.png"
)

OUTPUT_FILE = ROOT / "signature.png"


# ============================================================
# FETCH XML
# ============================================================

def fetch_xml():

    request = Request(
        XML_URL,
        headers={
            "User-Agent":
            "SERVPRO-LadderSlasher-Signature/4.0"
        }
    )

    with urlopen(
        request,
        timeout=20
    ) as response:

        return response.read()


# ============================================================
# PARSE PROFICIENCIES
# ============================================================

def parse_proficiencies(raw):

    result = {}

    if not raw:
        return result

    for entry in raw.strip().split(";"):

        if not entry:
            continue

        parts = [
            part.strip()
            for part in entry.split(",")
        ]

        try:

            prof_id = int(parts[0])

            rank = int(parts[1])

            progress = (
                int(parts[2])
                if len(parts) >= 3
                else 0
            )

            result[prof_id] = {
                "rank": rank,
                "progress": progress
            }

        except (ValueError, IndexError):

            continue

    return result


def get_prof(
    data,
    prof_id
):

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


def percentage_to_next_rank(
    rank,
    progress
):

    required = (
        requirement_for_next_rank(
            rank
        )
    )

    if required <= 0:
        return 0.0

    percentage = (
        progress / required
    ) * 100

    return max(
        0.0,
        min(
            percentage,
            100.0
        )
    )


# ============================================================
# FONTS
# ============================================================

def get_font(size):

    possible_fonts = [

        "/usr/share/fonts/truetype/"
        "dejavu/DejaVuSans-Bold.ttf",

        "/usr/share/fonts/truetype/"
        "liberation2/LiberationSans-Bold.ttf"

    ]

    for font_path in possible_fonts:

        if Path(font_path).exists():

            return ImageFont.truetype(
                font_path,
                size=size
            )

    return ImageFont.load_default()


# ============================================================
# CENTER TEXT
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

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=stroke_width
    )

    text_width = (
        bbox[2]
        - bbox[0]
    )

    x = (
        center_x
        - text_width // 2
    )

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill
    )


# ============================================================
# SAVE UNDER 70 KB
# ============================================================

def save_optimized(image):

    final_image = (
        image.convert("RGB")
    )

    for colors in [
        256,
        192,
        160,
        128,
        96,
        64
    ]:

        optimized = (
            final_image.quantize(
                colors=colors,
                method=(
                    Image.Quantize.MEDIANCUT
                ),
                dither=(
                    Image.Dither.FLOYDSTEINBERG
                )
            )
        )

        optimized.save(
            OUTPUT_FILE,
            "PNG",
            optimize=True,
            compress_level=9
        )

        file_size = (
            OUTPUT_FILE.stat().st_size
        )

        print(
            f"{colors} colors: "
            f"{file_size / 1024:.1f} KB"
        )

        if file_size <= MAX_FILE_SIZE:

            print(
                "Signature saved successfully: "
                f"{file_size / 1024:.1f} KB"
            )

            return

    print(
        "Warning: Signature could not "
        "be reduced below 70 KB."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # FETCH LIVE SERVPRO XML
    # --------------------------------------------------------

    raw_xml = fetch_xml()

    xml = ET.fromstring(
        raw_xml
    )


    # --------------------------------------------------------
    # PARSE PROFICIENCIES
    # --------------------------------------------------------

    weapon_profs = (
        parse_proficiencies(
            xml.findtext(
                "wprof",
                ""
            )
        )
    )

    skill_profs = (
        parse_proficiencies(
            xml.findtext(
                "sprof",
                ""
            )
        )
    )


    # --------------------------------------------------------
    # SERVPRO PROFICIENCIES
    #
    # Display order:
    #
    # Sword
    # Axe
    # Dagger
    # Glyphing
    # Transmuting
    # --------------------------------------------------------

    sword = get_prof(
        weapon_profs,
        0
    )

    axe = get_prof(
        weapon_profs,
        2
    )

    dagger = get_prof(
        weapon_profs,
        3
    )

    glyphing = get_prof(
        skill_profs,
        0
    )

    transmuting = get_prof(
        skill_profs,
        3
    )


    proficiencies = [

        sword,

        axe,

        dagger,

        glyphing,

        transmuting

    ]


    # --------------------------------------------------------
    # LOAD BACKGROUND
    # --------------------------------------------------------

    image = (
        Image.open(
            BACKGROUND_FILE
        )
        .convert("RGBA")
    )


    # --------------------------------------------------------
    # FIT BACKGROUND TO 400 x 150
    #
    # This preserves proportions instead of stretching.
    # --------------------------------------------------------

    image = ImageOps.fit(
        image,
        (
            OUTPUT_WIDTH,
            OUTPUT_HEIGHT
        ),
        method=(
            Image.Resampling.LANCZOS
        ),
        centering=(
            0.5,
            0.5
        )
    )


    draw = ImageDraw.Draw(
        image
    )


    # --------------------------------------------------------
    # FONTS
    # --------------------------------------------------------

    rank_font = get_font(10)

    percent_font = get_font(7)


    # --------------------------------------------------------
    # FIVE PROFICIENCY CENTERS
    #
    # Sword
    # Axe
    # Dagger
    # Glyphing
    # Transmuting
    # --------------------------------------------------------

    proficiency_centers = [

        112,    # Sword

        171,    # Axe

        230,    # Dagger

        289,    # Glyphing

        348     # Transmuting

    ]


    # --------------------------------------------------------
    # DRAW LIVE VALUES
    # --------------------------------------------------------

    for center_x, proficiency in zip(
        proficiency_centers,
        proficiencies
    ):

        rank = (
            proficiency["rank"]
        )

        progress = (
            proficiency["progress"]
        )

        percentage = (
            percentage_to_next_rank(
                rank,
                progress
            )
        )


        # ----------------------------------------------------
        # RANK
        # ----------------------------------------------------

        draw_centered_text(
            draw,
            center_x,
            113,
            str(rank),
            rank_font,
            fill=(
                255,
                215,
                0,
                255
            ),
            stroke_width=1,
            stroke_fill=(
                0,
                0,
                0,
                255
            )
        )


        # ----------------------------------------------------
        # PROGRESS PERCENTAGE
        # ----------------------------------------------------

        draw_centered_text(
            draw,
            center_x,
            130,
            f"{percentage:.1f}%",
            percent_font,
            fill=(
                255,
                255,
                255,
                255
            ),
            stroke_width=1,
            stroke_fill=(
                0,
                0,
                0,
                255
            )
        )


    # --------------------------------------------------------
    # SAVE FINAL SIGNATURE
    # --------------------------------------------------------

    save_optimized(
        image
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
