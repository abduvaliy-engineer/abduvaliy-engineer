"""The hero: a circuit board. The CPU in the middle is me, every chip is a project."""
import datetime as dt
import random

from svg import document, lang_color, mix, text, width

W, H = 1000, 520
CPU = (422.0, 194.0, 578.0, 350.0)
CX, CY = 500.0, 272.0
PITCH = 6.0     # pin pitch, and the spacing between traces in a bus
PIN = 7.0       # pin leg length
BEND = 0.4142   # tan(22.5°): keeps a bus evenly spaced through its 45° bends
LEFT_EDGE, RIGHT_EDGE = 262.0, 738.0
TIER_H = {1: 52.0, 2: 60.0, 3: 70.0}
# slot: (side, chip centre on the cross axis, landing point on the CPU)
SLOTS = {
    "L1": ("left", 140.0, 236.0), "L2": ("left", 272.0, 272.0), "L3": ("left", 404.0, 308.0),
    "R1": ("right", 140.0, 236.0), "R2": ("right", 272.0, 272.0), "R3": ("right", 404.0, 308.0),
    "T": ("top", 128.0, 500.0), "B": ("bottom", 412.0, 500.0),
}
STITCH = [(172, 206), (172, 338), (828, 206), (828, 338)]
CAPS = [(392, 180), (600, 180), (392, 364), (600, 364)]


def when(stamp):
    if not stamp:
        return None
    if len(stamp) == 10:
        stamp += "T12:00:00Z"
    return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def recent(stamp, now, days=7):
    t = when(stamp)
    return None if t is None else (now - t).days < days


def chips(cfg, live):
    """Board chips from the projects and contributions that have a slot."""
    out = []
    for p in cfg["projects"]:
        if p.get("slot"):
            info = live["projects"].get(p["id"]) or {}
            out.append({"id": p["id"], "label": p["chip"], "lang": p["lang"], "kind": p["kind"],
                        "slot": p["slot"], "tier": p.get("tier", 2), "upstream": False,
                        "stamp": info.get("pushed_at"),
                        "sub": f"{p['lang']} · {p['kind'].capitalize()}"})
    for c in cfg["contributions"]:
        if c.get("slot"):
            pulls = (live["contributions"].get(c["id"]) or {}).get("pulls") or []
            stamp = max((p["merged_at"] for p in pulls if p.get("merged_at")), default=c.get("date"))
            status = f"{len(pulls)} Merged" if pulls else c.get("status", "merged").capitalize()
            out.append({"id": c["id"], "label": c["chip"], "lang": c["lang"], "kind": "upstream",
                        "slot": c["slot"], "tier": c.get("tier", 2), "upstream": True,
                        "stamp": stamp, "sub": f"{c['lang']} · {status}"})
    return out


def box(chip):
    side, centre, _ = SLOTS[chip["slot"]]
    h = TIER_H[chip["tier"]]
    w = max(118.0, round(width(chip["label"], 11.5) + 36))
    if side == "left":
        x0 = LEFT_EDGE - w
    elif side == "right":
        x0 = RIGHT_EDGE
    else:
        x0 = CX - w / 2
    return (x0, centre - h / 2, x0 + w, centre + h / 2)


def sgn(v):
    return (v > 0) - (v < 0)


def bus(chip, b):
    """Three parallel traces from a chip to the CPU, with constant spacing."""
    side, centre, land = SLOTS[chip["slot"]]
    x0, y0, x1, y1 = b
    paths = []
    for k in (-1, 0, 1):
        if side in ("left", "right"):
            d = 1 if side == "left" else -1
            xs = x1 + PIN if d == 1 else x0 - PIN
            xe = CPU[0] - PIN if d == 1 else CPU[2] + PIN
            ys, ye = centre + k * PITCH, land + k * PITCH
            dy = ye - ys
            if abs(dy) < 0.5:
                paths.append([(xs, ys), (xe, ye)])
                continue
            xb = xs + d * (16 + k * PITCH * BEND * -sgn(dy))
            paths.append([(xs, ys), (xb, ys), (xb + d * abs(dy), ye), (xe, ye)])
        else:
            d = 1 if side == "top" else -1
            x = land + k * PITCH
            ys = y1 + PIN if d == 1 else y0 - PIN
            ye = CPU[1] - PIN if d == 1 else CPU[3] + PIN
            paths.append([(x, ys), (x, ye)])
    return paths


