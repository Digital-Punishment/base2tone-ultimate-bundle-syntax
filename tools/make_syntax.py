from datetime import datetime, timezone
from deepmerge import always_merger
from http import HTTPStatus
from pathlib import Path, PurePath
from typing import NoReturn

import json
import plistlib
import pprint
import re
import requests
import time

base16_dark = "https://raw.githubusercontent.com/base16-builder/base16-builder/refs/heads/master/db/templates/textmate/dark.ejs"
base16_light = "https://raw.githubusercontent.com/base16-builder/base16-builder/refs/heads/master/db/templates/textmate/light.ejs"
base16_tinted = "https://raw.githubusercontent.com/tinted-theming/tinted-sublime-text/refs/heads/main/templates/base16-color-scheme.mustache"

templates_dir = "./templates"
styles_dir = "./styles"

MAX_AGE = 30 #days

colors_dict = {
    "black":           "00",
    "very-dark-gray":  "01",
    "dark-gray":       "02",
    "gray":            "03",
    "light-gray":      "04",
    "very-light-gray": "05",
    "almost-white":    "06",
    "white":           "07",

    "red":             "08",
    "orange":          "09",
    "yellow":          "0A",
    "green":           "0B",
    "cyan":            "0C",
    "blue":            "0D",
    "purple":          "0E",
    "brown":           "0F",
}
base16_dict = {v: k for k, v in colors_dict.items()}

lambda i: i.split("_")[1].upper()

def get_template(url : str) -> dict:
    """Get scheme template from github."""
    result = ""

    if not Path(templates_dir).exists():
        Path(templates_dir).mkdir(parents = True)
    template_path = Path(templates_dir) / url.rsplit("/", maxsplit=1)[1]

    template_actual = False
    if Path(template_path).exists():
        t_mtime = Path(template_path).stat().st_mtime
        t_age = datetime.now(timezone.utc) - \
            datetime.fromtimestamp(t_mtime, tz=timezone.utc)
        if t_age.days < MAX_AGE:
            template_actual = True

    if not template_actual:
        print("Downloading fresh template...")
        time.sleep(0.1)
        response = requests.get(url, timeout = 5)
        if response.status_code == HTTPStatus.OK:
            cleaned_content = re.sub(r"({#)(.*\n)*(#})", "", response.text)
            cleaned_content = re.sub(r"(<%-)", "", cleaned_content)
            cleaned_content = re.sub(r"(%>)", "", cleaned_content)
            with Path.open(template_path, "w") as template_file:
                template_file.write(cleaned_content)
        else:
            print("---!!!Github not responding!!!---")

    if Path(template_path).exists():
        with Path.open(template_path, "r") as template_file:
            if PurePath(template_path).suffix == ".ejs":
                result = plistlib.loads(template_file.read())
            elif PurePath(template_path).suffix == ".mustache":
                result = json.loads(template_file.read())
            else:
                result = ""

    return result


def parse_ejs_template(theme_data: dict) -> dict:
    """Parse template data from plist."""
    result = {}
    # print("\n---\n")
    result["name"] = theme_data["name"]

    gutter = {}
    for field in theme_data["gutterSettings"]:
        gutter[field] = less_color(theme_data["gutterSettings"][field])
    result["gutter"] = gutter

    settings = {}
    rules = {}
    for i in theme_data["settings"]:
        if "scope" not in i:
            for field in i["settings"]:
                settings[field] = less_color(i["settings"][field])
        elif i["scope"] != "none":
            i_settings = {}
            for setting in i["settings"]:
                if setting in ["foreground", "background"]:
                    i_settings[setting] = less_color(i["settings"][setting])
                else:
                    i_settings[setting] = i["settings"][setting]
            for rule in i["scope"].split(", "):
                always_merger.merge(
                    rules,
                    add_rule(rule, i["name"], i_settings),
                )

    #             print(i["name"], "\n ", len(rule.split(".")), " ", rule, "\n", i["settings"])
    #             print("\n---")
    # print("\n---\n")

    result["settings"] = settings
    result["rules"] = rules

    return result


