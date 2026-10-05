"""Offline tests for the profile drawings. Standard library only; no network."""
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gen"))

import board  # noqa: E402
import build  # noqa: E402
import cards  # noqa: E402
import fetch  # noqa: E402
import svg  # noqa: E402

NOW = "2026-10-04T12:00:00Z"
CFG = json.loads((ROOT / "gen" / "profile.json").read_text(encoding="utf-8"))


def intersects(p1, p2, q1, q2):
    def orient(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)

    def on(a, b, c):
        return min(a[0], b[0]) - 1e-9 <= c[0] <= max(a[0], b[0]) + 1e-9 and \
            min(a[1], b[1]) - 1e-9 <= c[1] <= max(a[1], b[1]) + 1e-9

    o1, o2, o3, o4 = orient(p1, p2, q1), orient(p1, p2, q2), orient(q1, q2, p1), orient(q1, q2, p2)
    if o1 != o2 and o3 != o4:
        return True
    return any(o == 0 and on(a, b, c) for o, a, b, c in
               ((o1, p1, p2, q1), (o2, p1, p2, q2), (o3, q1, q2, p1), (o4, q1, q2, p2)))


class OfflineBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.files = build.main(["--offline", "--out", cls.tmp.name, "--now", NOW])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_drawing_is_valid_svg_in_both_themes(self):
        stems = {re.sub(r"-(dark|light)\.svg$", "", name) for name in self.files}
        self.assertEqual(len(self.files), 2 * len(stems))
        for stem in stems:
            for theme in ("dark", "light"):
                root = ET.fromstring(self.files[f"{stem}-{theme}.svg"])
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")

    def test_readme_uses_exactly_the_drawings_that_are_built(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        used = set(re.findall(r"/output/([\w.-]+\.svg)", readme))
        self.assertEqual(used - set(self.files), set(), "README points at drawings that are never built")
        self.assertEqual(set(self.files) - used, set(), "drawings are built but never shown")

    def test_foundation_stage_and_role_are_on_the_profile(self):
        for name in ("board-dark.svg", "terminal-light.svg"):
            self.assertIn("foundation stage", self.files[name].lower())
            self.assertIn("ai software engineer", self.files[name].lower())

    def test_board_words_start_with_a_capital(self):
        for name in ("board-dark.svg", "key-dark.svg"):
            root = ET.fromstring(self.files[name])
            for t in root.iter("{http://www.w3.org/2000/svg}text"):
                first = (t.text or "").lstrip()[:1]
                self.assertFalse(first.isalpha() and not first.isupper(), f"lowercase in {name}: {t.text!r}")

    def test_key_has_even_padding_and_a_clear_rule(self):
        root = ET.fromstring(self.files["key-dark.svg"])
        ns = "{http://www.w3.org/2000/svg}"
        box = root.findall(f"{ns}rect")[0]  # top-level only: <defs> holds pin rects too
        top = float(box.get("y") or 0)
        bottom = top + float(box.get("height") or 0)
        rule = float(root.findall(f"{ns}line")[0].get("y1") or 0)
        texts = [(float(t.get("y") or 0), float(t.get("font-size") or 0)) for t in root.iter(f"{ns}text")
                 if t.text and t.get("font-size") in ("12", "10")]
        above = [y for y, _ in texts if y < rule]
        below = [y for y, _ in texts if y > rule]
        self.assertGreaterEqual(rule - (max(above) + 3), 10, "row text crowds the rule")
        self.assertGreaterEqual(min(below) - 7.5 - rule, 10, "footer crowds the rule")
        top_pad = min(y - 0.72 * size for y, size in texts) - top
        bottom_pad = bottom - (max(below) + 3)
        self.assertLessEqual(abs(top_pad - bottom_pad), 4, f"uneven padding {top_pad:.1f} vs {bottom_pad:.1f}")

    def test_board_chips_use_real_names(self):
        board_svg = self.files["board-light.svg"]
        for item in CFG["projects"] + CFG["contributions"]:
            if item.get("slot"):
                self.assertIn(svg.esc(item["chip"]), board_svg)


class BoardGeometry(unittest.TestCase):
    def setUp(self):
        self.placed, self.buses, self.wire = board.layout(CFG, fetch.offline(CFG))

    def segments(self):
        for chip_id, paths in self.buses.items():
            for pts in paths:
                for a, b in zip(pts, pts[1:]):
                    yield chip_id, a, b
        for a, b in zip(self.wire, self.wire[1:]):
            yield "wire", a, b

    def test_buses_never_cross_each_other(self):
        segs = list(self.segments())
        for i, (ida, a1, a2) in enumerate(segs):
            for idb, b1, b2 in segs[i + 1:]:
                if ida != idb:
                    self.assertFalse(intersects(a1, a2, b1, b2), f"{ida} crosses {idb}")

    def test_traces_never_run_through_a_package(self):
        boxes = [b for _, b in self.placed] + [board.CPU]
        for chip_id, a, b in self.segments():
            steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) // 2) + 1
            for s in range(steps + 1):
                x = a[0] + (b[0] - a[0]) * s / steps
                y = a[1] + (b[1] - a[1]) * s / steps
                for x0, y0, x1, y1 in boxes:
                    self.assertFalse(x0 < x < x1 and y0 < y < y1, f"{chip_id} runs through a package")

    def test_chips_fit_on_the_board_without_touching(self):
        boxes = [b for _, b in self.placed] + [board.CPU]
        pad = board.PIN + 4
        for x0, y0, x1, y1 in boxes:
            self.assertTrue(40 <= x0 - pad and x1 + pad <= board.W - 40)
            self.assertTrue(80 <= y0 - pad and y1 + pad <= board.H - 40)
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                apart = a[2] + pad <= b[0] - pad or b[2] + pad <= a[0] - pad or \
                    a[3] + pad <= b[1] - pad or b[3] + pad <= a[1] - pad
                self.assertTrue(apart, f"{a} touches {b}")

    def test_chip_labels_fit_inside_their_package(self):
        for chip, (x0, _, x1, _) in self.placed:
            self.assertLessEqual(svg.width(chip["label"], 11.5) + 12, x1 - x0)
            self.assertLessEqual(svg.width(chip["sub"], 8.5) + 12, x1 - x0)


