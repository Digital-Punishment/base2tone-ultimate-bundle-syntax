from pathlib import Path #, PurePath
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageFilter

import argparse
import json
import re
import semantic_version

# WARNING
# use default font for banner!
# default:
# Menlo, Consolas, DejaVu Sans Mono, monospace
# usual:
# Cartograph CF ML Ligatured CCG, Cascadia Code, Ubuntu Mono

settings_path = "../lib/base2tone_bundle_settings.json"
package_path = "../package.json"
screenshots_path = "./screenshots/"

crop_topleft = (0, 190)
crop_size = (740, 195)

banner_width = 720

ver_regex = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


def create_banner(title: str, version: str, count: int) -> Image:
    """Create banner from screenshots."""
    final_size = (banner_width, int(crop_size[1] * (banner_width / crop_size[0])))
    result = Image.new("RGB", crop_size, 0)

    crop = ( \
        crop_topleft[0], \
        crop_topleft[1], \
        crop_topleft[0] + crop_size[0], \
        crop_topleft[1] + crop_size[1] \
        )

    screenshots = sorted(Path(screenshots_path).glob("*.png"))#[:10]
    mask_size = ([i * 4 for i in crop_size])
    mask_ratio = 1.5
    for index, screenshot in enumerate(screenshots):
        print(f"Processing: {screenshot}")
        img = Image.open(screenshot)
        cropped = img.crop(crop)

        mask = Image.new("L", mask_size, 255) # White background
        draw = ImageDraw.Draw(mask)
        for y in range(mask_size[1]):
            for x in range(mask_size[0]):
                mask_width = (
                    ((mask_size[0] + (mask_size[1] * mask_ratio)) / len(screenshots)) *
                    index
                )
                if (x + mask_ratio * (mask_size[1] - y)) < mask_width:
                    mask.putpixel((x, y), 0) # Black pixel

        mask = mask.resize(crop_size, Image.Resampling.LANCZOS)

        shadow = Image.new("L", crop_size, 0)
        shadowmask = mask.copy().filter(ImageFilter.GaussianBlur(radius = 2.5))

        result.paste(shadow, (0, 0), shadowmask)
        result.paste(cropped, (0, 0), mask)

    shadows = Image.new("RGBA", crop_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadows)

    text_title = title
    text_version = f"Version: {version}"
    text_count = f"{count} color schemes"

    font_title = ImageFont.truetype("RacingSansOne-Regular.ttf", 55)
    font_version = ImageFont.truetype("OpenSans-Regular.ttf", 20)

    hoffset_title = (crop_size[0] - font_title.getlength(text_title)) / 2
    hoffset_version = (crop_size[0] - font_version.getlength(text_version)) / 2
    hoffset_count = (crop_size[0] - font_version.getlength(text_count)) / 2

    voffset_title = 10
    voffset_version = 125
    voffset_count = 155

    text_fill = ImageColor.getrgb("#FBFAF8")
    text_stroke = (26, 25, 24)
    shadow_fill = (0, 0, 0, 150)

    rect_radius = 10

    rect_title = font_title.getbbox(text_title)
    rect_title_off = (\
        rect_title[0] + hoffset_title - rect_radius,\
        rect_title[1] + voffset_title - rect_radius,\
        rect_title[2] + hoffset_title + rect_radius,\
        rect_title[3] + voffset_title + rect_radius\
    )
    rect_version = font_version.getbbox(text_version)
    rect_version_off = (\
        rect_version[0] + hoffset_version - rect_radius,\
        rect_version[1] + voffset_version - rect_radius,\
        rect_version[2] + hoffset_version + rect_radius,\
        rect_version[3] + voffset_version + rect_radius\
    )
    rect_count = font_version.getbbox(text_count)
    rect_count_off = (\
        rect_count[0] + hoffset_count - rect_radius,\
        rect_count[1] + voffset_count - rect_radius,\
        rect_count[2] + hoffset_count + rect_radius,\
        rect_count[3] + voffset_count + rect_radius\
    )

    draw.rounded_rectangle(rect_title_off, radius = rect_radius, fill=shadow_fill)
    draw.rounded_rectangle(rect_version_off, radius = rect_radius, fill=shadow_fill)
    draw.rounded_rectangle(rect_count_off, radius = rect_radius, fill=shadow_fill)

    shadows = shadows.filter(ImageFilter.GaussianBlur(radius = 15))

    overlay = Image.new("RGBA", crop_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.text(
        (hoffset_title, voffset_title),
        text_title,
        fill=text_fill,
        stroke_fill=text_stroke,
        stroke_width=3,
        font=font_title,
    )
    draw.text(
        (hoffset_version, voffset_version),
        text_version,
        fill=text_fill,
        stroke_fill=text_stroke,
        stroke_width=2,
        font=font_version,
    )
    draw.text(
        (hoffset_count, voffset_count),
        text_count,
        fill=text_fill,
        stroke_fill=text_stroke,
        stroke_width=2,
        font=font_version,
    )

    result.paste(shadows, (0, 0), mask = shadows)
    result.paste(overlay, (0, 0), mask = overlay)

    return result.resize(final_size, Image.Resampling.LANCZOS)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Combine screenshots into banner image and adds package name, "
        "version and amount of schemes.",
    )
    parser.add_argument(
        "-v", "--version",
        default = "",
        help = "Version of the package to add to a banner. It can be a version string "
               "in SemVer format (x.y.z) or a string describing next release (major, "
               "minor or patch), in such case version will be bumped automatically.",
    )
    args = parser.parse_args()

    package_name = "Default name"
    scheme_count = 0
    next_ver = "0.0.1"

    with Path(settings_path).open(mode = "r") as settings_file:
        settings_content = json.load(settings_file)
    with Path(package_path).open(mode = "r") as package_file:
        package_content = json.load(package_file)

    package_name = package_content["name"].removesuffix("-syntax").replace("-", " ").title()
    scheme_count = len(settings_content["config"]["scheme"]["enum"])

    if args.version != "":
        if ver_match := re.fullmatch(ver_regex, args.version):
            next_ver = ver_match[0]
            print("Next version: ", next_ver)
        elif args.version in ["major", "minor", "patch"]:
            cur_ver = semantic_version.Version(package_content["version"])
            match args.version:
                case "major":
                    next_ver = str(cur_ver.next_major())
                case "minor":
                    next_ver = str(cur_ver.next_minor())
                case "patch":
                    next_ver = str(cur_ver.next_patch())
            print("Current version: ", str(cur_ver))
            print("Next release: ", args.version)
            print("Next version: ", str(next_ver))
        else:
            print("Incorrect version. See 'make_banner.py -h' for instructions.")
    else:
        print("Please, provide a version. See 'make_banner.py -h' for instructions.")

    print(package_name, next_ver, scheme_count)

    banner = create_banner(package_name, next_ver, scheme_count)
    # banner.show()
    banner.save("../banner.png")
