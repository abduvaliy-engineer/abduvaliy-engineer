"""Small SVG helpers shared by every drawing. Standard library only."""
from html import escape

FONT = ("ui-monospace,'SFMono-Regular','JetBrains Mono','Cascadia Mono',Menlo,"
        "Consolas,'DejaVu Sans Mono','Liberation Mono',monospace")
ADVANCE = 0.62  # monospace advance per font-size unit, on the generous side

# GitHub linguist colours for the languages that show up on this profile.
LANG = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Shell": "#89e051", "C": "#555555", "C#": "#178600", "QML": "#44a51c",
    "Ruby": "#701516", "Lua": "#000080", "MDX": "#fcb32c", "CSS": "#663399",
    "HTML": "#e34c26", "Dart": "#00B4AB",
}

THEMES = {
    "dark": {
        "name": "dark", "bg": "#0d1117", "card": "#0f151c", "card_hi": "#151d27",
        "border": "#262f3b", "border_hi": "#3b4757", "text": "#e6edf3",
        "muted": "#9aa5b1", "faint": "#6b7683", "accent": "#f2b84b",
        "blue": "#58a6ff", "green": "#3fb950", "red": "#f85149", "purple": "#bc8cff",
        "board_a": "#101c16", "board_b": "#09110d", "board_edge": "#24382d",
        "grid": "#ffffff", "grid_op": 0.045, "silk": "#d5ddd3", "silk_dim": "#8fa395",
        "copper": "#b98b3e", "gold": "#f5c35b", "chip": "#171a1f", "chip_hi": "#2b3038",
        "chip_text": "#eceff2", "chip_muted": "#8d96a0", "pin": "#a7afb9",
        "led_on": "#3fb950", "led_off": "#26332b", "pulse": "#ffd98a", "hole": "#0d1117",
    },
    "light": {
        "name": "light", "bg": "#ffffff", "card": "#f6f8fa", "card_hi": "#ffffff",
        "border": "#d0d7de", "border_hi": "#afb8c1", "text": "#1f2328",
        "muted": "#57606a", "faint": "#8c959f", "accent": "#9a6700",
        "blue": "#0969da", "green": "#1a7f37", "red": "#cf222e", "purple": "#8250df",
        "board_a": "#eef4ec", "board_b": "#dfe9dc", "board_edge": "#c3d2c0",
        "grid": "#000000", "grid_op": 0.05, "silk": "#2f3e35", "silk_dim": "#6a7d70",
        "copper": "#b8732c", "gold": "#cf9310", "chip": "#24282f", "chip_hi": "#3b414b",
        "chip_text": "#f3f4f6", "chip_muted": "#a6aeb8", "pin": "#8a929c",
        "led_on": "#2da44e", "led_off": "#c4d0c1", "pulse": "#ff8c1a", "hole": "#ffffff",
    },
}


def esc(value):
    return escape(str(value), quote=True)


def width(s, size):
    return len(s) * size * ADVANCE


def fit(s, size, max_w):
    """Cut a string with an ellipsis so it never runs past max_w."""
    n = max(1, int(max_w // (size * ADVANCE)))
    return s if len(s) <= n else s[: max(1, n - 1)].rstrip() + "…"


def wrap(s, size, max_w, lines):
    """Word-wrap into at most `lines` lines; the last one gets an ellipsis if needed."""
    n = max(1, int(max_w // (size * ADVANCE)))
    words, out, cur, i = s.split(), [], "", 0
    while i < len(words) and len(out) < lines - 1:
        trial = f"{cur} {words[i]}".strip()
        if len(trial) <= n or not cur:
            cur, i = trial, i + 1
        else:
            out.append(cur)
            cur = ""
    rest = " ".join([cur] + words[i:]).strip()
    if rest:
        out.append(rest)  # the last line takes whatever is left, cut by fit()
    return [fit(line, size, max_w) for line in out]


def text(x, y, s, size, fill, weight=400, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    ra, rb = rgb(a), rgb(b)
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ra, rb))


def luminance(h):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def lang_color(lang, th):
    """The language colour, nudged until it reads on the current background."""
    base = LANG.get(lang or "", "#8b949e")
    if th["name"] == "dark" and luminance(base) < 0.12:
        return mix(base, "#ffffff", 0.45)
    if th["name"] == "light" and luminance(base) > 0.55:
        return mix(base, "#000000", 0.3)
    return base


def document(w, h, body, label, css="", defs=""):
    style = ("text{font-family:%s;font-variant-ligatures:none}" % FONT) + css + (
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f"<title>{esc(label)}</title><style>{style}</style>"
            + (f"<defs>{defs}</defs>" if defs else "") + body + "</svg>\n")