class Words(unittest.TestCase):
    def test_wrap_keeps_width_and_line_count(self):
        lines = svg.wrap("one two three four five six seven eight nine ten eleven", 12, 100, 2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(svg.width(line, 12) <= 100 for line in lines))
        self.assertTrue(lines[-1].endswith("…"))

    def test_short_text_is_left_alone(self):
        self.assertEqual(svg.wrap("short note", 12, 300, 3), ["short note"])

    def test_user_text_is_escaped(self):
        p = dict(CFG["projects"][0], note="<b> & 'quotes' \"too\"")
        out = cards.project(p, None, svg.THEMES["dark"], board.when(NOW))
        ET.fromstring(out)
        self.assertIn("&lt;b&gt; &amp;", out)

    def test_terminal_lines_fit_the_window(self):
        for th in svg.THEMES.values():
            root = ET.fromstring(cards.terminal(CFG, th, board.when(NOW)))
            w = float(root.get("width") or 0)
            for t in root.iter("{http://www.w3.org/2000/svg}text"):
                if t.get("text-anchor", "start") == "start" and t.text:
                    size = float(t.get("font-size") or 0)
                    self.assertLessEqual(float(t.get("x") or 0) + svg.width(t.text, size), w - 20, t.text)

    def test_dates_read_like_a_person_wrote_them(self):
        now = board.when(NOW)
        self.assertEqual(cards.ago("2026-10-04T06:00:00Z", now), "today")
        self.assertEqual(cards.ago("2026-10-01T06:00:00Z", now), "3d ago")
        self.assertEqual(cards.ago("2026-08-01T06:00:00Z", now), "2mo ago")
        self.assertEqual(cards.span(["2026-07-14T13:42:29Z", "2026-07-20T11:51:09Z"]), "jul 14–20, 2026")
        self.assertEqual(cards.span(["2026-10-02"]), "oct 2, 2026")

    def test_leds_follow_recent_activity(self):
        now = board.when(NOW)
        self.assertTrue(board.recent("2026-10-02", now))
        self.assertFalse(board.recent("2026-09-20T00:00:00Z", now))
        self.assertIsNone(board.recent(None, now))