def wire(a, b):
    """The special trace between two chips (left one's right side to right one's left side)."""
    ys = (a[1] + a[3]) / 2 - PITCH
    ye = (b[1] + b[3]) / 2 - 3 * PITCH
    xs, xe = a[2] + PIN, b[0] - PIN
    if abs(ye - ys) < 0.5:
        return [(xs, ys), (xe, ye)]
    xb = xs + 20
    return [(xs, ys), (xb, ys), (xb + abs(ye - ys), ye), (xe, ye)]


def layout(cfg, live):
    placed = [(c, box(c)) for c in chips(cfg, live)]
    buses = {c["id"]: bus(c, b) for c, b in placed}
    boxes = {c["id"]: b for c, b in placed}
    w = cfg.get("wire")
    special = wire(boxes[w["from"]], boxes[w["to"]]) if w else None
    return placed, buses, special


def d_attr(pts):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def defs(th):
    pin = th["pin"]
    gold = th["gold"]
    return (
        f'<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{th["board_a"]}"/>'
        f'<stop offset="1" stop-color="{th["board_b"]}"/></linearGradient>'
        f'<radialGradient id="vg" cx=".5" cy=".46" r=".72"><stop offset=".55" stop-color="{th["board_b"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{th["board_b"]}" stop-opacity=".75"/></radialGradient>'
        f'<pattern id="dots" width="12" height="12" patternUnits="userSpaceOnUse">'
        f'<circle cx="6" cy="6" r=".9" fill="{th["grid"]}" fill-opacity="{th["grid_op"]}"/></pattern>'
        f'<pattern id="pv" width="{PIN}" height="6" patternUnits="userSpaceOnUse"><rect y=".6" width="{PIN}" height="2.8" rx=".6" fill="{pin}"/></pattern>'
        f'<pattern id="ph" width="6" height="{PIN}" patternUnits="userSpaceOnUse"><rect x=".6" width="2.8" height="{PIN}" rx=".6" fill="{pin}"/></pattern>'
        f'<pattern id="pvg" width="{PIN}" height="6" patternUnits="userSpaceOnUse"><rect y=".6" width="{PIN}" height="2.8" rx=".6" fill="{gold}"/></pattern>'
        f'<pattern id="phg" width="6" height="{PIN}" patternUnits="userSpaceOnUse"><rect x=".6" width="2.8" height="{PIN}" rx=".6" fill="{gold}"/></pattern>'
        f'<radialGradient id="pg"><stop offset="0" stop-color="{th["pulse"]}" stop-opacity=".95"/>'
        f'<stop offset="1" stop-color="{th["pulse"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="cg"><stop offset="0" stop-color="{th["gold"]}" stop-opacity=".30"/>'
        f'<stop offset="1" stop-color="{th["gold"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="ihs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{th["chip_hi"]}"/>'
        f'<stop offset="1" stop-color="{th["chip"]}"/></linearGradient>'
        f'<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".09"/>'
        f'<stop offset=".5" stop-color="#ffffff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="xtal" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#dfe3e8"/>'
        f'<stop offset="1" stop-color="#8b929b"/></linearGradient>'
        f'<radialGradient id="led"><stop offset="0" stop-color="#d7ffe0"/><stop offset=".55" stop-color="{th["led_on"]}"/>'
        f'<stop offset="1" stop-color="{th["led_on"]}" stop-opacity=".2"/></radialGradient>'
    )


