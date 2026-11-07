import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "docs" / "figures"))
from make_banner import banner_svg, curve  # noqa: E402


class BannerTests(unittest.TestCase):
    def test_is_one_svg_with_one_curve(self):
        svg = banner_svg()
        self.assertTrue(svg.startswith("<svg"))
        self.assertEqual(svg.count('<path class="curve"'), 1)

    def test_curve_stays_inside_the_plot(self):
        pts = curve()
        self.assertTrue(all(60 <= x <= 1140 and 118 <= y <= 210 for x, y in pts))

    def test_carries_no_data_values(self):
        svg = banner_svg()
        for word in ("meV", "TOSCA", "TSC", "stretch", "thymol", "Thymol", "DOS"):
            self.assertNotIn(word, svg)
        self.assertEqual(re.findall(r">(\d+)<", svg), [])

    def test_has_dark_mode(self):
        self.assertIn("prefers-color-scheme: dark", banner_svg())


if __name__ == "__main__":
    unittest.main()
