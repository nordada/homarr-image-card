# image-card

One image from Homarr's **Media** library on a board tile, with an optional
title and caption.

```
 below                     over the image
 ┌────────────────┐        ┌────────────────┐
 │                │        │                │
 │     image      │        │     image      │
 │                │        │ ▁▁▁▁▁▁▁▁▁▁▁▁▁▁ │
 ├────────────────┤        │ Shed roof      │
 │ Shed roof      │        │ Course three   │
 │ Course three   │        └────────────────┘
 └────────────────┘
```

No requests, no integrations. Everything comes from the options, so the widget
works on a board with nothing else configured.

## Installing

**Management → Custom Widgets.** Paste each file into the matching field:

| File | Field |
| --- | --- |
| `template.jsx` | Template |
| `requests.json` | Requests (JSON) |
| `options.json` | Options (JSON) |
| `description.txt` | Description |

Copy each one with `pbcopy`, not by selecting terminal output:

```bash
pbcopy < template.jsx
```

`template.jsx` is **one line** and 8043 characters. Copying it out of a pager,
a wrapped terminal or a diff view can insert real newlines mid-expression, and
the workbench then rejects it with an `Unexpected token` at whatever line the
break landed on.

`requests.json` is `{}`. The schema still requires a source named `default`, so
set one up in the workbench pointing at this Homarr; nothing ever calls it.

## Choosing the image

The `image` option uses `control: "icon"`, which renders Homarr's icon picker:
it searches the Media library, shows thumbnails, uploads a new file in place,
and accepts a typed image URL for something hosted elsewhere. What it stores is
a URL.

**Homarr renders that one control without its label or description.** Every
other control gets both. So the picker appears at the top of the settings as an
unlabelled box, and the description written for it is never shown. That is why
the empty state on the tile explains where the picker is. It is a gap in
`widget-custom-widget-configuration-input.tsx`, which spreads `common` into
every control except this one, not something the definition can fix.

An upload lives in the database and is served from `/api/user-medias/<id>`.
**That route has no session check**: anything that can reach Homarr can fetch
the file if it knows the id. Fine for a logo or a photo of the shed, worth
knowing before putting something private on a board.

## Options

| Option | Control | Default | What it does |
| --- | --- | --- | --- |
| `image` | icon | empty | The image. Unlabelled picker at the top |
| `title` | text | empty | Empty hides it |
| `caption` | textarea | empty | Empty hides it |
| `textPlacement` | select | below | below, over the image, hidden |
| `fit` | select | cover | cover, contain, fill, scale-down, none |
| `focalPoint` | select | centre | Which part survives cropping |
| `aspectRatio` | select | fill the tile | 16:9, 3:2, 4:3, 1:1, 3:4, 9:16, 21:9 |
| `radius` | select | md | Corner rounding |
| `withBorder` | switch | off | Outline in the theme's border colour |
| `padding` | slider | 8 | Tile edge to image, in pixels |
| `imageOpacity` | slider | 100 | Fades the image. Ignored over the image |
| `align` | select | left | Title and caption together |
| `titleSize` | select | sm | |
| `boldTitle` | switch | on | |
| `captionSize` | select | xs | |
| `captionLines` | slider | 0 | Clamp with an ellipsis. 0 shows all |
| `scrim` | switch | on | Dark gradient behind overlaid text |
| `linkUrl` | text | empty | Makes the image clickable |
| `linkNewTab` | switch | on | |
| `altText` | text | empty | Falls back to the title |

`hidden` placement keeps whatever is typed in `title` and `caption`, so
switching back restores them.

**Every select stores a string, including the numeric ones.** `aspectRatio`
holds `"1.7778"` and `radius` holds `"0"`, converted in the template. Homarr's
option validator rejects a non-string value on any control outside `number`,
`slider`, `duration`, `switch`, `multiSelect` and `json`, and it checks the
declared default as well, so a numeric choice fails on save with
`options.aspectRatio.default Expected text`. `build-template.py` now applies
the same rule and names the option.

## Editing

`template.jsx` is generated. Edit `build-template.py` and re-run it:

```bash
python3 build-template.py
```

Then render it through Homarr's actual interpreter, against current source and
against the build this instance runs:

```bash
bash tools/sandbox-check.sh release/v2
bash tools/sandbox-check.sh 3aa14e22
```

It fetches Homarr's `packages/custom-widgets` at that ref, bundles the real
Custom JSX interpreter and renders the template through it once per case in
`sandbox-cases.json`. No Homarr instance needed. Everything lands in
`.sandbox-check/`, gitignored.

Both refs matter. Before `47f6c1cc` (2026-09-24) the sandbox implements `==`
and `!=` as `String(left) === String(right)`, so `undefined != null` is true
and a `!= null` guard takes the wrong branch. Every fallback here uses `||` and
every comparison is `===` for that reason.

The sandbox notes in
[homarr-tagged-apps](https://github.com/nordada/homarr-tagged-apps) cover the
rest: silent failures, blocked props, what spends the render budget, and the
resource limits. They describe the runtime rather than either widget, and this
one was written against them.

## Licence

GPL-3.0. See [LICENSE](LICENSE).

## Things worth knowing about images specifically

- **`src` takes a root-relative path or an http/https URL.** `data:` URIs and
  protocol-relative `//host/x` are rejected as unsafe, which shows as an
  `INVALID_PROP_VALUE` warning and an `Image` with no `src`.
- **CSS `url(...)` is stripped out of any `style` prop**, so a background image
  has to come from the `BackgroundImage` component, which is what the overlay
  placement uses.
- **`position`, `top`, `left`, `inset` and `zIndex` are blocked**, so text
  cannot be placed at an arbitrary point on the image. Overlaid text sits in a
  flex column at the bottom, and that is the only option.
- **`filter` is blocked too**, so no greyscale or blur. `opacity` works.