def parse_mustache_template(theme_data : dict) -> dict:
    """Parse template data from json."""
    result = {}
    # print("\n---\n")
    result["name"] = theme_data["name"].strip("{").strip("}")

    settings = {}
    for i in theme_data["globals"]:
        if "{{base" in theme_data["globals"][i]:
            settings[i] = less_color(theme_data["globals"][i])
    result["settings"] = settings

    rules = {}
    for i in theme_data["rules"]:
        i_settings = {}
        i_name = i["name"] if "name" in i else i["scope"]
        for setting in i:
            if setting not in ["name", "scope"]:
                if setting in ["foreground", "background"]:
                    i_settings[setting] = less_color(i[setting])
                else:
                    i_settings[setting] = i[setting]
        for rule in i["scope"].split(", "):
            always_merger.merge(rules, add_rule(rule, i_name, i_settings))
    #         print(i_name, "\n ", len(rule.split(".")), " ", rule, "\n", i_settings)
    #         print("\n---")
    # print("\n---\n")
    result["rules"] = rules

    return result


def add_rule(rule_scope : str, rule_name : str, rule_settings : dict) -> dict:
    """Split scope into parts and build nested dict."""
    less_prefix = ""

    if rule_scope.startswith(" - "):                    #exlusion selector
        less_prefix = "-."
        rule_scope = rule_scope.removeprefix(" - ")
    elif rule_scope.startswith(" "):                    #descendant selector
        less_prefix = "_."
        rule_scope = rule_scope.removeprefix(" ")
    elif rule_scope.startswith("."):                    #nested selector
        less_prefix = "&."
        rule_scope = rule_scope.removeprefix(".")
    else:                                               #root parent
        less_prefix = "."

    next_minus = rule_scope.find(" - ") if " - " in rule_scope else len(rule_scope)
    next_space = rule_scope.find(" ") if " " in rule_scope else len(rule_scope)
    next_dot = rule_scope.find(".") if "." in rule_scope else len(rule_scope)
    if next_minus == next_space:
        next_space = len(rule_scope)
    separator = (
        " - "
        if (next_minus <= next_space and next_minus <= next_dot)
        else (" " if (next_space <= next_minus and next_space <= next_dot) else ".")
    )

    scope_current = rule_scope.split(separator)[0]
    scope_next = rule_scope.removeprefix(scope_current)
    result = {}
    if len(scope_next) == 0:
        result[f"{less_prefix}syntax--{scope_current}"] = {}
        result[f"{less_prefix}syntax--{scope_current}"]["rule.name"] = str(rule_name)
        result[f"{less_prefix}syntax--{scope_current}"]["rule.settings"] = rule_settings
    else:
        result[f"{less_prefix}syntax--{scope_current}"] = add_rule(
            scope_next,
            rule_name,
            rule_settings,
        )
    return result


def less_color(text_element : str) -> str:
    """Extract color code from string."""
    #{{base01-hex}} in mustache
    # base["0B"]["hex"] in ejs
    color_match = re.search(r'base\["\d(\d|\D)"\]\["hex"\]', text_element)
    if not color_match:
        color_match = re.search(r"{{base\d(\d|\D)-hex}}", text_element)
    color_idx = color_match[0] if color_match else "0E"
    if not color_match:
        print("---!!! no match !!!---", text_element)
    color_idx = color_idx.removeprefix('base["').removesuffix('"]["hex"]')
    color_idx = color_idx.removeprefix("{{base").removesuffix("-hex}}")

    return f"@{base16_dict[color_idx]};   //@base16-color-base{color_idx}"