def pins(b, gold=False):
    """Pin legs on all four sides of a package, aligned to the 6px grid."""
    x0, y0, x1, y1 = b
    v, h = ("url(#pvg)", "url(#phg)") if gold else ("url(#pv)", "url(#ph)")
    m = 6.0
    return (f'<rect x="{x0 - PIN:.1f}" y="{y0 + m:.1f}" width="{PIN}" height="{y1 - y0 - 2 * m:.1f}" fill="{v}"/>'
            f'<rect x="{x1:.1f}" y="{y0 + m:.1f}" width="{PIN}" height="{y1 - y0 - 2 * m:.1f}" fill="{v}"/>'
            f'<rect x="{x0 + m:.1f}" y="{y0 - PIN:.1f}" width="{x1 - x0 - 2 * m:.1f}" height="{PIN}" fill="{h}"/>'
            f'<rect x="{x0 + m:.1f}" y="{y1:.1f}" width="{x1 - x0 - 2 * m:.1f}" height="{PIN}" fill="{h}"/>')


def led(x, y, on, th):
    if on:
        return (f'<g class="blink"><circle cx="{x}" cy="{y}" r="10" fill="{th["led_on"]}" fill-opacity=".18"/>'
                f'<circle cx="{x}" cy="{y}" r="4.6" fill="url(#led)"/></g>')
    return f'<circle cx="{x}" cy="{y}" r="4.2" fill="{th["led_off"]}" stroke="{th["silk_dim"]}" stroke-opacity=".35"/>'


def courtyard(b, th, gap):
    """Dashed silkscreen outline around a package: marks private or team work."""
    x0, y0, x1, y1 = b
    o = PIN + gap
    return (f'<rect x="{x0 - o:.1f}" y="{y0 - o:.1f}" width="{x1 - x0 + 2 * o:.1f}" height="{y1 - y0 + 2 * o:.1f}" '
            f'rx="6" fill="none" stroke="{th["silk"]}" stroke-opacity=".7" stroke-width="1.3" stroke-dasharray="5 4"/>')


def chip_svg(chip, b, n, th):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hidden = chip["kind"] in ("private", "team")
    parts = [
        courtyard(b, th, 4) if hidden else "",
        pins(b, gold=chip["upstream"]),
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" fill="{th["chip"]}" '
        f'stroke="{th["chip_hi"]}" stroke-width="1"/>',
        f'<rect x="{x0 + 3:.1f}" y="{y0 + 3:.1f}" width="{w - 6:.1f}" height="{h - 6:.1f}" rx="2.5" fill="url(#sheen)"/>',
        f'<circle cx="{x0 + 8:.1f}" cy="{y0 + 8:.1f}" r="2" fill="{th["chip_hi"]}"/>',
        text(cx, cy - 1, chip["label"], 11.5, th["chip_text"], 600, "middle"),
        text(cx, cy + 13, chip["sub"], 8.5, th["chip_muted"], 400, "middle"),
        f'<rect x="{x0 + 8:.1f}" y="{y1 - 6.5:.1f}" width="{w - 16:.1f}" height="2.6" rx="1.3" '
        f'fill="{lang_color(chip["lang"], th)}"/>',
        text(x0, y0 - PIN - 9 if hidden else y0 - PIN - 4, f"U{n}", 8.5, th["silk_dim"]),
    ]
    if chip["on"] is not None:
        parts.append(led(round(x1 + PIN + 7), round(y0 - PIN - 7), chip["on"], th))
    return "".join(parts)


def traces(paths, colour, th, glow=False):
    out = []
    for pts in paths:
        d = d_attr(pts)
        if glow:
            out.append(f'<path d="{d}" stroke="{colour}" stroke-opacity=".16" stroke-width="6"/>')
        out.append(f'<path d="{d}" stroke="{th["board_b"]}" stroke-opacity=".8" stroke-width="4.2"/>')
        out.append(f'<path d="{d}" stroke="{colour}" stroke-opacity=".92" stroke-width="2"/>')
    return f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">{"".join(out)}</g>'


