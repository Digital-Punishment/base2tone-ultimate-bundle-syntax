from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path, PurePath
from typing import NoReturn

import copy
import json
import plistlib
import pprint
import re
import requests
import time

template_urls = [
    "https://raw.githubusercontent.com/atelierbram/Base2Tone-sublime-text/refs/heads/master/db/templates/dark.ejs",
    "https://raw.githubusercontent.com/atelierbram/Base2Tone-sublime-text/refs/heads/master/db/templates/light.ejs",
    "https://raw.githubusercontent.com/atelierbram/Base2Tone-sublime-text/refs/heads/master/db/templates/dark-alt.ejs",
    "https://raw.githubusercontent.com/atelierbram/Base2Tone-sublime-text/refs/heads/master/db/templates/light-alt.ejs",
]

templates_dir = "./templates"
styles_dir = "../styles"

settings_path = "../lib/base2tone_bundle_settings.json"

MAX_AGE = 30 #days

colors_dict = {
    "base2tone-color-baseA0": "A0",
    "base2tone-color-baseA1": "A1",
    "base2tone-color-baseA2": "A2",
    "base2tone-color-baseA3": "A3",
    "base2tone-color-baseA4": "A4",
    "base2tone-color-baseA5": "A5",
    "base2tone-color-baseA6": "A6",
    "base2tone-color-baseA7": "A7",

    "base2tone-color-baseB0": "B0",
    "base2tone-color-baseB1": "B1",
    "base2tone-color-baseB2": "B2",
    "base2tone-color-baseB3": "B3",
    "base2tone-color-baseB4": "B4",
    "base2tone-color-baseB5": "B5",
    "base2tone-color-baseB6": "B6",
    "base2tone-color-baseB7": "B7",

    "base2tone-color-baseC0": "C0",
    "base2tone-color-baseC1": "C1",
    "base2tone-color-baseC2": "C2",
    "base2tone-color-baseC3": "C3",
    "base2tone-color-baseC4": "C4",
    "base2tone-color-baseC5": "C5",
    "base2tone-color-baseC6": "C6",
    "base2tone-color-baseC7": "C7",

    "base2tone-color-baseD0": "D0",
    "base2tone-color-baseD1": "D1",
    "base2tone-color-baseD2": "D2",
    "base2tone-color-baseD3": "D3",
    "base2tone-color-baseD4": "D4",
    "base2tone-color-baseD5": "D5",
    "base2tone-color-baseD6": "D6",
    "base2tone-color-baseD7": "D7",
}
base2tone_dict = {v: k for k, v in colors_dict.items()}

variables_dict ={
    "Variables":                "@syntax-color-variable",
    "Comments":                 "@syntax-color-comment",
    "Constants":                "@syntax-color-constant",

    "Values":                   "@syntax-color-value",
    "Functions":                "@syntax-color-function",
    "Methods":                  "@syntax-color-method",
    "Classes":                  "@syntax-color-class",
    "Keywords":                 "@syntax-color-keyword",
    "Tags":                     "@syntax-color-tag",
    "Attributes":               "@syntax-color-attribute",

    "Strings, Inherited Class": "@syntax-color-string",
}

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


def deep_merge(old: dict, new: dict) -> dict:
    """Recursively merges 'new' into 'old'."""
    result = copy.deepcopy(old)
    for k, v in new.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def parse_ejs_template(theme_data: dict) -> dict:
    """Parse template data from plist."""
    result = {}
    # print("\n---\n")
    result["name"] = theme_data["name"]
    result["author"] = theme_data["author"]

    gutter = {}
    for field in theme_data["gutterSettings"]:
        gutter[field] = less_color(theme_data["gutterSettings"][field])
    result["gutter"] = gutter

    settings = {}
    rules = {}
    syntax_vars = {}
    for i in theme_data["settings"]:
        if "scope" not in i:
            for field in i["settings"]:
                settings[field] = less_color(i["settings"][field])
        else:
            if i["name"] in variables_dict:
                syntax_vars[variables_dict[i["name"]]] = less_color(i["settings"]["foreground"])
            if i["scope"] != "none":
                i_settings = {}
                for setting in i["settings"]:
                    if setting == "foreground":
                        i_settings[setting] = (
                            variables_dict[i["name"]]
                            if i["name"] in variables_dict
                            else less_color(i["settings"][setting])
                        )
                    elif setting == "background":
                        i_settings[setting] = less_color(i["settings"][setting])
                    else:
                        i_settings[setting] = i["settings"][setting]
                for rule in i["scope"].split(", "):
                    new_rules = add_rule(rule.strip(" "), i["name"], i_settings)
                    rules = deep_merge(rules, new_rules)

    #                 print(i["name"], "\n ", rule, "\n", i["settings"], "\n", i_settings)
    #             print("\n---")
    # print("\n---\n")

    result["settings"] = settings
    result["rules"] = rules
    result["syntax_vars"] = syntax_vars

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
    color_match = re.search(r'base\["(\d|\D)(\d|\D)"\]\["hex"\]', text_element)
    if not color_match:
        color_match = re.search(r"{{base(\d|\D)(\d|\D)-hex}}", text_element)
    color_idx = color_match[0] if color_match else "A0"
    if not color_match:
        print("---!!! no match !!!---", text_element)
    color_idx = color_idx.removeprefix('base["').removesuffix('"]["hex"]')
    color_idx = color_idx.removeprefix("{{base").removesuffix("-hex}}")

    return f"@{base2tone_dict[color_idx]}"