class Terminal(unittest.TestCase):
    NS = "{http://www.w3.org/2000/svg}"

    def svg(self, theme="dark"):
        return cards.terminal(CFG, svg.THEMES[theme], board.when(NOW))

    def strings(self, root):
        for t in root.iter(f"{self.NS}text"):
            if t.text and t.text.strip():
                yield t.text
            for span in t.iter(f"{self.NS}tspan"):
                if span.text and span.text.strip():
                    yield span.text

    def test_words_start_with_a_capital_but_typed_things_stay_as_typed(self):
        commands = ("fastfetch", "cat about.txt", "cat now.txt", "cat plan.txt")
        literals = {CFG["user"], CFG["host"], "@", f'{CFG["user"]}@{CFG["host"]}: ~', *commands}
        seen = list(self.strings(ET.fromstring(self.svg())))
        self.assertIn(f'{CFG["user"]}@{CFG["host"]}: ~', seen)  # kept exactly as typed, on request
        for s in seen:
            first = s.lstrip()[:1]
            half_typed = any(c.startswith(s.rstrip(cards.CURSOR)) for c in commands)
            if s in literals or half_typed or not first.isalpha():
                continue
            self.assertTrue(first.isupper(), f"lowercase in the terminal: {s!r}")

    def test_plan_shows_the_main_goal_and_every_plan(self):
        out = self.svg("light")
        for s in ["cat plan.txt", CFG["goal"], *CFG["route"], *CFG["plan"]]:
            self.assertIn(svg.esc(s), out)

    def test_goal_route_never_touches_the_goal_text(self):
        _, _, route_left = cards.goal(CFG, 500, svg.THEMES["dark"], 880, 32, 14)
        self.assertGreaterEqual(route_left - (32 + 20 + svg.width(CFG["goal"], 14)), 16)

    def test_iris_glance_stays_inside_the_eye(self):
        art, _, _, shift = cards.eye(svg.THEMES["dark"])
        self.assertEqual(shift, cards.LOOK * 8)
        self.assertIn('class="look"', art)
        with self.assertRaises(ValueError):
            cards.eye(svg.THEMES["dark"], look=6)

    def test_eye_glances_one_way_only(self):
        found = re.search(r"@keyframes look\{(.*?)\}\}", self.svg())
        self.assertIsNotNone(found, "the eye has no glance animation")
        moves = [float(v) for v in re.findall(r"translateX\((-?[\d.]+)px\)", found.group(1) if found else "")]
        self.assertTrue(all(v >= 0 for v in moves), "the eye should only look right")
        self.assertEqual(max(moves), cards.LOOK * 8)

    def test_blink_swaps_pixel_frames_instead_of_squashing(self):
        out = self.svg()
        self.assertFalse("scale" in out, "the eye must not squash or flip")

        def frames(name):
            block = re.search(r"@keyframes %s\{((?:[\d.]+%%\{opacity:[\d.]+\})+)\}" % name, out)
            self.assertIsNotNone(block, f"no {name} keyframes")
            return [(float(p), float(v)) for p, v in re.findall(r"([\d.]+)%\{opacity:([\d.]+)\}",
                                                                 block.group(1) if block else "")]

        def at(keys, t):  # step-end: hold each keyframe's value until the next one
            return [v for p, v in keys if p <= t][-1]

        keys = {name: frames(name) for name in ("open", "half", "shut")}
        shown = {name: 0.0 for name in keys}
        for i in range(2000):  # every 0.05% of the loop
            t = i / 20
            visible = [name for name in keys if at(keys[name], t) == 1]
            self.assertEqual(len(visible), 1, f"at {t}% visible frames: {visible}")
            shown[visible[0]] += cards.LOOP * 1000 / 2000
        self.assertGreater(shown["shut"], 100, "the eye should be fully closed for a moment")
        self.assertLess(shown["half"] + shown["shut"], 400, "a blink is quick")
        self.assertGreater(cards.BLINK[0], cards.GLANCE[3], "blink only while looking straight ahead")
        # with motion off, only the open eye shows
        art, _, _, _ = cards.eye(svg.THEMES["dark"])
        self.assertIn('class="half" opacity="0"', art)
        self.assertIn('class="shut" opacity="0"', art)

    def test_detection_box_follows_the_blink(self):
        for theme in ("dark", "light"):
            th = svg.THEMES[theme]
            boxes = {}
            for g in ET.fromstring(self.svg(theme)).iter(f"{self.NS}g"):
                label, path = g.find(f"{self.NS}text"), g.find(f"{self.NS}path")
                if g.get("class") in ("open", "half", "shut") and label is not None and path is not None:
                    boxes[g.get("class")] = (float((label.text or "0").split()[-1]), path.get("stroke"), g.get("opacity"))
            self.assertEqual(set(boxes), {"open", "half", "shut"})
            conf = [boxes[k][0] for k in ("open", "half", "shut")]
            self.assertTrue(conf[0] > conf[1] > 0.25 > conf[2], f"confidence must drop as the eye closes: {conf}")
            self.assertEqual([boxes[k][1] for k in ("open", "half", "shut")], [th["green"], th["accent"], th["red"]])
            self.assertEqual([boxes[k][2] for k in ("open", "half", "shut")], [None, "0", "0"])

    def test_closed_eye_is_a_thin_lid_line(self):
        art, _, _, _ = cards.eye(svg.THEMES["dark"])
        shut = re.search(r'<g class="shut"[^>]*>(.*?)</g>', art)
        self.assertIsNotNone(shut)
        rows = {float(y) for y in re.findall(r'y="([\d.]+)"', shut.group(1) if shut else "")}
        self.assertLessEqual(len(rows), 2, "closed eye should be a line, not a squashed eye")

    def test_even_padding_and_rhythm(self):
        root = ET.fromstring(self.svg())
        h = float(root.get("height") or 0)
        texts = [(float(t.get("y") or 0), t.text) for t in root.iter(f"{self.NS}text") if t.text]
        prompts = sorted(y for y, s in texts if s == "❯")
        for p in prompts[2:]:  # now, plan and the final prompt: one gap below the previous output
            above = max(y for y, s in texts if y < p)
            self.assertAlmostEqual(p - above, 34, delta=0.5)
        top_pad = (prompts[0] - 10) - 40          # first prompt's cap top to the title-bar line
        bottom_pad = (h - 1.5) - (prompts[-1] + 4)  # cursor bottom to the card edge
        self.assertLessEqual(abs(top_pad - bottom_pad), 4, f"{top_pad:.1f} vs {bottom_pad:.1f}")


