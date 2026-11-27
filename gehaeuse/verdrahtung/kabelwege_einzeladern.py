# -*- coding: utf-8 -*-
# Einzeladern-Ansicht der Reader-Verdrahtung (Draufsicht). Liest cad/kabelwege_v2.json (schreibt build_prototyp_v2.py)
# und fuer den Hintergrund die V2-FCStd. Jede Ader wird einzeln entlang ihres Bandes gezeichnet (Band = Buendel im 3D-Modell).
# Aufruf: freecadcmd -c "exec(open('gehaeuse/verdrahtung/kabelwege_einzeladern.py').read())"  -> gehaeuse/ansichten/kabelwege_einzeladern.png
# Annahmen: Pinfolge der I2C-Leiste von -y nach +y = SCL, SDA, VCC, GND (Daten-Seite -y wie im Modell) -> am Board pruefen.
#           VCC aller Reader an Ader "V+" (5 V oder 3,3 V offen, NP_WIRES), dritte Strang-Ader gestrichelt = Reserve/zweite Spannung.
import json, os
import FreeCAD as App
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
# Projektwurzel: Umgebungsvariable MATTE_PROJ, sonst aktuelles Verzeichnis (wenn es die Projektwurzel ist), sonst Standardpfad dieses Macs
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
GEH = os.path.join(PROJ, "gehaeuse")
J = json.load(open(os.path.join(GEH, "pruefberichte", "kabelwege_v2.json")))
R = J["readers"]; PATHS = {p["name"]: p for p in J["paths"]}
def band(prefix): return [p for n, p in PATHS.items() if n.startswith(prefix)][0]
COL = dict(SDA="#1565c0", SCL="#2e9e44", VCC="#d62828", GND="#111111", V2="#f08c00")
STEP = 0.75   # Abstand der Einzeladern in der Zeichnung [mm]

def offset_poly(pts, d):
    """achsparallele Polylinie um d nach links (in Laufrichtung) versetzen"""
    segs = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if abs(x1 - x0) < 1e-9 and abs(y1 - y0) < 1e-9: continue
        horiz = abs(y1 - y0) < abs(x1 - x0)
        if horiz: segs.append(("h", y0 + (d if x1 > x0 else -d)))
        else:     segs.append(("v", x0 + (-d if y1 > y0 else d)))
    if not segs: return pts
    out = []
    k0, c0 = segs[0]; x, y = pts[0]
    out.append((x, c0) if k0 == "h" else (c0, y))
    for (ka, ca), (kb, cb) in zip(segs, segs[1:]):
        if ka == kb: continue
        out.append((cb, ca) if ka == "h" else (ca, cb))
    kn, cn = segs[-1]; x, y = pts[-1]
    out.append((x, cn) if kn == "h" else (cn, y))
    return out

def from_point(pts, p):
    """Rest der Polylinie ab dem Punkt p (liegt auf einem Segment)"""
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        if min(x0, x1) - 1e-6 <= p[0] <= max(x0, x1) + 1e-6 and min(y0, y1) - 1e-6 <= p[1] <= max(y0, y1) + 1e-6:
            return [tuple(p)] + [tuple(q) for q in pts[k + 1:]]
    raise ValueError("Punkt %s nicht auf Band" % (p,))

def tap(pts, x):
    """Abzweigpunkt bei x auf dem ersten waagrechten Segment, das x enthaelt"""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if abs(y1 - y0) < 1e-6 and min(x0, x1) - 1e-6 <= x <= max(x0, x1) + 1e-6: return (x, y0)
    if abs(pts[0][0] - x) < 1e-3: return tuple(pts[0])   # Band beginnt senkrecht an der Leiste
    raise ValueError("kein Abzweig bei x=%.2f" % x)

def drop_end(p):
    if p["drop"]: return p["drop"]
    for q in PATHS.values():   # endet am Ende eines anderen Bandes -> dessen Abstieg zur TCA-Leiste nehmen
        if q is not p and q["drop"] and abs(q["pts"][-1][0] - p["pts"][-1][0]) < 1e-3 and abs(q["pts"][-1][1] - p["pts"][-1][1]) < 1e-3: return q["drop"]
    return None

