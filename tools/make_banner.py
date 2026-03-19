from pathlib import Path #, PurePath
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import json


settings_path = "../lib/base16bundle_settings.json"
package_path = "../package.json"

banner_size = (820, 205)
final_width = 720
final_size = (final_width, int(banner_size[1] * (final_width / banner_size[0])))
crop_topleft = (240, 190)
mask_size = ([i * 4 for i in banner_size])

banner = Image.new("RGB", banner_size, 0)
crop = ( \
    crop_topleft[0], \
    crop_topleft[1], \
    crop_topleft[0] + banner_size[0], \
    crop_topleft[1] + banner_size[1] \
    )

screenshots = sorted(Path("./screenshots/").glob("*.png"))
for index, screenshot in enumerate(screenshots):
    print(f"Processing: {screenshot}")
    img = Image.open(screenshot)
    cropped = img.crop(crop)

    mask = Image.new("L", mask_size, 255) # White background
    draw = ImageDraw.Draw(mask)
    for y in range(mask_size[1]):
        for x in range(mask_size[0]):
            if (x + 1.5 * (mask_size[1] - y)) < (banner_size[0] * 1.5 / len(screenshots)) * index * 4:
                mask.putpixel((x, y), 0) # Black pixel

    mask = mask.resize(banner_size, Image.Resampling.LANCZOS)

    shadow = Image.new("L", banner_size, 0)
    shadowmask = mask.copy().filter(ImageFilter.GaussianBlur(radius = 3))

    banner.paste(shadow, (0, 0), shadowmask)
    banner.paste(cropped, (0, 0), mask)

shadows = Image.new("RGBA", banner_size, (0, 0, 0, 0))
draw = ImageDraw.Draw(shadows)

with Path(settings_path).open(mode = "r") as settings_file:
    settings_content = json.load(settings_file)
with Path(package_path).open(mode = "r") as package_file:
    package_content = json.load(package_file)

text_title = package_content["name"].removesuffix("-syntax").replace("-", " ").title()
text_version = f"Version: {package_content["version"]}"
text_count = f"{len(settings_content["config"]["scheme"]["enum"])} color schemes"

font_title = ImageFont.truetype("RacingSansOne-Regular.ttf", 65)
font_version = ImageFont.truetype("OpenSans-Regular.ttf", 25)

hoffset_title = (banner_size[0] - font_title.getlength(text_title)) / 2
hoffset_version = (banner_size[0] - font_version.getlength(text_version)) / 2
hoffset_count = (banner_size[0] - font_version.getlength(text_count)) / 2

voffset_title = 10
voffset_version = 130
voffset_count = 160

color_fill = (251, 241, 200)
color_stroke = (26, 25, 24)

rect_radius = 10

rect_title = font_title.getbbox(text_title)
rect_title_offsetted = (\
    rect_title[0] + hoffset_title - rect_radius,\
    rect_title[1] + voffset_title - rect_radius,\
    rect_title[2] + hoffset_title + rect_radius,\
    rect_title[3] + voffset_title + rect_radius\
   )
rect_version = font_version.getbbox(text_version)
rect_version_offsetted = (\
    rect_version[0] + hoffset_version - rect_radius,\
    rect_version[1] + voffset_version - rect_radius,\
    rect_version[2] + hoffset_version + rect_radius,\
    rect_version[3] + voffset_version + rect_radius\
   )
rect_count = font_version.getbbox(text_count)
rect_count_offsetted = (\
    rect_count[0] + hoffset_count - rect_radius,\
    rect_count[1] + voffset_count - rect_radius,\
    rect_count[2] + hoffset_count + rect_radius,\
    rect_count[3] + voffset_count + rect_radius\
   )

draw.rounded_rectangle(rect_title_offsetted, radius = rect_radius, fill=(0, 0, 0, 150))
draw.rounded_rectangle(rect_version_offsetted, radius = rect_radius, fill=(0, 0, 0, 150))
draw.rounded_rectangle(rect_count_offsetted, radius = rect_radius, fill=(0, 0, 0, 150))

shadows = shadows.filter(ImageFilter.GaussianBlur(radius = 15))

overlay = Image.new("RGBA", banner_size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

draw.text((hoffset_title, voffset_title), text_title, fill=color_fill, stroke_fill=color_stroke, stroke_width=3, font=font_title)
draw.text((hoffset_version, voffset_version), text_version, fill=color_fill, stroke_fill=color_stroke, stroke_width=2, font=font_version)
draw.text((hoffset_count, voffset_count), text_count, fill=color_fill, stroke_fill=color_stroke, stroke_width=2, font=font_version)

banner.paste(shadows, (0, 0), mask = shadows)
banner.paste(overlay, (0, 0), mask = overlay)

banner = banner.resize(final_size, Image.Resampling.LANCZOS)

# banner.show()
banner.save("../banner.png")