class Typing(unittest.TestCase):
    """The intro types each command once; the eye, cursor and route keep looping."""
    NS = "{http://www.w3.org/2000/svg}"
    COMMANDS = ["fastfetch", "cat about.txt", "cat now.txt", "cat plan.txt"]

    def svg(self, theme="dark"):
        return cards.terminal(CFG, svg.THEMES[theme], board.when(NOW))

    def blocks(self, theme="dark"):
        """Reveal groups in document order: prompt, typed prefixes, entered command, output."""
        found = []
        for g in ET.fromstring(self.svg(theme)).iter(f"{self.NS}g"):
            kind = g.get("class")
            if kind not in ("on", "key", "ln"):
                continue
            style = dict(part.split(":", 1) for part in (g.get("style") or "").split(";") if part)
            start = int(style["animation-delay"].removesuffix("ms"))
            end = start + int(style.get("animation-duration", "0ms").removesuffix("ms"))
            item = SimpleNamespace(start=start, end=end, text="".join(g.itertext()),
                                   hidden=g.get("opacity") == "0")
            if kind == "on" and item.text == "❯":
                found.append(SimpleNamespace(prompt=item, states=[], entered=None, output=[]))
            elif kind == "key":
                found[-1].states.append(item)
            elif kind == "on":
                found[-1].entered = item
            else:
                found[-1].output.append(item)
        return found

    def test_each_command_is_typed_key_by_key(self):
        typed = [b for b in self.blocks() if b.states]
        self.assertEqual([b.entered.text for b in typed], self.COMMANDS)
        for b in typed:
            cmd = b.entered.text
            self.assertEqual([s.text for s in b.states], [cmd[:k] + cards.CURSOR for k in range(len(cmd) + 1)])
            self.assertEqual(b.states[0].start, b.prompt.start, "the cursor waits next to the prompt")
            for a, c in zip(b.states, b.states[1:]):
                self.assertEqual(a.end, c.start, "one prefix at a time: no gap, no overlap")
            self.assertEqual(b.states[-1].end, b.entered.start, "Enter swaps in the finished command")
            keys = [c.start - a.start for a, c in zip(b.states[1:], b.states[2:])]
            self.assertTrue(all(30 <= k <= 120 for k in keys), keys)

    def test_motion_off_shows_the_finished_card(self):
        for b in self.blocks("light"):
            self.assertFalse(b.prompt.hidden)
            self.assertTrue(all(s.hidden for s in b.states), "no half-typed commands with motion off")
            self.assertFalse(b.entered and b.entered.hidden)

    def test_output_waits_for_its_command(self):
        found = self.blocks()
        for b in found[:-1]:
            self.assertTrue(b.output)
            self.assertTrue(all(o.start >= b.entered.start for o in b.output), "output before Enter")
        for before, after in zip(found, found[1:]):
            self.assertGreater(after.prompt.start, max(o.start for o in before.output), "prompt before output")
        self.assertEqual(found[-1].states, [], "the last prompt just waits with a blinking cursor")
        self.assertLessEqual(found[-1].prompt.start, 7500, "the whole intro stays short")

    def test_typing_plays_once_while_the_rest_keeps_moving(self):
        css = re.search(r"<style>(.*?)</style>", self.svg(), re.S)
        self.assertIsNotNone(css)
        rules = dict(re.findall(r"\.([\w-]+)\{([^{}]*)\}", css.group(1) if css else ""))
        for once in ("on", "key", "ln"):
            self.assertNotIn("infinite", rules[once])
        for loop in ("look", "open", "half", "shut", "cur", "go"):
            self.assertIn("infinite", rules[loop])

    def test_every_redraw_types_the_same(self):
        self.assertEqual(self.svg(), self.svg())


