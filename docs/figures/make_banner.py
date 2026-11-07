"""Draw the README banner: a title over a decorative curve.

The curve is seeded random Gaussians arranged like a molecular-crystal spectrum. It stands for no measurement or simulation and carries no values.

Run: python docs/figures/make_banner.py docs/figures/banner.svg
"""
import math
import random
import sys

W, H = 1200, 250
X0, X1, BASE, TOP = 60, 1140, 210, 118


def _peaks(rng):
    """Peaks (centre, width, height) in 0..1 shaped like the INS spectrum of a molecular crystal.

    Dense and low in the lattice region, many mid-height lines in the fingerprint region (widths grow with
    energy, as instrument resolution does), a quiet gap, then a few high-energy lines. Seeded, so the file is stable.
    """
    peaks = [(rng.uniform(0.02, 0.2), rng.uniform(0.003, 0.006), rng.uniform(0.15, 0.6)) for _ in range(30)]
    for _ in range(42):
        c = rng.uniform(0.2, 0.5)
        peaks.append((c, 0.002 + 0.012 * c, rng.uniform(0.1, 0.9)))
    peaks += [(rng.uniform(0.78, 0.9), rng.uniform(0.003, 0.006), rng.uniform(0.35, 0.9)) for _ in range(6)]
    return peaks


def curve(n=900):
    """Points (x, y) of the decorative curve in SVG coordinates."""
    peaks = _peaks(random.Random(7))
    values = []
    for i in range(n + 1):
        u = i / n
        values.append(0.04 * (1 - u) + sum(a * math.exp(-0.5 * ((u - c) / w) ** 2) for c, w, a in peaks))
    top = max(values)
    return [(X0 + i / n * (X1 - X0), BASE - v / top * (BASE - TOP)) for i, v in enumerate(values)]


def banner_svg():
    pts = curve()
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{line} L{X1},{BASE} L{X0},{BASE} Z"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Molecular dynamics and neutron spectra</title>
<style>
:root{{--ink:#1C2A39;--muted:#5C6B7C;--line:#2F4FD8}}
@media (prefers-color-scheme: dark){{:root{{--ink:#E6EDF3;--muted:#9AA7B5;--line:#8BA2FF}}}}
text{{font-family:Georgia,"Times New Roman",serif;fill:var(--ink)}}
.title{{font-size:48px;font-weight:700}}
.sub{{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;font-size:20px;fill:var(--muted)}}
.fill{{fill:var(--line);opacity:.14}}
.curve{{fill:none;stroke:var(--line);stroke-width:2;stroke-linejoin:round}}
.base{{stroke:var(--muted);stroke-width:1.5}}
</style>
<text class="title" x="{X0}" y="62">Molecular dynamics and neutron spectra</text>
<text class="sub" x="{X0}" y="90">Simulation and analysis code</text>
<path class="fill" d="{area}"/>
<path class="curve" d="{line}"/>
<line class="base" x1="{X0}" x2="{X1}" y1="{BASE}" y2="{BASE}"/>
</svg>
"""


if __name__ == "__main__":
    open(sys.argv[1], "w", encoding="utf-8").write(banner_svg())