fig, ax = plt.subplots(figsize=(14, 14))
# Hintergrund aus dem Modell
d = App.openDocument(os.path.join(GEH, "modell", "Prototyp_15x15_Deckel_V2.FCStd"))
ax.add_patch(Rectangle((0.7, 0.7), 148.5, 148.5, fill=False, ec="#777", lw=1.0))
for o in d.Objects:
    n = o.Name
    if not hasattr(o, "Shape") or o.Shape.isNull(): continue
    b = o.Shape.BoundBox
    if n.startswith("REF_PN532_") and n.count("_") == 2:
        ax.add_patch(Rectangle((b.XMin, b.YMin), b.XLength, b.YLength, fc="#eef2f6", ec="#b6c2cc", lw=0.8, zorder=0))
        ax.text(b.Center.x, b.YMax - 3, "Reader " + n[-2:], ha="center", va="top", fontsize=10, color="#5b6b78", zorder=1)
    elif n.startswith("REF_Waegezelle"):
        ax.add_patch(Rectangle((b.XMin, b.YMin), b.XLength, b.YLength, fc="#cfcfcf", ec="#777", lw=0.8, zorder=1, alpha=0.8))
        ax.text(b.Center.x, b.Center.y, "Waegezelle " + n[-1], ha="center", va="center", fontsize=9, color="#555", zorder=1)
    elif n in ("REF_TCA9548A_A", "REF_TCA9548A_B", "REF_Loetverteiler"):
        ax.add_patch(Rectangle((b.XMin, b.YMin), b.XLength, b.YLength, fc="#d8f0d0", ec="#5a8f4e", lw=1.0, zorder=1))
        ax.text(b.Center.x, b.Center.y, {"REF_TCA9548A_A": "TCA A", "REF_TCA9548A_B": "TCA B", "REF_Loetverteiler": "Loet-\nverteiler"}[n], ha="center", va="center", fontsize=10, fontweight="bold", color="#2f5e26", zorder=6)
    elif n in ("REF_ESP32_C6", "REF_HX711_A", "REF_HX711_B"):
        ax.add_patch(Rectangle((b.XMin, b.YMin), b.XLength, b.YLength, fc="none", ec="#d9a066", lw=0.8, ls="--", zorder=1))
        ax.text(b.XMin + 1, b.YMin + 1, n[4:] + " (Unterteil)", fontsize=7, color="#b07a3c", zorder=1)
def line(pts, c, lw=1.3, ls="-", z=5):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=c, lw=lw, ls=ls, zorder=z, solid_capstyle="round", solid_joinstyle="round")

# Stiftleisten (I2C, 4 Pins waagrecht) und Pinbeschriftung
NAMES = ["SCL", "SDA", "VCC", "GND"]
for k, r in R.items():
    for q, py in enumerate(r["pin_y"]):
        line([(r["row"], py), (r["tip"], py)], "#8a8a8a", lw=2.2, z=4)
    lx = r["tip"] + r["side"] * 0.6
    if k == "11":
        for q, py in enumerate(r["pin_y"]):
            ax.text(r["row"] - 0.5, py, NAMES[q], fontsize=6, ha="right", va="center", color=COL[NAMES[q]], zorder=7)

# Daten: Band -> Reader in Reihenfolge der Adern im Band
DATA = [("Daten 11 + 21", ["21", "11"]), ("Daten 12 + 11/21", ["12"]), ("Daten 22", ["22"]), ("Daten 13 + 23", ["23", "13"]),
        ("Daten 31 ", ["31"]), ("Daten 32 + 31", ["32"]), ("Daten 33", ["33"])]
ends = {"A": [], "B": []}
for prefix, rds in DATA:
    p = band(prefix); pts = [tuple(q) for q in p["pts"]]; n = p["n"]
    de = drop_end(p)
    for s_, rk in enumerate(rds):
        r = R[rk]; t = tap(pts, r["apx"])
        rest = from_point(pts, t)
        for w_, sig in enumerate(("SCL", "SDA")):
            slot = 2 * s_ + w_; dd = (slot - (n - 1) / 2) * STEP
            path = offset_poly(rest, dd) if len(rest) > 1 else rest
            start = (r["apx"], r["pin_y"][0 if sig == "SCL" else 1])
            full = [start, (start[0], path[0][1]) if abs(path[0][0] - start[0]) < 2 else (path[0][0], start[1])] + path
            if de: full.append((de[0], path[-1][1]))
            line(full, COL[sig])
        if de:
            tca = "A" if de[0] < 75 else "B"; ends[tca].append((rk, de[0], de[1]))
