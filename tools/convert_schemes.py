from pathlib import Path, PurePath
from spectrum.main import generate_pixels, parse_hex
from PIL import Image
# from typing import NoReturn

# import pprint
import yaml
import json
import re

source_path = "./schemes/db/schemes"
schemes_path = "../styles/schemes"
settings_path = "../lib/base2tone_bundle_settings.json"
package_path = "../package.json"
readme_path = "../README.md"

base_name = "Base2Tone"
base_github = "https://github.com/atelierbram/Base2Tone"
theme_github = "https://github.com/Digital-Punishment/base2tone-ultimate-bundle-syntax"

def lower_filename(name: str) -> str:
    """Convert scheme name to file name."""
    return name\
        .replace("(", "").replace(")", "")\
        .replace(",", "")\
        .replace("é", "e")\
        .replace(" ", "-").lower()

def lower_keyword(name: str) -> str:
    """Generate keyword from scheme name."""
    name = re.sub(r"\(\w+\s*\w+\)", "", name)
    return name\
        .lower()\
        .replace(",", "")\
        .replace("é", "e")\
        .replace(" lighter", "")\
        .replace(" light", "")\
        .replace(" darker", "")\
        .replace(" dark", "")\
        .replace(" hard", "")\
        .replace(" medium", "")\
        .replace(" soft", "")\
        .replace(" terminal", "")\
        .replace(" high contrast", "")\
        .replace(" contrast", "")\
        .replace(" plus", "")\
        .replace(" dimmed", "")\
        .replace("  ", " ")\
        .lstrip(" ").rstrip(" ")

def convert_scheme(scheme_path: Path) -> str:
    """Convert yaml scheme to .less scheme."""
    with scheme_path.open(mode = "r") as source_file:
        yaml_content = yaml.safe_load(source_file)

    scheme_name = yaml_content["scheme"].replace("Base2Tone-", "")
    scheme_system = "base2tone"

    less_filename = lower_filename(scheme_name)
    less_filepath = Path(schemes_path / PurePath(less_filename).with_suffix(".less"))
    spectrum_filepath = Path(schemes_path / PurePath(less_filename).with_suffix(".png"))

    spectrum_colors = []
    less_content = f"//Name: {scheme_name}\n//Author: {yaml_content["author"]}\n"
    for color in sorted(yaml_content):
        if "base" in color:
            color_code = yaml_content[color].upper()\
                if "#" in yaml_content[color]\
                else "#" + yaml_content[color].upper()
            less_content += f"@{scheme_system}-color-{color}: {color_code};\n"

            color_rgb = parse_hex(yaml_content[color].strip("#"))
            if color_rgb is not None:
                spectrum_colors.append(color_rgb)

    need_update = False
    if not less_filepath.exists() or not spectrum_filepath.exists():
        need_update = True
    else:
        with less_filepath.open(mode = "r") as less_file:
            less_file_content = less_file.read()
        if less_content != less_file_content:
            need_update = True

    if need_update:
        with less_filepath.open(mode = "w") as less_file:
            less_file.write(less_content)
        spectrum_pixels = generate_pixels(spectrum_colors, 720, 20)
        Image.fromarray(spectrum_pixels).save(spectrum_filepath)
        print(f"Update file: {less_filename}.less")
    else:
        print(f"File is up to date: {less_filename}.less")

    return scheme_name.replace("-", " ").title()

