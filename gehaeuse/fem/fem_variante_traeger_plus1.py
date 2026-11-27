# -*- coding: utf-8 -*-
# FEM-Studie Traeger +1 mm (9,5 mm) mit den echten Passzapfen Deckel-Traeger. Rechnet auf dem aktuellen V2-Modell
# (Prototyp_15x15_Deckel_V2.FCStd), aendert es NICHT. Alte Fassung (gestreckter 8,5-mm-Traeger): archiv/fem_variante_traeger_plus1_alt_2026-11-25.py
# Varianten (Steifigkeit A < B <= Wirklichkeit <= C):
#   A lose      : nur der Traeger traegt, Last auf seiner Oberseite (Deckel liegt nur auf, ohne Zapfen)
#   B Zapfen    : Deckel mit CON_GAP Luft ueber dem Traeger, nur ueber die 8 Passzapfen verbunden (Presssitz starr).
#                 Kein Kontakt modelliert -> untere Grenze (in Wirklichkeit drueckt der Deckel zusaetzlich auf den Traeger)
#   C verbunden : Deckel vollflaechig mit dem Traeger verbunden (obere Grenze, z. B. geklebt)
# Zapfenlage und Bohrungsmasse kommen aus dem Pruefbericht (pruefbericht_deckel_v2.txt), Hoehen aus dem Modell.
# Aufruf (aus der Projektwurzel): freecadcmd -c "exec(open('gehaeuse/fem/fem_variante_traeger_plus1.py').read())"
import os, re, json
import FreeCAD as App, Part
from FreeCAD import Vector as V
# Projektwurzel: Umgebungsvariable MATTE_PROJ, sonst aktuelles Verzeichnis (wenn es die Projektwurzel ist), sonst Standardpfad dieses Macs
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
GEH = os.path.join(PROJ, "gehaeuse")
_src = open(os.path.join(GEH, "fem", "fem_traeger_deckel.py"), encoding="utf-8").read()
exec(_src[:_src.index("rep = []")])
LOADSUM = []

PV = [
    ("CON_GAP", 0.2, "Annahme", "Variante B: Luft Deckel-Traeger ausserhalb der Zapfen (keine Kontaktkraft modelliert)"),
]
Q = {n: v for n, v, s, q in PV}

# Passzapfen aus dem Pruefbericht
rp = open(os.path.join(GEH, "pruefberichte", "pruefbericht_deckel_v2.txt"), encoding="utf-8").read()
mline = [l for l in rp.splitlines() if l.startswith("Passzapfen Deckel->Traeger")][0]
m = re.search(r"(\d+) Stueck D([\d.]+) x ([\d.]+).*Bohrung D([\d.]+) tief ([\d.]+).*Fase ([\d.]+)", mline)
N_PIN, PIN_D, PIN_L, HOLE_D, HOLE_T, CH = int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)), float(m.group(6))
PINS = [(float(a), float(b)) for a, b in re.findall(r"\(([\d.]+)\|([\d.]+)\)", mline.split("Lage:")[1])]
assert len(PINS) == N_PIN, (N_PIN, PINS)
T_TR = Z_SPLIT - Z_UP
print("Traeger %.2f mm, %d Zapfen D%.1f, Bohrung D%.1f tief %.1f" % (T_TR, N_PIN, PIN_D, HOLE_D, HOLE_T))

def hole_fill(x, y):   # Bohrung samt Quetschrippen und Fase ausfuellen = Zapfen sitzt starr (idealer Presssitz)
    c = Part.makeCylinder(HOLE_D / 2, HOLE_T, V(x, y, Z_SPLIT - HOLE_T))
    k = Part.makeCone(HOLE_D / 2, HOLE_D / 2 + CH, CH, V(x, y, Z_SPLIT - CH))
    return c.fuse(k)
FILLS = [hole_fill(x, y) for x, y in PINS]

def one_solid(sh, tag):
    sh = sh.removeSplitter()
    print(tag, "Koerper:", len(sh.Solids), "gueltig", sh.isValid())
    assert len(sh.Solids) == 1, "%s: %d Koerper statt 1" % (tag, len(sh.Solids))
    return sh.Solids[0]

