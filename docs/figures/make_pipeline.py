W_, H_ = 172, 66
rows = {-1: 40, 0: 160, 1: 256, 2: 352, 3: 448, 4: 544, 5: 640, 6: 736}
N = {  # key: (x, row, status, title, detail)
 "A": (60, 0, "done", "Predicted structures", "Salager 2010, COD"),
 "B": (260, 0, "done", "PDB supercells", "thymol_cif/, pdb/"),
 "C": (460, 0, "done", "GAFF2 MD", "OpenMM, md/, 10 K"),
 "E": (660, 0, "done", "Hessian", "cell, supercell"),
 "F": (860, 0, "wip", "INS per detector", "abinslib"),
 "D": (460, 1, "done", "Vibrational DOS", "from velocities"),
 "FF": (460, -1, "planned", "Other force fields", ("MACE and others", "for higher accuracy")),
 "R": (60, 2, "done", "TOSCA runs", "two thymol runs"),
 "S": (260, 2, "done", "Reduction", "Mantid"),
 "T": (460, 2, "done", "Reduced spectra", "git-ignored"),
 "SYN": (60, 3, "planned", "Synthetic data", "stand-in runs"),
 "Q": (460, 3, "planned", "QENS check", "exploratory"),
 "IR": (60, 4, "planned", "FTIR and Raman", "band positions in meV"),
 "VR": (60, 5, "planned", "VESUVIO runs", "foil in / foil out"),
 "VM": (260, 5, "planned", "Foil difference", "Mantid LoadVesuvio"),
 "VF": (460, 5, "planned", "Compton profiles", "fit per mass: H, C, O"),
 "VH": (660, 5, "planned", "H momentum width", "kinetic energy of H"),
 "VD": (260, 6, "planned", "Diffraction", "back angles, 0.5-8 A"),
 "U": (1000, 2, "wip", "Comparison", "simulation vs data"),
 "W": (1000, 3, "planned", "Bayesian band model", "dynesty"),
}
def box(k):
    x, r, s, t, d = N[k]; y = rows[r]
    d = [d] if isinstance(d, str) else list(d)
    h = H_ + 16 * (len(d) - 1)
    label = {"done": "DONE", "wip": "WIP", "planned": "PLANNED"}[s]
    lines = "".join(f'<text class="d" x="{x+14}" y="{y+41+16*i}">{ln}</text>' for i, ln in enumerate(d))
    return (f'<g class="n {s}"><rect x="{x}" y="{y}" width="{W_}" height="{h}" rx="8"/>'
            f'<text class="t" x="{x+14}" y="{y+23}">{t}</text>{lines}'
            f'<text class="s" x="{x+14}" y="{y+58+16*(len(d)-1)}">{label}</text></g>')
def right(k): x, r, *_ = N[k]; return (x + W_, rows[r] + H_ / 2)
def left(k): x, r, *_ = N[k]; return (x, rows[r] + H_ / 2)
def top(k): x, r, *_ = N[k]; return (x + W_ / 2, rows[r])
def bottom(k):
    x, r, s, t, d = N[k]; return (x + W_ / 2, rows[r] + H_ + (16 * (len(d) - 1) if not isinstance(d, str) else 0))
def edge(p, q, via="", cls=""):
    return f'<path class="e {cls}" d="M{p[0]},{p[1]} {via} L{q[0]},{q[1]}" marker-end="url(#a)"/>'
def join(k):  # dotted line from box k to the comparison column, ending on the comparison box
    return f'<path class="e dot" d="M{right(k)[0]},{right(k)[1]} L970,{right(k)[1]} L970,{right("T")[1]}"/>'
E = [edge(right("A"), left("B")), edge(right("B"), left("C")), edge(right("C"), left("E")), edge(right("E"), left("F")),
     edge(bottom("C"), top("D")), edge(bottom("FF"), top("C"), cls="dot"), edge(right("R"), left("S")), edge(right("S"), left("T")),
     edge(top("SYN"), bottom("R"), cls="dot"), edge(bottom("T"), top("Q"), cls="dot"),
     edge(right("VR"), left("VM"), cls="dot"), edge(right("VM"), left("VF"), cls="dot"), edge(right("VF"), left("VH"), cls="dot"),
     edge(bottom("VR"), left("VD"), via=f"L{bottom('VR')[0]},{left('VD')[1]}", cls="dot"),
     edge(right("F"), top("U"), via=f"L{top('U')[0]},{right('F')[1]}"),
     edge(right("T"), left("U")), join("IR"), join("VH"),
     edge(bottom("U"), top("W"), cls="dot")]
labels = [(-1, "Simulation"), (2, "Measurement: TOSCA"), (4, "Measurement: FTIR and Raman"), (5, "Measurement: VESUVIO")]
lab = "".join(f'<text class="lane" x="60" y="{rows[r]-10}">{t}</text>' for r, t in labels)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 826" role="img" aria-labelledby="t d">
<title id="t">Pipeline of the thymol project with the status of every step</title>
<desc id="d">Simulation path from predicted crystal structures through molecular dynamics and the Hessian to a simulated INS spectrum, the TOSCA measurement path through reduction, and planned FTIR, Raman, VESUVIO, QENS and synthetic-data branches, all meeting in an overlay of simulation and measurement.</desc>
<style>
:root{{--ink:#1C2A39;--muted:#5C6B7C;--done:#1E7B5C;--wip:#B26A00;--plan:#6C7A8D}}
@media (prefers-color-scheme: dark){{:root{{--ink:#E6EDF3;--muted:#9AA7B5;--done:#4FC3A0;--wip:#F0B450;--plan:#9AA7B5}}}}
text{{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;fill:var(--ink)}}
.t{{font-size:14px;font-weight:600}} .d{{font-size:12px;fill:var(--muted);font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}}
.s{{font-size:11px;font-weight:700;letter-spacing:.04em}}
.lane{{font-size:13px;fill:var(--muted)}}
.done rect{{fill:var(--done);fill-opacity:.12;stroke:var(--done);stroke-width:1.5}} .done .s{{fill:var(--done)}}
.wip rect{{fill:var(--wip);fill-opacity:.14;stroke:var(--wip);stroke-width:1.5;stroke-dasharray:6 4}} .wip .s{{fill:var(--wip)}}
.planned rect{{fill:none;stroke:var(--plan);stroke-width:1.5;stroke-dasharray:2 4}} .planned .s{{fill:var(--plan)}}
.e{{fill:none;stroke:var(--muted);stroke-width:1.5}} .e.dot{{stroke-dasharray:2 4}}
#a path{{fill:var(--muted)}}
</style>
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
{lab}
{"".join(E)}
{"".join(box(k) for k in N)}
</svg>
'''
open("docs/figures/pipeline.svg", "w", encoding="utf-8").write(svg)
