from pathlib import Path, PurePath
from spectrum.main import generate_pixels, parse_hex
from PIL import Image
# from typing import NoReturn

# import pprint
import yaml
import json
import re

source_path = "../schemes/base16"
schemes_path = "../styles/schemes"
settings_path = "../lib/base16bundle_settings.json"
package_path = "../package.json"
readme_path = "../README.md"

def lower_filename(name: str) -> str:
    """Convert scheme name to file name."""
    return name\
        .replace("(", "").replace(")", "")\
        .replace(",", "")\
        .replace("é", "e")\
        .replace(" ", "-").lower()

def lower_keyword(name: str) -> str:
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

    less_filename = lower_filename(yaml_content["name"])
    less_filepath = Path(schemes_path / PurePath(less_filename).with_suffix(".less"))
    spectrum_filepath = Path(schemes_path / PurePath(less_filename).with_suffix(".png"))

    spectrum_colors = []
    less_content = f"//Name: {yaml_content["name"]}\n//Author: {yaml_content["author"]}\n"
    for color in sorted(yaml_content["palette"]):
        color_code = yaml_content["palette"][color].upper()\
            if "#" in yaml_content["palette"][color]\
            else "#" + yaml_content["palette"][color].upper()
        less_content += f"@{yaml_content["system"]}-color-{color}: {color_code};\n"

        color_rgb = parse_hex(yaml_content["palette"][color].strip("#"))
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
        Image.fromarray(spectrum_pixels, mode="RGB").save(spectrum_filepath)
        print(f"Update file: {less_filename}.less")
    else:
        print(f"File is up to date: {less_filename}.less")

    return yaml_content["name"].replace("-", " ").title()

def generate_readme(name_list: list) -> str:
    """Generate README.md file."""
    readme_content = "# Base16 Ultimate Syntax Theme Bundle\n"
    readme_content += "\n![Base16 Banner](https://github.com/Digital-Punishment/base16-ultimate-bundle-syntax/blob/master/banner.png?raw=true)\n"
    readme_content += f"\nA Base16 syntax theme bundle for Pulsar with {len(name_list)} [Base16](https://github.com/tinted-theming/home) color schemes inside.\n"

    readme_content += "\n<details>\n"
    readme_content += "\n<summary>The following Base16 color schemes are included:</summary>\n"

    schemes_list = ""
    for name in name_list:
        author = ""
        scheme_filename = lower_filename(name)
        scheme_path = Path(schemes_path / PurePath(scheme_filename).with_suffix(".less"))
        preview_path = Path(schemes_path / PurePath(scheme_filename).with_suffix(".png"))
        with scheme_path.open(mode = "r") as scheme_file:
            for line in scheme_file:
                if "Author:" in line:
                    author = line.lstrip("/").lstrip(" ").rstrip("\n").removeprefix("Author: ")
        schemes_list += f"\n> ###### {name} (Author: {"Unknown" if author == "" else author}):\n"
        if preview_path.exists():
            schemes_list += f">![name](https://github.com/Digital-Punishment/base16-ultimate-bundle-syntax/blob/master/styles/schemes/{scheme_filename}.png?raw=true)\n"

    readme_content += schemes_list
    readme_content += "\n</details>\n"

    readme_content +="\nEach color scheme can be used in a `Dark` or `Light` style.\n"

    readme_content +="\n## Install Base16 Ultimate Bundle\n"
    readme_content +="\nBase16 Ultimate Bundle can be installed by going to the _Settings_ view (<kbd>Ctrl + ,</kbd>). Select the _Install_ section on the left, hit the _Themes_ button and search for `Base16 Ultimate Bundle` in the search box. Click on _Install_ on the Base16 Ultimate Bundle card.\n"
    readme_content +="\nAlternatively, open a terminal and type in\n"
    readme_content +="\n```\n ppm install base16-ultimate-bundle-syntax \n```\n"
    readme_content +="\nor\n"
    readme_content +="\n```\n pulsar --package install base16-ultimate-bundle-syntax \n```\n"

    readme_content +="\n## Enable Base16 Ultimate Bundle\n"
    readme_content +="\nBase16 Ultimate Bundle can be enabled by going to the _Settings_ view (<kbd>Ctrl + ,</kbd>). Select the _Themes_ section on the left side and choose _Base16 Ultimate Bundle_ from the _Syntax Theme_ drop down menu.\n"

    readme_content +="\n## Change Base16 color scheme\n"
    readme_content +="\nThe `Default Dark` color scheme is loaded by default.\n"
    readme_content +="\nThe scheme can be changed by choosing a different `scheme` from the drop down menu in the `Base16 Ultimate Bundle` _Settings_ view.\n"
    readme_content +="\nMany schemes have `Dark`, `Light` and other variants, but it is also possible to invert text/background colors with `Invert Colors` toggle. This way `Dark` scheme turns into `Light` and vice versa. Most schemes support this feature, but in some cases it may lead to some undesirable effects and color combinations.\n"
    readme_content +="\nAlternatively, the theme can be changed in the Preview Mode. Toggle the _Command Palette_ (<kbd>Ctrl + Shift + P</kbd>). Type in `Base16 Ultimate Bundle Syntax: Select Theme` and choose another theme from the list. While browsing through the list of available themes a live preview of each selected theme is automatically applied to all open files.\n"
    readme_content +="\n![Base16 Syntax Preview](https://github.com/Digital-Punishment/base16-ultimate-bundle-syntax/blob/master/preview.gif?raw=true)\n"

    readme_content +="\n## Credits\n"
    readme_content +="\nThis is a fork of [Base16 Syntax Theme](https://packages.pulsar-edit.dev/packages/base16-syntax) by [Alchiadus](https://github.com/Alchiadus).\n"
    readme_content +="\nThe original [Base16 Theme](https://github.com/chriskempson/base16) is made by [Chris Kempson](http://chriskempson.com).\n"
    readme_content +="\nColor schemes converted from [GitHub Repository](https://github.com/tinted-theming/schemes) maintained by [Tinted Theming](https://github.com/tinted-theming) community.\n"
    # readme_content +="\n\n"

    return readme_content

if __name__ == "__main__":
    schemes = sorted(Path(source_path).glob("*.y*ml"))

    name_list = [convert_scheme(scheme) for scheme in schemes]
    print(f"{len(name_list)} schemes in package")

    with Path(settings_path).open(mode = "r") as settings_file:
        settings_content = json.loads(settings_file.read())
    settings_content["config"]["scheme"]["enum"] = sorted(name_list)
    with Path(settings_path).open(mode = "w") as settings_file:
        json.dump(settings_content, settings_file, indent = 2)

    keywords = {lower_keyword(name) for name in name_list}
    keywords.add("base16")
    with Path(package_path).open(mode = "r") as package_file:
        package_content = json.loads(package_file.read())
    package_content["keywords"] = sorted(keywords)
    with Path(package_path).open(mode = "w") as package_file:
        json.dump(package_content, package_file, indent = 2)

    with Path(readme_path).open(mode = "w") as readme_file:
        readme_file.write(generate_readme(name_list))
