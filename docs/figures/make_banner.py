"""Draw the README banner: a title over a decorative curve.

The curve is a fixed sum of Gaussians. It stands for no measurement or simulation and carries no values.

Run: python docs/figures/make_banner.py docs/figures/banner.svg
"""
import math
import sys

W, H = 1200, 250
X0, X1, BASE, TOP = 60, 1140, 210, 118
PEAKS = ((0.10, 0.025, 0.55), (0.22, 0.02, 0.9), (0.31, 0.03, 0.5), (0.47, 0.015, 1.0), (0.58, 0.02, 0.45), (0.80, 0.012, 0.7), (0.88, 0.01, 0.35))


def curve(n=240):
    """Points (x, y) of the decorative curve in SVG coordinates."""
    pts = []
    for i in range(n + 1):
        u = i / n
        v = min(1.0, sum(a * math.exp(-0.5 * ((u - c) / w) ** 2) for c, w, a in PEAKS))
        pts.append((X0 + u * (X1 - X0), BASE - v * (BASE - TOP)))
    return pts


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
<text class="sub" x="{X0}" y="90">Code and notes for my MSc thesis</text>
<path class="fill" d="{area}"/>
<path class="curve" d="{line}"/>
<line class="base" x1="{X0}" x2="{X1}" y1="{BASE}" y2="{BASE}"/>
</svg>
"""


if __name__ == "__main__":
    open(sys.argv[1], "w", encoding="utf-8").write(banner_svg())