def pulse(pts, dur, begin, reverse, colour="url(#pg)"):
    keys = "1;0" if reverse else "0;1"
    return (f'<g><circle r="6.5" fill="{colour}"/><circle r="1.9" fill="#fffaf0"/>'
            f'<animateMotion dur="{dur:.2f}s" begin="-{begin:.2f}s" repeatCount="indefinite" '
            f'calcMode="linear" keyPoints="{keys}" keyTimes="0;1" path="{d_attr(pts)}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.12;.88;1" dur="{dur:.2f}s" '
            f'begin="-{begin:.2f}s" repeatCount="indefinite"/></g>')


def cpu_svg(cfg, th):
    x0, y0, x1, y1 = CPU
    return "".join([
        f'<circle class="breathe" cx="{CX}" cy="{CY}" r="128" fill="url(#cg)"/>',
        pins(CPU),
        f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="8" fill="{th["chip"]}" stroke="{th["chip_hi"]}"/>',
        f'<rect x="{x0 + 14}" y="{y0 + 14}" width="{x1 - x0 - 28}" height="{y1 - y0 - 28}" rx="5" fill="url(#ihs)" '
        f'stroke="{th["chip_hi"]}" stroke-opacity=".8"/>',
        f'<path d="M{x0 + 6} {y0 + 6} h12 l-12 12 z" fill="{th["gold"]}" fill-opacity=".85"/>',
        text(CX, 251, cfg["name"].split()[0], 17, th["chip_text"], 700, "middle"),
        text(CX, 270, cfg["role"], 9.5, th["chip_muted"], 400, "middle"),
        text(CX, 284, cfg["focus"], 9.5, th["gold"], 600, "middle"),
        f'<line x1="{x0 + 34}" y1="298" x2="{x1 - 34}" y2="298" stroke="{th["chip_muted"]}" stroke-opacity=".35"/>',
        text(CX, 314, "HBAI Academy", 8, th["chip_muted"], 400, "middle"),
        text(CX, 325, "Foundation Stage", 8, th["chip_muted"], 400, "middle"),
        text(x0, y0 - PIN - 4, "U1", 8.5, th["silk_dim"]),
    ])


def extras(th):
    """Crystal, decoupling caps, stitching vias and mounting holes."""
    c = th["copper"]
    parts = [traces([[(341, 232), (357, 248), (CPU[0] - PIN, 248)], [(303, 232), (296, 239), (296, 247)]], c, th),
             f'<circle cx="296" cy="250" r="3.4" fill="{th["hole"]}" stroke="{c}" stroke-width="2"/>',
             f'<rect x="300" y="228" width="7" height="8" rx="1" fill="{th["pin"]}"/>',
             f'<rect x="337" y="228" width="7" height="8" rx="1" fill="{th["pin"]}"/>',
             f'<rect x="305" y="224" width="34" height="16" rx="8" fill="url(#xtal)" stroke="#6c737c" stroke-width=".8"/>',
             text(322, 235, "24h", 8, "#2b3036", 700, "middle"),
             text(305, 218, "Y1", 8.5, th["silk_dim"])]
    for i, (x, y) in enumerate(CAPS, 1):
        parts.append(f'<rect x="{x - 6}" y="{y - 3}" width="3" height="6" fill="{th["pin"]}"/>'
                     f'<rect x="{x + 3}" y="{y - 3}" width="3" height="6" fill="{th["pin"]}"/>'
                     f'<rect x="{x - 3}" y="{y - 2.6}" width="6" height="5.2" fill="#b08d5b"/>'
                     + text(x - 6, y - 7, f"C{i}", 7.5, th["silk_dim"]))
    for x, y in STITCH + [(34, y) for y in range(118, 420, 28)] + [(966, y) for y in range(118, 420, 28)]:
        parts.append(f'<circle cx="{x}" cy="{y}" r="2.7" fill="{th["hole"]}" stroke="{c}" stroke-opacity=".8" stroke-width="1.6"/>')
    for x, y in [(30, 30), (970, 30), (30, 490), (970, 490)]:
        parts.append(f'<circle cx="{x}" cy="{y}" r="11" fill="none" stroke="{c}" stroke-width="3" stroke-opacity=".9"/>'
                     f'<circle cx="{x}" cy="{y}" r="7" fill="{th["hole"]}"/>')
    return "".join(parts)