def generate_variables(theme : dict, source : str) ->str:
    """Generate "syntax-variables.less" from parsed theme."""
    # useless as it is, but is a good base/reference for a syntax-variables.less file.
    result = ""
    result += f"//{theme["name"]}\n"
    result += f"//Converted from {source}\n"
    result += "\n@import 'colors';\n"

    result += "\n// General colors\n"
    text_color = theme["settings"]["foreground"]
    result += f"@syntax-text-color:                         {text_color};\n"
    cursor_color = theme["settings"]["caret"]
    result += f"@syntax-cursor-color:                       {cursor_color};\n"
    selection_color = theme["settings"]["selection"]
    result += f"@syntax-selection-color:                    {selection_color};\n"
    selection_flash_color = theme["settings"]["foreground"]
    result += f"@syntax-selection-flash-color:              {selection_flash_color};\n"
    background_color = theme["settings"]["background"]
    result += f"@syntax-background-color:                   {background_color};\n"

    result += "\n// Guide colors\n"
    wrap_guide_color = theme["settings"]["guide"] \
                       if "guide" in theme["settings"] \
                       else theme["settings"]["selection"]
    result += f"@syntax-wrap-guide-color:                   {wrap_guide_color};\n"
    indent_guide_color = theme["settings"]["guide"] \
                         if "guide" in theme["settings"] \
                         else theme["settings"]["selection"]
    result += f"@syntax-indent-guide-color:                 {indent_guide_color};\n"
    invisible_character_color = theme["settings"]["invisibles"]
    result += f"@syntax-invisible-character-color:          {invisible_character_color};\n"

    result += "\n// For find and replace markers\n"
    result_marker_color = theme["settings"]["find_highlight"] \
                          if "find_highlight" in theme["settings"] \
                          else theme["settings"]["selection"]
    result += f"@syntax-result-marker-color:                {result_marker_color};\n"
    result_marker_selected_color = theme["settings"]["foreground"]
    result += f"@syntax-result-marker-color-selected:       {result_marker_selected_color};\n"

    result += "\n// Gutter colors\n"
    gutter_text_color = theme["gutter"]["foreground"] \
                        if "gutter" in theme \
                        else theme["settings"]["gutter_foreground"]
    result += f"@syntax-gutter-text-color:                  {gutter_text_color};\n"
    gutter_text_selected_color = theme["gutter"]["selectionForeground"] \
                                 if "gutter" in theme \
                                 else theme["settings"]["caret"]
    result += f"@syntax-gutter-text-color-selected:         {gutter_text_selected_color};\n"
    gutter_background_color = theme["gutter"]["background"] \
                              if "gutter" in theme \
                              else theme["settings"]["gutter"]
    result += f"@syntax-gutter-background-color:            {gutter_background_color};\n"
    gutter_background_selected_color = theme["gutter"]["selectionBackground"] \
                                       if "gutter" in theme \
                                       else theme["settings"]["foreground"]
    result += f"@syntax-gutter-background-color-selected:   {gutter_background_selected_color};\n"

    result += "\n// For git diff info. i.e. in the gutter\n"
    result += "@syntax-color-renamed:                      @blue;                      //@base16-color-base0D;\n"
    result += "@syntax-color-added:                        @green;                     //@base16-color-base0B;\n"
    result += "@syntax-color-modified:                     @orange;                    //@base16-color-base09;\n"
    result += "@syntax-color-removed:                      @red;                       //@base16-color-base08;\n"

    result += "\n// For language entity colors\n"
    result += "@syntax-color-variable:                     @red;                       //@base16-color-base08;\n"
    result += "@syntax-color-comment:                      @green;                     //@base16-color-base0B;\n"
    result += "@syntax-color-constant:                     @orange;                    //@base16-color-base09;\n"
    result += "@syntax-color-property:                     @syntax-text-color;\n"
    result += "@syntax-color-value:                        @green;                     //@base16-color-base0B;\n"
    result += "@syntax-color-function:                     @blue;                      //@base16-color-base0D;\n"
    result += "@syntax-color-method:                       @syntax-color-function;\n"
    result += "@syntax-color-class:                        @yellow;                    //@base16-color-base0A;\n"
    result += "@syntax-color-keyword:                      @purple;                    //@base16-color-base0E;\n"
    result += "@syntax-color-tag:                          @red;                       //@base16-color-base08;\n"
    result += "@syntax-color-attribute:                    @orange;                    //@base16-color-base09;\n"
    result += "@syntax-color-import:                       @purple;                    //@base16-color-base0E;\n"
    result += "@syntax-color-snippet:                      @green;                     //@base16-color-base0B;\n"
    result += "@syntax-color-string:                       @green;                     //@base16-color-base0B;\n"


    return result


def generate_syntax(theme : dict, source : str) ->str:
    """Generate "syntax.less" from parsed theme."""
    result = ""
    result += f"//{theme["name"]}\n"
    result += f"//Converted from {source}\n"
    result += "\n@import 'colors';\n"

    for rule in sorted(theme["rules"]):
        result += use_rule(theme["rules"][rule], rule, 0)

    return result


