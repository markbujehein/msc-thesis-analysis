"""Per-detector TOSCA geometry from Mantid's instrument definition (standard library only)."""
import re
from pathlib import Path

DETECTOR = re.compile(r'<location[^>]* t="([\d.]+)"[^>]*/>\s*<parameter name="Efixed">\s*<value val="([\d.]+)"')


def read_detectors(idf_path):
    """List of {"bank": "back"|"front", "two_theta_deg", "efixed_mev"} in file order.

    Raises ValueError unless there are exactly 70 detectors in each bank.
    """
    text = Path(idf_path).read_text()
    detectors = []
    for bank in ("back", "front"):
        block = re.search(rf'<type name="{bank}">(.*?)</type>', text, flags=re.S)
        found = DETECTOR.findall(block.group(1)) if block else []
        if len(found) != 70:
            raise ValueError(f"bank {bank}: expected 70 detectors, found {len(found)}")
        detectors += [{"bank": bank, "two_theta_deg": float(t), "efixed_mev": float(e)} for t, e in found]
    return detectors


def write_csv(detectors, path):
    lines = ["bank,two_theta_deg,efixed_mev"]
    lines += [f"{d['bank']},{d['two_theta_deg']},{d['efixed_mev']}" for d in detectors]
    Path(path).write_text("\n".join(lines) + "\n")
