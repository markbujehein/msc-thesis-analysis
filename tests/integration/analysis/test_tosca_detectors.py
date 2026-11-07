import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "analysis"))
from tosca_detectors import read_detectors, write_csv  # noqa: E402

IDF = Path(sys.prefix) / "instrument" / "TOSCA_Definition_2016.xml"  # run in the mantid environment


class TestToscaDetectors(unittest.TestCase):
    def test_counts_and_ranges(self):
        detectors = read_detectors(IDF)
        for bank, (e_lo, e_hi, t_lo, t_hi) in {"back": (2.690, 4.297, 127.0, 140.8), "front": (2.688, 4.294, 38.9, 53.1)}.items():
            d = [x for x in detectors if x["bank"] == bank]
            self.assertEqual(len(d), 70)
            self.assertAlmostEqual(min(x["efixed_mev"] for x in d), e_lo, places=3)
            self.assertAlmostEqual(max(x["efixed_mev"] for x in d), e_hi, places=3)
            self.assertAlmostEqual(min(x["two_theta_deg"] for x in d), t_lo, places=1)
            self.assertAlmostEqual(max(x["two_theta_deg"] for x in d), t_hi, places=1)

    def test_incomplete_table_raises(self):
        text = IDF.read_text()
        with tempfile.TemporaryDirectory() as d:
            broken = Path(d) / "broken.xml"
            broken.write_text(text.replace('name="Detector #1"', 'name="Gone"', 1).replace("Efixed", "Efixe", 1))
            with self.assertRaises(ValueError):
                read_detectors(broken)

    def test_csv_round_trip(self):
        detectors = read_detectors(IDF)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "d.csv"
            write_csv(detectors, path)
            lines = path.read_text().splitlines()
            self.assertEqual(lines[0], "bank,two_theta_deg,efixed_mev")
            self.assertEqual(len(lines), 141)


if __name__ == "__main__":
    unittest.main()