def run_variant(tag, shape, loadz, on_traeger):
    shp = imprint(shape, [rect(*PATCH[0], Z_UP), rect(*PATCH[1], Z_UP)])
    if on_traeger: shp = imprint(shp, [rect(*FIELDS[k], loadz) for k in FIELDS])
    doc, part, ana, solver, mesh = setup("FEM_" + tag, shp)
    fixed = faces_at(shp, Z_UP, -1, PATCH[0]) + faces_at(shp, Z_UP, -1, PATCH[1])
    lf = {k: faces_at(shp, loadz, +1, FIELDS[k]) for k in FIELDS}
    assert all(lf[k] for k in lf), "Lastflaechen fehlen: %s" % {k: len(v) for k, v in lf.items()}
    out = {}
    for nm, loads in (("Ecke 5 kg", [(lf["11"], P["M_FELD"] * G)]), ("verteilt 10 kg", [(lf[k], P["M_VOLL"] * G / 9) for k in sorted(lf)])):
        data, vm = solve(doc, part, ana, solver, fixed, loads, OUT + "var_%s_%s" % (tag, nm[:4]))
        near = lambda p, xy, r: (p.x - xy[0]) ** 2 + (p.y - xy[1]) ** 2 < r * r
        st = [minuz(data, lambda p, s=s: abs(p.z - Z_UP) < 0.05 and near(p, s, 5.0))[0] for s in STOPS]
        zr = Z_UP + P["CLR_TOP"]
        rel = min(minuz(data, lambda p, c=c: abs(p.z - zr) < 0.08 and c[0] < p.x < c[2] and c[1] < p.y < c[3])[0] for c in CELLS)
        out[nm] = dict(stop=-min(st), stops=[-u for u in st], sag=-min(d.z for p, d in data), relief=-rel, vm995=pct(vm, 0.995),
                       load=LOADSUM[-1], soll=sum(n for _, n in loads), nodes=mesh.FemMesh.NodeCount)
        print(tag, nm, out[nm])
    App.closeDocument(doc.Name)
    return out

RESV = {}
# A) lose
RESV["A lose"] = run_variant("A_lose", TR, Z_SPLIT, True)
# B) nur Zapfen, Deckel mit Luft darueber (Zapfen des Deckels ragen in die ausgefuellten Bohrungen)
g = Q["CON_GAP"]
DEb = DE.copy(); DEb.translate(V(0, 0, g))
B = one_solid(TR.fuse(FILLS + [DEb]), "Variante B")
RESV["B Zapfen"] = run_variant("B_Zapfen", B, Z_FLOOR + g, False)
# C) vollflaechig verbunden
C = one_solid(TR.fuse(FILLS + [DE]), "Variante C")
RESV["C verbunden"] = run_variant("C_verbunden", C, Z_FLOOR, False)

ref = json.load(open(OUT + "fem_ergebnisse.json"))
L = ["STUDIE Traeger %.1f mm mit %d Passzapfen D%.1f Deckel-Traeger  (aktuelles V2-Modell, E = %.0f MPa, Vollmaterial, Zellen starr)" % (T_TR, N_PIN, PIN_D, P["E_PLA"]),
     "Groesse: hoechste Absenkung an einem Anschlag (Spalt %.2f mm). Unter 0,40 mm = ok (0,1 mm Reserve)." % P["STOP_GAP"],
     "Referenz alter Stand (8,5 mm, ohne Zapfen, fem_ergebnisse.json): lose  Ecke %.2f / verteilt %.2f mm;  vollflaechig verbunden  Ecke %.2f / verteilt %.2f mm" % (
         -min(ref["LF1 5 kg auf Feld 1|1 (Ecke vorne links)"]["stops"]), -min(ref["LF4 10 kg gleichmaessig auf 9 Feldern"]["stops"]),
         -min(ref["LV1 5 kg Behaelter auf Feld 1|1 (Ecke)"]["stops"]), -min(ref["LV4 10 kg gleichmaessig auf 9 Feldern"]["stops"]))]
for v, r in RESV.items():
    for nm, x in r.items():
        lim = P["M_FELD"] if nm.startswith("Ecke") else P["M_VOLL"]
        L.append("%-12s %-15s Anschlag %.2f mm  -> %s; Last bis Anschlag ca. %.1f kg; Freistich-Absenkung %.2f; max %.2f mm; vM99,5 %.1f MPa  [Last %.1f/%.1f N, %d Knoten]" % (
            v, nm, x["stop"], "ok" if x["stop"] < P["STOP_GAP"] - 0.1 else "KRITISCH", lim * P["STOP_GAP"] / x["stop"], x["relief"], x["sag"], x["vm995"], x["load"], x["soll"], x["nodes"]))
L.append("Annahmen: Zapfen starr im Presssitz (kein Spiel); B ohne Kontaktkraft ausserhalb der Zapfen (untere Grenze), C vollflaechig (obere Grenze). Linear, Last bis Anschlag linear hochgerechnet.")
open(OUT + "studie_traeger_plus1.txt", "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(RESV, open(OUT + "studie_traeger_plus1.json", "w"), indent=1)
print("\n".join(L))