def use_rule(rule : dict, rule_scope : str, indentation : int) -> str:
    """Generate .less rules from dict."""
    # print(rule)
    result = ""
    is_complex = False
    if "rule.name" in rule:
        result += "\n" + indent(indentation) + f"//{rule["rule.name"]} \n"

    #If there is no other sub-rules, print settings in a block with curled brackets
    if len({k: v for k, v in rule.items() if "rule." not in k}) == 0:
        result += indent(indentation) + f"{rule_scope} {{\n"
        is_complex = True
        for i in sorted(rule):
            if "rule." in i and ".settings" in i:
                for s, v in rule[i].items():
                    result += indent(indentation + 2) + format_setting(s, v, indentation) + "\n"

    #If there is only one sub-rule, combine selector into a single string
    elif len(rule) == 1:
        for i in sorted(rule):
            if "rule." not in i:
                i_scope = i\
                    .replace("&.", ".", count = 1)\
                    .replace("_.", " .", count = 1)\
                    .replace("-.", ":not(.", count = 1)
                if i.startswith("-."):
                    i_scope += ")"
                if rule_scope.endswith(")"):
                    rule_scope = rule_scope.removesuffix(")")
                    i_scope += ")"
                result += use_rule(rule[i], rule_scope + i_scope, indentation)

    else:
        #If there is more than 1 sub-rule, make a block with curled brackets
        if indentation == 0:
            result += "\n"
        result += indent(indentation) + f"{rule_scope} {{\n"
        is_complex = True

        #Some rules have both settings and sub-rules
        for i in sorted(rule):
            if "rule." in i and ".settings" in i:
                for s, v in rule[i].items():
                    result += indent(indentation + 2) + format_setting(s, v, indentation) + "\n"
        for i in sorted(rule):
            if "rule." not in i:
                i_scope = i\
                    .replace("_.", ".", count = 1)\
                    .replace("-.", "&:not(.", count = 1)
                if i.startswith("-."):
                    i_scope += ")"
                if rule_scope.endswith(")"):
                    rule_scope = rule_scope.removesuffix(")")
                    i_scope += ")"
                result += indent(indentation) + use_rule(rule[i], i_scope, indentation + 2)

    #Close brackets as needed
    if is_complex:
        result += indent(indentation) + "}\n"

    return result

def indent(indentation: int) -> str:
    """Generate indentation string with spaces."""
    return (" " * indentation)

def format_setting(setting: str, value: str, indentation: int) -> str:
    """Format each css attribute."""
    result = ""
    if setting == "foreground":
        result = f"color: {value}"
    elif setting == "background":
        result = f"background-color: {value}"
    elif setting in ["font_style", "fontStyle"]:
        newstring = False
        if "bold" in value:
            result += "font-weight: bold;"
            newstring = True
        if "italic" in value:
            if newstring:
                result +="\n" + indent(indentation + 2)
            result += "font-style: italic;"
            newstring = True
        if "normal" in value or value == "":
            if newstring:
                result +="\n" + indent(indentation + 2)
            result += "font-weight: normal;\n" + indent(indentation + 2)
            result += "font-style: normal;"
            newstring = True
        if not newstring:
            print("---!!!unknown fontstyle!!!---")
            print(f"{setting}: {value}\n")
    else:
        result += "//unknown"
        print("---!!!unknown setting!!!---")
        print(f"{setting}: {value}\n")
    return result


def write_style(content : str, filename : str) -> NoReturn:
    """Write .less style to a file."""
    if not Path(styles_dir).exists():
        Path(styles_dir).mkdir(parents = True)
    style_path = Path(styles_dir) / Path(filename).with_suffix(".less")

    with Path.open(style_path, "w") as style_file:
        style_file.write(content)

def convert_template(template_path : str) -> NoReturn:
    """Convert file from Sublime/Textmate template to Pulsar theme."""
    template_data = get_template(template_path)
    parsed = {}
    if len(template_data) != 0:
        # pprint.pp(template_data)
        if PurePath(template_path).suffix == ".ejs":
            parsed = parse_ejs_template(template_data)
        elif PurePath(template_path).suffix == ".mustache":
            parsed = parse_mustache_template(template_data)
        pprint.pp(parsed)
        theme_variables = generate_variables(parsed, template_path)
        theme_syntax = generate_syntax(parsed, template_path)
        # print("\nVariables:\n", theme_variables)
        # print("\nSyntax:\n", theme_syntax)
        write_style(theme_variables, "syntax-variables_" + PurePath(template_path).stem)
        write_style(theme_syntax, "syntax_" + PurePath(template_path).stem)


if __name__ == "__main__":
    convert_template(base16_dark)
    convert_template(base16_light)
    convert_template(base16_tinted)