def silkscreen(cfg, th, now):
    local = now.astimezone(dt.timezone(dt.timedelta(hours=5)))
    s, d = th["silk"], th["silk_dim"]
    return "".join([
        text(56, 50, cfg["name"], 15, s, 700, extra=' letter-spacing=".6"'),
        text(56, 68, f'{cfg["role"]} · {cfg["focus"]}', 10.5, d),
        text(944, 50, f"Rev {local:%Y.%m.%d}", 10.5, s, 600, "end"),
        text(944, 68, "Redrawn daily from live GitHub data", 9.5, d, 400, "end"),
        text(56, 488, cfg["study"], 10.5, s, 600),
        text(944, 488, "Drawn with plain Python", 9.5, d, 400, "end"),
    ])


def board(cfg, live, th, now):
    placed, buses, special = layout(cfg, live)
    rnd = random.Random(7)
    body = [f'<rect x="8" y="8" width="{W - 16}" height="{H - 16}" rx="22" fill="url(#bd)" stroke="{th["board_edge"]}" stroke-width="2"/>',
            f'<rect x="8" y="8" width="{W - 16}" height="{H - 16}" rx="22" fill="url(#dots)"/>',
            f'<rect x="8" y="8" width="{W - 16}" height="{H - 16}" rx="22" fill="url(#vg)"/>',
            extras(th)]
    for chip, _ in placed:
        colour = th["gold"] if chip["upstream"] else th["copper"]
        body.append(traces(buses[chip["id"]], colour, th, glow=chip["upstream"]))
    if special:
        w = cfg["wire"]
        mx = (special[0][0] + special[-1][0]) / 2
        my = special[0][1]
        body.append(traces([special], th["gold"], th, glow=True))
        body.append(f'<rect x="{mx - 6:.1f}" y="{my - 4:.1f}" width="12" height="8" rx="1.5" fill="{th["gold"]}"/>')
        body.append(text(mx, my - 10, w["label"], 9.5, th["gold"], 700, "middle"))
    body.append(cpu_svg(cfg, th))
    for n, (chip, b) in enumerate(placed, 2):
        chip = dict(chip, on=None if chip["kind"] in ("private", "team") else recent(chip["stamp"], now))
        body.append(chip_svg(chip, b, n, th))
    for i, (chip, _) in enumerate(placed):
        dur = 2.6 + rnd.random() * 1.8
        body.append(pulse(buses[chip["id"]][1], dur, rnd.random() * dur, reverse=i % 2 == 1))
    if special:
        body.append(pulse(special, 3.6, 1.2, reverse=False))
    body.append(silkscreen(cfg, th, now))
    css = (".breathe{animation:breathe 5s ease-in-out infinite alternate}@keyframes breathe{from{opacity:.45}}"
           ".blink{animation:blink 1.5s ease-in-out infinite alternate}@keyframes blink{from{opacity:.3}}")
    label = (f"{cfg['name']}: {cfg['role']}, {cfg['focus']}. A circuit board drawn from my GitHub: "
             "the CPU in the middle is me, the chips around it are my projects and contributions.")
    return document(W, H, "".join(body), label, css, defs(th))


KEY = {"w": 1000, "h": 174, "box": (8, 162), "rows": (39, 87), "rule": 118, "foot": 138}


