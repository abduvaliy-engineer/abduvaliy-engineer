import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'update_activity.py'


class ActivityTests(unittest.TestCase):
    def test_rejects_inconsistent_total(self):
        spec = importlib.util.spec_from_file_location('activity', SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        calendar = {'totalContributions': 9, 'weeks': [{'contributionDays': [
            {'date': '2026-01-01', 'contributionCount': 3, 'contributionLevel': 'FIRST_QUARTILE'},
        ]}]}
        with self.assertRaises(ValueError):
            module.render(calendar, 'abduvaliy-engineer')

    def test_renders_calendar_as_valid_svg(self):
        self.assertTrue(SCRIPT.exists(), 'activity generator is missing')
        spec = importlib.util.spec_from_file_location('activity', SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        calendar = {'totalContributions': 3, 'weeks': [
            {'contributionDays': [
                {'date': '2026-01-01', 'contributionCount': 0, 'contributionLevel': 'NONE'},
                {'date': '2026-01-02', 'contributionCount': 3, 'contributionLevel': 'FIRST_QUARTILE'},
            ]}
        ]}
        svg = module.render(calendar, 'abduvaliy-engineer')
        element = ET.fromstring(svg)
        self.assertEqual(element.tag, '{http://www.w3.org/2000/svg}svg')
        self.assertIn('3 contributions', svg)
        self.assertIn('2026-01-01', svg)
        self.assertIn('2026-01-02', svg)
        self.assertIn('abduvaliy-engineer', svg)
        self.assertEqual(svg, module.render(calendar, 'abduvaliy-engineer'))


if __name__ == '__main__':
    unittest.main()