def generate_variables(theme : dict, source : str) ->str:
    """Generate "syntax-variables.less" from parsed theme."""
    # useless as it is, but is a good base/reference for a syntax-variables.less file.
    result = ""
    result += f"//{theme["name"]}\n"
    result += f"//Converted from {source}\n"
    result += f"//Original Author: {theme["author"]}\n"

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
    result += "@syntax-color-renamed:                      hsl(hue(blue), saturation(@syntax-cursor-color), lightness(@syntax-cursor-color));\n"
    result += "@syntax-color-added:                        hsl(hue(green), saturation(@syntax-cursor-color), lightness(@syntax-cursor-color));\n"
    result += "@syntax-color-modified:                     hsl(hue(orange), saturation(@syntax-cursor-color), lightness(@syntax-cursor-color));\n"
    result += "@syntax-color-removed:                      hsl(hue(red), saturation(@syntax-cursor-color), lightness(@syntax-cursor-color));\n"

    result += "\n// For language entity colors\n"
    result += f"@syntax-color-variable:                     {theme["syntax_vars"]["@syntax-color-variable"]};\n"
    result += f"@syntax-color-comment:                      {theme["syntax_vars"]["@syntax-color-comment"]};\n"
    result += f"@syntax-color-constant:                     {theme["syntax_vars"]["@syntax-color-constant"]};\n"
    result += "@syntax-color-property:                     @syntax-text-color;\n"
    result += f"@syntax-color-value:                        {theme["syntax_vars"]["@syntax-color-value"]};\n"
    result += f"@syntax-color-function:                     {theme["syntax_vars"]["@syntax-color-function"]};\n"
    result += f"@syntax-color-method:                       {theme["syntax_vars"]["@syntax-color-method"]};\n"
    result += f"@syntax-color-class:                        {theme["syntax_vars"]["@syntax-color-class"]};\n"
    result += f"@syntax-color-keyword:                      {theme["syntax_vars"]["@syntax-color-keyword"]};\n"
    result += f"@syntax-color-tag:                          {theme["syntax_vars"]["@syntax-color-tag"]};\n"
    result += f"@syntax-color-attribute:                    {theme["syntax_vars"]["@syntax-color-attribute"]};\n"
    result += f"@syntax-color-string:                       {theme["syntax_vars"]["@syntax-color-string"]};\n"
    result += "@syntax-color-import:                       @syntax-color-keyword;\n"
    result += "@syntax-color-snippet:                      @syntax-color-string;\n"

    return result


def generate_syntax(theme : dict, source : str) ->str:
    """Generate "syntax.less" from parsed theme."""
    result = ""
    result += f"//{theme["name"]}\n"
    result += f"//Converted from {source}\n"
    result += f"//Original Author: {theme["author"]}\n"

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
        result = f"color: {value};"
    elif setting == "background":
        result = f"background-color: {value};"
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
    style_path = Path(styles_dir) / Path(filename).with_suffix(".less")
    if not Path(style_path.parent).exists():
        Path(style_path.parent).mkdir(parents = True)

    with Path.open(style_path, "w") as style_file:
        style_file.write(content)


def convert_template(template_path : str) -> NoReturn:
    """Convert file from Sublime/Textmate template to Pulsar theme."""
    template_data = get_template(template_path)
    parsed = {}
    style_name = ""
    if len(template_data) != 0:
        # pprint.pp(template_data)
        if PurePath(template_path).suffix == ".ejs":
            parsed = parse_ejs_template(template_data)
        else:
            print("---!!! unknown format !!!---")
        pprint.pp(parsed)

        theme_variables = generate_variables(parsed, template_path)
        theme_syntax = generate_syntax(parsed, template_path)

        # print("\nVariables:\n", theme_variables)
        # print("\nSyntax:\n", theme_syntax)
        style_name = PurePath(template_path).stem
        write_style(theme_variables, style_name + "/syntax-variables")
        write_style(theme_syntax, style_name + "/syntax")
    return style_name


if __name__ == "__main__":
    style_list = [convert_template(style).replace("-", " ").title() for style in template_urls]
    with Path(settings_path).open(mode = "r") as settings_file:
        settings_content = json.loads(settings_file.read())
    settings_content["config"]["style"]["enum"] = sorted(style_list)
    with Path(settings_path).open(mode = "w") as settings_file:
        json.dump(settings_content, settings_file, indent = 2)