class ProjectCards(unittest.TestCase):
    NS = "{http://www.w3.org/2000/svg}"

    def card(self, p, theme="dark"):
        info = fetch.offline(CFG)["projects"].get(p["id"])
        return cards.project(p, info, svg.THEMES[theme], board.when(NOW))

    def test_words_start_with_a_capital(self):
        for p in CFG["projects"]:
            for t in ET.fromstring(self.card(p)).iter(f"{self.NS}text"):
                s = (t.text or "").strip()
                core = s.rstrip("…")
                if not s or (core in p["note"] and not p["note"].startswith(core)):
                    continue  # empty, or a wrapped continuation of a sentence
                self.assertFalse(s[0].isalpha() and not s[0].isupper(), f"{p['id']}: lowercase {s!r}")

    def test_cards_use_the_same_real_names_as_the_board(self):
        for p in CFG["projects"]:
            if p.get("chip"):
                self.assertEqual(p["name"], p["chip"])
            self.assertIn(svg.esc(p["name"]), self.card(p, "light"))

    def test_public_projects_get_gold_pins_and_nothing_is_dashed(self):
        for p in CFG["projects"]:
            for theme in ("dark", "light"):
                out = self.card(p, theme)
                public = p["kind"] == "public"
                self.assertEqual("url(#pvg)" in out and "url(#phg)" in out, public, f"{p['id']}: gold pins")
                self.assertEqual("url(#pv)" in out and "url(#ph)" in out, not public, f"{p['id']}: silver pins")
                self.assertNotIn("stroke-dasharray", out, f"{p['id']}: dashed outline")

    def test_projects_heading_starts_with_a_capital(self):
        self.assertIn("Things I built", cards.heading(*cards.HEADINGS[0][1:], svg.THEMES["dark"]))


class Safety(unittest.TestCase):
    def test_placeholder_text_is_rejected(self):
        bad = svg.document(10, 10, svg.text(1, 1, "None", 5, "#000"), "x")
        with self.assertRaises(ValueError):
            build.check({"bad.svg": bad})

    def test_missing_merged_prs_fail_instead_of_drawing_zeroes(self):
        class Fake:
            calls = 0

            def get(self, path, **params):
                if path.startswith("search/"):
                    return {"items": []}
                return {"stargazers_count": 1, "language": "Python", "pushed_at": NOW, "size": 1, "private": False}

        cfg = {"login": "someone", "projects": [], "contributions": [{"id": "a", "repo": "o/r"}]}
        with self.assertRaises(RuntimeError):
            fetch.collect(cfg, Fake())


if __name__ == "__main__":
    unittest.main()