def key(th):
    """The legend under the board, with even padding and the rule clear of both rows."""
    items = [("The CPU", "Me"), ("A Chip", "Something I built or worked on"),
             ("The Stripe", "Its main language"), ("Dashed Outline", "Private or team work"),
             ("Gold Pins + Traces", "My code in someone else's repo"), ("Green LED", "Worked on it this week"),
             ("GPIO 11", "The pin behind my kernel fix"), ("The Crystal", "Redraws this board every day")]
    w, h = KEY["w"], KEY["h"]
    top, bottom = KEY["box"]
    parts = [f'<rect x="8" y="{top}" width="{w - 16}" height="{bottom - top}" rx="14" '
             f'fill="{th["card"]}" stroke="{th["border"]}"/>']
    for i, (title, desc) in enumerate(items):
        x = 34 + (i % 4) * 240
        base = KEY["rows"][i // 4]  # title baseline; the description sits 16px lower
        parts.append(glyph(i, x, base + 5, th))  # +5 centres the glyph on both lines
        parts.append(text(x + 40, base, title, 12, th["text"], 700))
        parts.append(text(x + 40, base + 16, desc, 10, th["muted"]))
    rule = KEY["rule"]
    parts.append(f'<line x1="34" y1="{rule}" x2="{w - 34}" y2="{rule}" stroke="{th["border"]}"/>')
    parts.append(text(w / 2, KEY["foot"], "The moving dots are just data flowing · Redrawn every day by a GitHub Action",
                      10, th["faint"], 400, "middle"))
    return document(w, h, "".join(parts), "Key: the CPU is me, chips are projects, gold means merged upstream.",
                    defs=defs(th))


def glyph(i, x, y, th):
    """Tiny drawings for the legend, each centred on (x + 14, y)."""
    cx = x + 14
    chip = th["chip"]
    if i == 0:
        return (f'<rect x="{cx - 9}" y="{y - 9}" width="18" height="18" rx="2.5" fill="{chip}" stroke="{th["chip_hi"]}"/>'
                f'<rect x="{cx - 12}" y="{y - 6}" width="3" height="12" fill="url(#pv)"/>'
                f'<rect x="{cx + 9}" y="{y - 6}" width="3" height="12" fill="url(#pv)"/>'
                f'<circle cx="{cx}" cy="{y}" r="3" fill="{th["gold"]}"/>')
    if i in (1, 3):
        body = (f'<rect x="{cx - 13}" y="{y - 10}" width="26" height="3" fill="url(#ph)"/>'
                f'<rect x="{cx - 13}" y="{y + 7}" width="26" height="3" fill="url(#ph)"/>'
                f'<rect x="{cx - 14}" y="{y - 7}" width="28" height="14" rx="2" fill="{chip}" stroke="{th["chip_hi"]}"/>')
        if i == 3:  # the same dashed courtyard the board draws around private/team chips
            body = (f'<rect x="{cx - 18}" y="{y - 14}" width="36" height="28" rx="4" fill="none" '
                    f'stroke="{th["silk"]}" stroke-opacity=".7" stroke-width="1.2" stroke-dasharray="4 3"/>') + body
        return body
    if i == 2:
        return "".join(f'<rect x="{cx - 13}" y="{y - 7 + j * 6}" width="26" height="3" rx="1.5" fill="{lang_color(l, th)}"/>'
                       for j, l in enumerate(["Python", "TypeScript", "Shell"]))
    if i == 4:
        return (f'<path d="M{cx - 14} {y - 4} h10 l8 8 h10" fill="none" stroke="{th["gold"]}" stroke-width="2.2"/>'
                f'<path d="M{cx - 14} {y + 2} h8 l8 8 h12" fill="none" stroke="{th["gold"]}" stroke-width="2.2" stroke-opacity=".7"/>')
    if i == 5:
        return led(cx, y, True, th)
    if i == 6:
        return (f'<path d="M{cx - 14} {y + 3} h28" stroke="{th["gold"]}" stroke-width="2.2"/>'
                f'<rect x="{cx - 6}" y="{y - 1}" width="12" height="8" rx="1.5" fill="{th["gold"]}"/>'
                + text(cx, y - 5, "11", 8, th["gold"], 700, "middle"))
    return (f'<rect x="{cx - 14}" y="{y - 7}" width="28" height="14" rx="7" fill="url(#xtal)" stroke="#6c737c" stroke-width=".8"/>'
            + text(cx, y + 3, "24h", 7.5, "#2b3036", 700, "middle"))