for tca, lst in ends.items():   # je Abstieg an der TCA-Leiste eine Beschriftung mit allen Readern
    grp = {}
    for rk, x, y in lst: grp.setdefault((round(x, 1), round(y)), []).append(rk)
    for (x, y), rks in grp.items():
        ax.annotate("Reader " + ", ".join(sorted(set(rks))) + "\n-> je eigener Kanal", (x, y), xytext=(x + (-16 if tca == "A" else 4), y - 3.5),
                    fontsize=7, color="#222", va="center", zorder=8, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#999", lw=0.5, alpha=0.9))

# Versorgung: Strang je Reihe (NP Adern: V+, Reserve/zweite Spannung, GND), Abzweig an jedem Reader
SUP = [("Strang Reihe 1", ["11", "21", "31"]), ("Strang Reihe 2/3", ["12", "22", "32"]), ("Strang Reihe 3", ["13", "23", "33"])]
sig3 = [("VCC", "-"), ("V2", "--"), ("GND", "-")][:J["NP"]]
for prefix, rds in SUP:
    p = band(prefix); pts = [tuple(q) for q in p["pts"]]; n = p["n"]
    for w_, (sig, ls) in enumerate(sig3):
        dd = (w_ - (n - 1) / 2) * STEP
        line(offset_poly(pts, dd), COL[sig], ls=ls, lw=1.2)
    for rk in rds:
        r = R[rk]
        for w_, (sig, ls) in enumerate(sig3):
            if sig == "V2": continue
            dd = (w_ - (n - 1) / 2) * STEP
            yb = offset_poly(pts, dd)[0][1] if abs(pts[0][1] - pts[1][1]) < 1e-6 else None
            yb = [q for q in offset_poly(pts, dd) if True][-1][1]
            line([(r["apx"] + (0.3 if sig == "GND" else -0.3), r["pin_y"][2 if sig == "VCC" else 3]), (r["apx"] + (0.3 if sig == "GND" else -0.3), yb)], COL[sig], lw=1.2)
# Bus Verteiler -> TCA_A -> TCA_B (4 Adern)
for prefix in ("Verteiler -> TCA_A", "TCA_A -> TCA_B"):
    p = band(prefix); pts = [tuple(q) for q in p["pts"]]
    pts = [pts[0]] + [q for a_, q in zip(pts, pts[1:]) if abs(q[0] - a_[0]) > 1e-6 or abs(q[1] - a_[1]) > 1e-6]
    for w_, sig in enumerate(("VCC", "GND", "SDA", "SCL")):
        dd = (w_ - 1.5) * STEP
        try: pp = offset_poly(pts, dd)
        except Exception: pp = pts
        line(pp, COL[sig], lw=1.2, ls=(0, (4, 1.5)))
# Schlaufe ueber den Waegespalt (4 Adern vom Unterteil) - nur Markierung
v = J["verteiler"]
ax.annotate("4 Adern von unten\n(Schlaufe ueber den Waegespalt)", ((v[0] + v[2]) / 2 - 2, v[3]), xytext=(2, 70), fontsize=8, color="#c2185b",
            arrowprops=dict(arrowstyle="->", color="#c2185b"), zorder=8)
for sig, lab in (("SDA", "SDA (je Reader eigenes Paar zum TCA-Kanal)"), ("SCL", "SCL"), ("VCC", "VCC / V+ (Kette je Reihe)"), ("V2", "3. Strang-Ader: zweite Spannung/Reserve (NP_WIRES offen)"), ("GND", "GND")):
    ax.plot([], [], color=COL[sig], lw=2.5, ls="--" if sig == "V2" else "-", label=lab)
ax.plot([], [], color="#777", lw=2, ls=(0, (4, 1.5)), label="Bus Verteiler -> TCA A -> TCA B (VCC, GND, SDA, SCL)")
ax.plot([], [], color="#8a8a8a", lw=3, label="I2C-Stiftleiste Reader (4 Pins, waagrecht)")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.09), ncol=2, fontsize=9, frameon=False)
ax.set_xlim(-2, 152); ax.set_ylim(-2, 152); ax.set_aspect("equal")
ax.set_title("Reader-Verdrahtung als Einzeladern (Draufsicht, Adern haengen unter dem Traeger)  -  Stand %s\n"
             "Annahme Pinfolge I2C-Leiste (von -y nach +y): SCL, SDA, VCC, GND - am Board pruefen. Adern seitlich auseinandergezogen, im Modell liegen sie als Buendel." % J["stand"], fontsize=10)
fig.tight_layout()
out = os.path.join(GEH, "ansichten", "kabelwege_einzeladern.png"); fig.savefig(out, dpi=130, bbox_inches="tight"); print("ok", out)
