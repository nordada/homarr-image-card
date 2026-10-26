#!/usr/bin/env python3
"""Emit template.jsx. Edit here, not in the .jsx, which is overwritten.

Rules this file exists to satisfy (see README.md and the sandbox notes in
homarr-tagged-apps):
  * no user-defined functions and no variables, so a value used twice is
    written twice, which is why the image element is emitted from one string
  * == and != are String(left) === String(right) in shipped builds, so
    undefined != null is true. Fallbacks use || and comparisons use ===
  * unlisted props are dropped silently, so every prop here is one
    tools/sandbox-check.sh has rendered on both release/v2 and 3aa14e22
"""
import json
import pathlib

OUT = pathlib.Path(__file__).with_name("template.jsx")
OPTIONS = pathlib.Path(__file__).with_name("options.json")
LIMITS = {"description": 512, "label": 128}

# Mirrors getCustomWidgetOptionValueIssue in Homarr's options-schema.ts. The
# workbench applies it on save, names the path and says only "Expected text".
NUMERIC_CONTROLS = ("number", "slider", "duration")

# Options are read straight from the object rather than bound, since the
# interpreter has no variables and binding through .map() costs AST depth.
PAD = "(options.padding===undefined?8:options.padding)"
# Every select stores a string, even for a numeric choice: the option
# validator rejects any non-string value on a control outside number, slider,
# duration, switch, multiSelect and json, and it runs against the declared
# default too ("options.aspectRatio.default Expected text"). So the numbers are
# declared as text and converted here.
RADIUS = "(options.radius===\"0\"?0:(options.radius||\"md\"))"
RATIO = "Number(options.aspectRatio||0)"
FIT = "(options.fit||\"cover\")"
FOCAL = "(options.focalPoint||\"center\")"
ALIGN = "(options.align||\"left\")"
PLACEMENT = "(options.textPlacement||\"below\")"
OPACITY = "((options.imageOpacity===undefined?100:options.imageOpacity)/100)"
# Under contain the picture keeps its own shape, so the <img> is sized by the
# picture (auto, capped at the box) and the box aligns it from the focal point.
# Every other fit stretches the <img> over the box, where the focal point is
# object-position. Radius and border then follow the picture in both cases.
SIZE = f'{FIT}==="contain"?"auto":"100%"'
JUSTIFY = f'({FOCAL}==="left"?"flex-start":({FOCAL}==="right"?"flex-end":"center"))'
ALIGN_Y = f'({FOCAL}==="top"?"flex-start":({FOCAL}==="bottom"?"flex-end":"center"))'
BORDER = 'options.withBorder===true?"1px solid var(--mantine-color-default-border)":undefined'
SCRIM = ("\"linear-gradient(to top, rgba(0,0,0,0.78) 0%, "
         "rgba(0,0,0,0.45) 45%, rgba(0,0,0,0) 78%)\"")

# One <Image>, emitted twice: once bare and once inside the link. Duplicating
# the element is cheaper than the depth a shared binding would cost.
IMAGE = (
    '<Image src={options.image} '
    'alt={options.altText||options.title||"Image"} '
    f'fit={{{FIT}}} radius={{{RADIUS}}} h={{{SIZE}}} w={{{SIZE}}} '
    f'style={{{{objectPosition:{FOCAL},opacity:{OPACITY},maxWidth:"100%",maxHeight:"100%",'
    f'border:{BORDER}}}}} />'
)

LINKED = (
    f'{{(options.linkUrl||"")===""?({IMAGE}):'
    '(<Anchor href={options.linkUrl} '
    'target={options.linkNewTab===false?"_self":"_blank"} '
    f'display="flex" h="100%" w="100%" style={{{{justifyContent:{JUSTIFY},alignItems:{ALIGN_Y}}}}}>'
    f'{IMAGE}</Anchor>)}}'
)

# AspectRatio holds the shape; "fill the tile" skips it so the image can take
# whatever height the board gives the widget.
FRAMED = (
    f'{{{RATIO}===0?(<Flex h="100%" w="100%" justify={{{JUSTIFY}}} align={{{ALIGN_Y}}}>{LINKED}</Flex>):'
    f'(<AspectRatio ratio={{{RATIO}}}><Flex h="100%" w="100%" justify={{{JUSTIFY}}} align={{{ALIGN_Y}}}>'
    f'{LINKED}</Flex></AspectRatio>)}}'
)

TITLE = (
    '{(options.title||"")===""?null:(<Text '
    'fw={options.boldTitle===false?500:700} '
    'size={options.titleSize||"sm"} '
    f'ta={{{ALIGN}}} '
    'c={PLACEHOLDER_TITLE_COLOR} '
    'style={{lineHeight:1.3,wordBreak:"break-word"}}>{options.title}</Text>)}'
)

CAPTION = (
    '{(options.caption||"")===""?null:(<Text '
    'size={options.captionSize||"xs"} '
    'c={PLACEHOLDER_CAPTION_COLOR} '
    f'ta={{{ALIGN}}} '
    'lineClamp={options.captionLines>0?options.captionLines:undefined} '
    'style={{lineHeight:1.4,wordBreak:"break-word"}}>{options.caption}</Text>)}'
)


def text_block(on_image: bool) -> str:
    """Title and caption. Colours differ because one sits on a photo."""
    title = TITLE.replace("PLACEHOLDER_TITLE_COLOR", '"white"' if on_image else "undefined")
    caption = CAPTION.replace("PLACEHOLDER_CAPTION_COLOR", '"gray.3"' if on_image else '"dimmed"')
    return f'<Stack gap={{2}}>{title}{caption}</Stack>'


