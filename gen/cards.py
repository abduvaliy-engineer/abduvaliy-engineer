"""Terminal card, section headings and project/contribution cards."""
import datetime as dt

import board
from svg import document, esc, fit, lang_color, text, width, wrap

TASHKENT = dt.timezone(dt.timedelta(hours=5))
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
HEADINGS = [("projects", "~/projects", "things i built"),
            ("contributions", "~/contributions", "my code in other people's projects"),
            ("activity", "~/activity", "how often i code")]
KIND = {"public": "green", "private": "purple", "team": "blue", "personal": "accent"}


def local(stamp):
    t = board.when(stamp)
    assert t is not None, "a date is required here"
    return t.astimezone(TASHKENT)


def day(d):
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def span(stamps):
    days = sorted(local(s) for s in stamps if s)
    a, b = days[0], days[-1]
    if a.date() == b.date():
        return day(a)
    if (a.year, a.month) == (b.year, b.month):
        return f"{MONTHS[a.month - 1]} {a.day}–{b.day}, {a.year}"
    if a.year == b.year:
        return f"{MONTHS[a.month - 1]} {a.day} – {MONTHS[b.month - 1]} {b.day}, {a.year}"
    return f"{day(a)} – {day(b)}"


def ago(stamp, now):
    days = (now - board.when(stamp)).days
    if days < 1:
        return "today"
    if days < 2:
        return "yesterday"
    if days < 14:
        return f"{days}d ago"
    if days < 60:
        return f"{days // 7}w ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


# ---------------------------------------------------------------- terminal