def generate_readme(name_list: list, pack_dict: dict) -> str:
    """Generate README.md file."""
    readme_content = (
        f"# {pack_dict["package_title"]} Syntax Theme\n"

        f"\n![{pack_dict["package_title"]} Banner]"
        f"({theme_github}/blob/master/banner.png?raw=true)\n"

        f"\n{pack_dict["package_title"]} is a syntax theme bundle for Pulsar with "
        f"{len(name_list)} [{base_name}]({base_github}) "
        "color schemes inside.\n"

        "\n<details>\n"
        f"\n<summary>The following {base_name} color schemes are included:</summary>\n"
    )

    schemes_list = ""
    for name in name_list:
        author = ""
        scheme_filename = lower_filename(name)
        scheme_path = Path(schemes_path / PurePath(scheme_filename).with_suffix(".less"))
        preview_path = Path(schemes_path / PurePath(scheme_filename).with_suffix(".png"))
        with scheme_path.open(mode = "r") as scheme_file:
            for line in scheme_file:
                if "Author:" in line:
                    author = line.lstrip("/")\
                    .lstrip(" ")\
                    .rstrip("\n")\
                    .removeprefix("Author: ")

        schemes_list += f"\n> ###### {name} (Author: {"Unknown" if author == "" else author}):\n"
        if preview_path.exists():
            schemes_list += f">![{name}]({theme_github}/blob/master/styles/schemes/{scheme_filename}.png?raw=true)\n"

    readme_content += schemes_list
    readme_content += (
        "\n</details>\n"

        "\nEach color scheme can be used in 4 styles, two _Dark_ and two _Light_.\n"

        f"\n## Install {pack_dict["package_title"]}\n"
        f"\n{pack_dict["package_title"]} can be installed by going to the "
        "_Settings_ view (<kbd>Ctrl + ,</kbd>). Select the _Install_ section on "
        "the left, hit the _Themes_ button and search for "
        f"`{pack_dict["package_title"]}` in the search box. Click on _Install_ "
        f"on the {pack_dict["package_title"]} card.\n"
        "\nAlternatively, open a terminal and type in\n"
        f"\n```\n ppm install {pack_dict["package_name"]} \n```\n"
        "\nor\n"
        f"\n```\n pulsar --package install {pack_dict["package_name"]} \n```\n"

        f"\n## Enable {pack_dict["package_title"]}\n"
        f"\n{pack_dict["package_title"]} can be enabled by going to the _Settings_ "
        "view (<kbd>Ctrl + ,</kbd>). Select the _Themes_ section on the left side "
        f"and choose `{pack_dict["package_title"]}` from the _Syntax Theme_ "
        "drop down menu.\n"

        f"\n## Change {base_name} color scheme\n"
        f"\nThe `{pack_dict["default_scheme"]} ({pack_dict["default_style"]})` "
        "color scheme is loaded by default.\n"
        "\nThe scheme can be changed by choosing a different `scheme` or `style` "
        f"from the drop down menu in the `{pack_dict["package_title"]}` _Settings_ "
        "view.\n"
        "\nAlternatively, the theme can be changed in the Preview Mode. "
        "Toggle the _Command Palette_ (<kbd>Ctrl + Shift + P</kbd>). Type in "
        f"`{pack_dict["package_title"]} Syntax: Select Theme` and choose another "
        "theme from the list. While browsing through the list of available "
        "themes a live preview of each selected theme is automatically applied "
        "to all open files.\n"
        f"\n![{pack_dict["package_title"]} Syntax Preview]"
        f"({theme_github}/blob/master/preview.gif?raw=true)\n"

        "\n## Credits\n"
        "\nThis is a fork of "
        "[Base16 Syntax Theme](https://packages.pulsar-edit.dev/packages/base16-syntax) "
        "by [Alchiadus](https://github.com/Alchiadus).\n"

        "\nOriginal [Base2Tone Theme](https://base2t.one) "
        "is made by [Bram de Haan](https://atelierbramdehaan.nl/) "

        "and is based on "
        "[DuoTone](http://simurai.com/projects/2016/01/01/duotone-themes) themes "
        "by [Simurai](http://simurai.com/) for Atom.\n"
        #"\n\n"
    )

    return readme_content

if __name__ == "__main__":
    schemes = sorted(Path(source_path).glob("*.y*ml"))

    name_list = [convert_scheme(scheme) for scheme in schemes]
    print(f"{len(name_list)} schemes in package")

    with Path(settings_path).open(mode = "r") as settings_file:
        settings_content = json.load(settings_file)
    settings_content["config"]["scheme"]["enum"] = sorted(name_list)
    with Path(settings_path).open(mode = "w") as settings_file:
        json.dump(settings_content, settings_file, indent = 2)
        settings_file.write("\n")

    keywords = {lower_keyword(name) for name in name_list}
    keywords.add("base2tone")
    keywords.add("dark")
    keywords.add("duotone")
    keywords.add("light")
    keywords.add("syntax")
    keywords.add("theme")

    with Path(package_path).open(mode = "r") as package_file:
        package_content = json.load(package_file)
    package_content["keywords"] = sorted(keywords)
    with Path(package_path).open(mode = "w") as package_file:
        json.dump(package_content, package_file, indent = 2)
        package_file.write("\n")

    package_dict = {
        "package_name": package_content["name"],
        "package_title": package_content["name"].removesuffix("-syntax").replace("-", " ").title(),
        "default_scheme": settings_content["config"]["scheme"]["default"],
        "default_style": settings_content["config"]["style"]["default"],
}

    with Path(readme_path).open(mode = "w") as readme_file:
        readme_file.write(generate_readme(name_list, package_dict))