# Hidden placement keeps whatever was typed, so the text is dropped here
# rather than in the options, and switching back restores it.
HAS_TEXT = ('((options.title||"")!==""||(options.caption||"")!=="")'
            f'&&{PLACEMENT}!=="hidden"')

# A link cannot go in an option description: every Homarr render path passes
# descriptions as an escaped JSX child, so markdown and HTML render literally.
# An Anchor in the template is the only clickable one, and the empty state is
# the only place it belongs, since a configured widget stops rendering this.
DOCS_URL = "https://github.com/nordada/homarr-image-card"

EMPTY = (
    '<Stack gap={8} p="md" h="100%" justify="center">'
    '<Text fw={700} fz="sm" tt="uppercase" ta="center">No image chosen</Text>'
    '<Text size="sm" c="dimmed" ta="center" style={{lineHeight:1.5}}>'
    'Open this widget\'s settings. The picker at the top lists everything from '
    'Manage, then Media, and uploads a new file in place. It has no label of '
    'its own, which is a Homarr limitation, not a missing setting.'
    '</Text>'
    '<Text size="xs" c="dimmed" ta="center" style={{lineHeight:1.5}}>'
    'A direct image URL can be typed into the same box.'
    '</Text>'
    '<Anchor href="' + DOCS_URL + '" target="_blank" size="xs" ta="center">'
    'Options and setup guide</Anchor>'
    '</Stack>'
)

OVERLAY = (
    '<BackgroundImage src={options.image} '
    f'radius={{{RADIUS}}} h="100%" w="100%" bgp={{{FOCAL}}} bgr="no-repeat" '
    f'bgsz={{{FIT}==="contain"?"contain":"cover"}}>'
    f'<Stack h="100%" w="100%" justify="flex-end" gap={{2}} p={{{PAD}+4}} '
    'style={options.scrim===false?{borderRadius:"inherit"}:'
    f'{{borderRadius:"inherit",backgroundImage:{SCRIM}}}}}>'
    f'{{{HAS_TEXT}?({text_block(True)}):null}}'
    '</Stack>'
    '</BackgroundImage>'
)

STACKED = (
    f'<Stack h="100%" w="100%" gap={{6}} p={{{PAD}}}>'
    f'<Box style={{{{flex:"1 1 auto",minHeight:0}}}}>{FRAMED}</Box>'
    f'{{{HAS_TEXT}?({text_block(False)}):null}}'
    '</Stack>'
)

# In the stacked layout the border is on the <img> itself (see IMAGE), so it
# hugs the picture and stays visible on a themed board whose card already draws
# its own border at the tile edge. Only the overlay, where the image is the
# tile, borders the whole tile.
BORDERED = (
    f'{{{PLACEMENT}==="overlay"?(options.withBorder===true?(<Paper withBorder radius={{{RADIUS}}} '
    f'bg="transparent" h="100%" w="100%" style={{{{overflow:"hidden"}}}}>{OVERLAY}</Paper>):'
    f'({OVERLAY})):({STACKED})}}'
)

TEMPLATE = (
    f'{{(options.image||"")===""?({EMPTY}):(<Box h="100%" w="100%">{BORDERED}</Box>)}}'
)


def option_value_issue(option: dict, value) -> str | None:
    control = option["control"]
    if control in NUMERIC_CONTROLS:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return "expected a number"
        if "min" in option and value < option["min"]:
            return f"below min {option['min']}"
        if "max" in option and value > option["max"]:
            return f"above max {option['max']}"
    elif control == "switch":
        if not isinstance(value, bool):
            return "expected a boolean"
    elif control == "multiSelect":
        if not isinstance(value, list):
            return "expected a list of choices"
    elif control != "json" and not isinstance(value, str):
        return "expected text"
    if control in ("select", "multiSelect") and "choices" in option:
        allowed = [choice["value"] for choice in option["choices"]]
        if value not in allowed:
            return f"not one of the choices {allowed}"
    return None


def check_options() -> int:
    options = json.loads(OPTIONS.read_text())
    for name, option in options.items():
        for field, limit in LIMITS.items():
            value = option.get(field, "")
            if len(value) > limit:
                print(f"options.json: {name}.{field} is {len(value)} characters, limit {limit}")
                return 1
        issue = option_value_issue(option, option["default"])
        if issue:
            print(f"options.json: {name}.default {issue}")
            return 1
        for choice in option.get("choices", []):
            if not isinstance(choice["value"], str):
                print(f"options.json: {name} choice {choice['value']!r} is not text, "
                      "which the option validator rejects on a select")
                return 1
    longest = max((len(o.get("description", "")) for o in options.values()), default=0)
    print(f"options.json: {len(options)} options within limits (longest description {longest}/512)")
    return 0


def main() -> int:
    OUT.write_text(TEMPLATE + "\n")
    balance = {pair[0]: TEMPLATE.count(pair[0]) - TEMPLATE.count(pair[1]) for pair in ("()", "{}", "[]")}
    ok = all(value == 0 for value in balance.values())
    print(f"template.jsx: {len(TEMPLATE)} chars  balance: {balance} -> {'OK' if ok else 'UNBALANCED'}")
    return (0 if ok else 1) or check_options()


if __name__ == "__main__":
    raise SystemExit(main())
