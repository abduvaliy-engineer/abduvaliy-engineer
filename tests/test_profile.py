"""Offline tests for the profile drawings. Standard library only; no network."""
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

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