def eye(th):
    """Pixel-art eye (computer vision) as merged rect runs."""
    cols, rows, cx, cy = 23, 13, 11, 6
    inside = set()
    for r in range(rows):
        for c in range(cols):
            x, y = (c - cx) / 11.6, (r - cy) / 6.6
            if abs(x) < 1 and abs(y) <= (1 - x * x) ** 0.85:
                inside.add((r, c))
    dark = th["name"] == "dark"
    colours = {"outline": th["blue"], "sclera": "#1a2330" if dark else "#e7edf5",
               "iris_in": "#3fc1cf" if dark else "#1b7c83", "iris": "#2f81f7" if dark else "#0969da",
               "pupil": "#04070b" if dark else "#0d1117", "shine": "#ffffff"}
    grid = {}
    for r, c in inside:
        d = ((c - cx) ** 2 + (r - cy) ** 2) ** 0.5
        if any((r + a, c + b) not in inside for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            grid[r, c] = "outline"
        elif d <= 1.6:
            grid[r, c] = "pupil"
        elif d <= 2.9:
            grid[r, c] = "iris_in"
        elif d <= 4.3:
            grid[r, c] = "iris"
        else:
            grid[r, c] = "sclera"
    grid[cy - 2, cx + 1] = "shine"
    px, out = 8, []
    for r in range(rows):
        c = 0
        while c < cols:
            kind = grid.get((r, c))
            if not kind:
                c += 1
                continue
            run = c
            while run + 1 < cols and grid.get((r, run + 1)) == kind:
                run += 1
            out.append(f'<rect x="{c * px}" y="{r * px}" width="{(run - c + 1) * px}" height="{px}" fill="{colours[kind]}"/>')
            c = run + 1
    return "".join(out), cols * px, rows * px


def terminal(cfg, th, now):
    w = 880
    dark = th["name"] == "dark"
    bg = "#0a0e14" if dark else "#fbfcfe"
    size, lh = 14, 22
    x0 = 32
    lines = []  # (svg, y) in reveal order

    def prompt(y, command):
        return (text(x0, y, "❯", size, th["green"], 700)
                + text(x0 + 20, y, command, size, th["text"]))

    y = 72
    lines.append(prompt(y, "fastfetch"))
    info_x, val_x = 268, 268 + 92
    y0 = y + 34
    head = f'{cfg["user"]}@{cfg["host"]}'
    lines.append(f'<text x="{info_x}" y="{y0}" font-size="{size}">'
                 f'<tspan fill="{th["blue"]}" font-weight="700">{esc(cfg["user"])}</tspan>'
                 f'<tspan fill="{th["faint"]}">@</tspan>'
                 f'<tspan fill="{th["blue"]}" font-weight="700">{esc(cfg["host"])}</tspan></text>')
    lines.append(text(info_x, y0 + lh, "-" * len(head), size, th["faint"]))
    for i, (k, v) in enumerate(cfg["fetch"]):
        yy = y0 + lh * (i + 2)
        lines.append(text(info_x, yy, k, size, th["blue"], 700)
                     + text(val_x, yy, fit(v, size, w - 28 - val_x), size, th["text"]))
    pal_y = y0 + lh * (len(cfg["fetch"]) + 2) - 8
    palette = [th["red"], th["green"], th["accent"], th["blue"], th["purple"], "#39c5cf", th["muted"], th["text"]]
    lines.append("".join(f'<rect x="{info_x + i * 22}" y="{pal_y}" width="19" height="12" rx="2" fill="{c}"/>'
                         for i, c in enumerate(palette)))
    block_bottom = pal_y + 12

    art, aw, ah = eye(th)
    ex = 40 + (200 - aw) / 2
    ey = (y0 - 14 + block_bottom) / 2 - ah / 2 + 8
    g = th["green"]
    m = 10
    bx0, by0, bx1, by1 = ex - m, ey - m, ex + aw + m, ey + ah + m
    corners = (f"M{bx0} {by0 + 16}V{by0}H{bx0 + 16} M{bx1 - 16} {by0}H{bx1}V{by0 + 16} "
               f"M{bx1} {by1 - 16}V{by1}H{bx1 - 16} M{bx0 + 16} {by1}H{bx0}V{by1 - 16}")
    tag = "eye 0.98"
    logo = (f'<g transform="translate({ex:.1f} {ey:.1f})"><g class="eye">{art}</g></g>'
            f'<path d="{corners}" fill="none" stroke="{g}" stroke-width="2.5"/>'
            f'<rect x="{bx0}" y="{by0 - 18}" width="{width(tag, 10.5) + 12:.1f}" height="16" rx="2" fill="{g}"/>'
            + text(bx0 + 6, by0 - 6, tag, 10.5, bg, 700))
    lines.insert(1, logo)

    y = block_bottom + 34
    lines.append(prompt(y, "cat about.txt"))
    for line in wrap(cfg["about"], size, w - 2 * x0, 2):
        y += lh
        lines.append(text(x0, y, line, size, th["text"]))
    y += lh + 12
    lines.append(prompt(y, "cat now.txt"))
    for item in cfg["now"]:
        y += lh
        lines.append(text(x0, y, "→", size, th["accent"], 700)
                     + text(x0 + 20, y, fit(item, size, w - x0 - 20 - 28), size, th["text"]))
    y += lh + 12
    lines.append(text(x0, y, "❯", size, th["green"], 700)
                 + f'<rect class="cur" x="{x0 + 20}" y="{y - 13}" width="9" height="17" fill="{th["text"]}"/>')
    h = y + 26

    stamp = now.astimezone(TASHKENT)
    body = [f'<defs><linearGradient id="hb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{th["accent"]}"/>'
            f'<stop offset="1" stop-color="{th["blue"]}"/></linearGradient></defs>',
            f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="12" fill="{bg}" stroke="url(#hb)" stroke-width="2"/>',
            text(x0, 27, f'{cfg["user"]}@{cfg["host"]}: ~', 11.5, th["muted"]),
            text(w - x0, 27, f"{stamp:%a %d %b}".lower(), 11.5, th["muted"], 400, "end"),
            f'<line x1="2" y1="40" x2="{w - 2}" y2="40" stroke="{th["border"]}"/>']
    for i, svg in enumerate(lines):
        body.append(f'<g class="ln" style="animation-delay:{0.15 + i * 0.07:.2f}s">{svg}</g>')
    css = (".ln{animation:ln .45s ease-out both}@keyframes ln{from{opacity:0;transform:translateY(4px)}}"
           ".cur{animation:cur 1.1s steps(1) infinite}@keyframes cur{50%{opacity:0}}"
           ".eye{transform-box:fill-box;transform-origin:center;animation:eye 6s ease-in-out infinite}"
           "@keyframes eye{0%,91%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}")
    label = (f'{cfg["user"]}: {cfg["role"]}, focused on {cfg["focus"]}. '
             + "; ".join(f"{k}: {v}" for k, v in cfg["fetch"]) + f'. {cfg["about"]} Now: ' + "; ".join(cfg["now"]))
    return document(w, h, "".join(body), label, css)


# ---------------------------------------------------------------- headings

def heading(title, sub, th):
    w, h = 880, 60
    tx = 30
    sx = tx + width(title, 20) + 14
    end = sx + width(sub, 12.5) + 18
    body = (text(6, 38, "❯", 20, th["accent"], 700) + text(tx, 38, title, 20, th["text"], 700)
            + text(sx, 37, sub, 12.5, th["muted"])
            + f'<path d="M{end:.1f} 33 H852" stroke="{th["copper"]}" stroke-width="2" stroke-opacity=".8"/>'
            + f'<circle cx="860" cy="33" r="4.5" fill="{th["bg"]}" stroke="{th["copper"]}" stroke-width="2"/>')
    return document(w, h, body, f"{title}: {sub}")


# ---------------------------------------------------------------- cards

def frame(w, h, th):
    return (f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{th["card"]}" '
            f'stroke="{th["border"]}" stroke-width="1.2"/>')


def pill(x, y, label, colour, th):
    pw = width(label, 10.5) + 16
    return (f'<rect x="{x:.1f}" y="{y - 13:.1f}" width="{pw:.1f}" height="18" rx="9" fill="{colour}" '
            f'fill-opacity=".14" stroke="{colour}" stroke-opacity=".55"/>'
            + text(x + 8, y, label, 10.5, colour, 600)), pw


def mini_chip(x0, y0, w, h, lang, kind, th):
    b = (x0, y0, x0 + w, y0 + h)
    hidden = kind in ("private", "team")
    return ((board.courtyard(b, th, 3) if hidden else "")
            + board.pins(b)
            + f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="4" fill="{th["chip"]}" stroke="{th["chip_hi"]}"/>'
            + f'<rect x="{x0 + 3}" y="{y0 + 3}" width="{w - 6}" height="{h - 6}" rx="2.5" fill="url(#sheen)"/>'
            + f'<circle cx="{x0 + 7}" cy="{y0 + 7}" r="1.8" fill="{th["chip_hi"]}"/>'
            + f'<rect x="{x0 + 7}" y="{y0 + h - 6.5}" width="{w - 14}" height="2.6" rx="1.3" fill="{lang_color(lang, th)}"/>')


def project(p, info, th, now):
    w, h = 440, 150
    info = info or {}
    tx, tw = 96, 440 - 96 - 18
    parts = [frame(w, h, th), mini_chip(26, 36, 50, 34, p["lang"], p["kind"], th),
             text(tx, 44, fit(p["name"], 15.5, tw), 15.5, th["text"], 700)]
    if info.get("pushed_at") and board.recent(info["pushed_at"], now):
        parts.append(board.led(88, 23, True, th))
    for i, line in enumerate(wrap(p["note"], 12, tw, 3)):
        parts.append(text(tx, 67 + i * 18, line, 12, th["muted"]))
    lang = info.get("language") or p["lang"]
    parts.append(f'<circle cx="27" cy="128" r="5" fill="{lang_color(lang, th)}"/>')
    parts.append(text(38, 132, lang, 11.5, th["muted"]))
    x = 38 + width(lang, 11.5) + 12
    badge, pw = pill(x, 132, p["kind"], th[KIND[p["kind"]]], th)
    parts.append(badge)
    x += pw + 12
    if info.get("stars"):
        parts.append(text(x, 132, f"★ {info['stars']}", 11.5, th["muted"]))
    if info.get("pushed_at"):
        parts.append(text(w - 20, 132, f"updated {ago(info['pushed_at'], now)}", 11, th["faint"], 400, "end"))
    label = f"{p['name']} ({p['kind']}, {lang}): {p['note']}"
    return document(w, h, "".join(parts), label, defs=board.defs(th))


def merge_glyph(x, y, colour):
    return (f'<g fill="none" stroke="{colour}" stroke-width="1.8">'
            f'<circle cx="{x}" cy="{y - 7}" r="2.6"/><circle cx="{x}" cy="{y + 7}" r="2.6"/>'
            f'<circle cx="{x + 11}" cy="{y + 1}" r="2.6"/><path d="M{x} {y - 4.4} V{y + 4.4}"/>'
            f'<path d="M{x} {y - 4.4} C{x} {y + 1} {x + 3} {y + 1} {x + 8.4} {y + 1}"/></g>')


def commit_glyph(x, y, colour):
    return (f'<g fill="none" stroke="{colour}" stroke-width="1.8"><path d="M{x - 3} {y} H{x + 2.4} M{x + 9.6} {y} H{x + 15}"/>'
            f'<circle cx="{x + 6}" cy="{y}" r="3.6"/></g>')


def contribution(c, info, th):
    w, h = 440, 150
    info = info or {}
    pulls = info.get("pulls") or []
    adds = sum(p["additions"] for p in pulls) if pulls else c["additions"]
    dels = sum(p["deletions"] for p in pulls) if pulls else c["deletions"]
    status = c.get("status", "merged")
    colour = th["purple"] if status == "merged" else th["green"]
    repo = c.get("label") or c["repo"] + (f" #{pulls[0]['number']}" if len(pulls) == 1 else "")
    stats = (f"+{adds} −{dels}" if dels else f"+{adds}") if c.get("stats", True) else f"{len(pulls)} prs"
    parts = [frame(w, h, th),
             merge_glyph(24, 29, colour) if status == "merged" else commit_glyph(18, 29, colour),
             text(46, 33, fit(repo, 11.5, w - 46 - width(stats, 11.5) - 32), 11.5, th["muted"])]
    if c.get("stats", True):
        parts.append(f'<text x="{w - 20}" y="33" font-size="11.5" text-anchor="end" font-weight="600">'
                     f'<tspan fill="{th["green"]}">+{adds}</tspan>'
                     + (f'<tspan fill="{th["red"]}"> −{dels}</tspan>' if dels else "") + "</text>")
    else:
        parts.append(text(w - 20, 33, stats, 11.5, colour, 600, "end"))
    for i, line in enumerate(wrap(c["note"], 14.5, w - 40, 2)):
        parts.append(text(20, 62 + i * 20, line, 14.5, th["text"], 700))
    titles = c.get("titles") or [p["title"] for p in pulls]
    parts.append(text(20, 104, fit(" · ".join(titles), 11, w - 40), 11, th["faint"]))
    badge, pw = pill(20, 132, status, colour, th)
    parts.append(badge)
    stamps = [p["merged_at"] for p in pulls if p.get("merged_at")] or [c["date"]]
    meta = [span(stamps)]
    if len(pulls) > 1 and c.get("stats", True):
        meta.append(f"{len(pulls)} prs")
    if info.get("stars"):
        meta.append(f"★ {info['stars']}")
    parts.append(text(20 + pw + 12, 132, "  ·  ".join(meta), 11, th["muted"]))
    label = f"{repo}: {c['note']}. {status} {span(stamps)}. " + "; ".join(titles)
    return document(w, h, "".join(parts), label, defs=board.defs(th))


def href(c, login):
    if c.get("href"):
        return c["href"]
    if c.get("pr"):
        return f"https://github.com/{c['repo']}/pull/{c['pr']}"
    return f"https://github.com/{c['repo']}/pulls?q=is%3Apr+author%3A{login}+is%3Amerged"
