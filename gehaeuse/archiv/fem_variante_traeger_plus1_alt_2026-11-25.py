# -*- coding: utf-8 -*-
# FEM-Studie "Was waere wenn": Traeger 1 mm hoeher + Verbindung Deckel-Traeger. Aendert das V2-Modell NICHT.
# Traeger wird im FEM-Modell oberhalb der Zellenauflage (Z_UP) in z gestreckt (8,5 -> 8,5 + DH), Deckel sitzt DH hoeher.
# Varianten: lose (nur Traeger traegt) / 8 Verbindungspunkte (Clip oder Schraube, sonst Luft) / vollflaechig verbunden (obere Grenze).
# Nutzt Hilfsfunktionen aus fem_traeger_deckel.py (bis vor dessen Lastfaellen).
# Aufruf: freecadcmd -c "exec(open('cad/fem_variante_traeger_plus1.py').read())"
import os, json
import FreeCAD as App, Part
from FreeCAD import Vector as V
_src = open("/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte/cad/fem_traeger_deckel.py", encoding="utf-8").read()
exec(_src[:_src.index("rep = []")])
LOADSUM = []

PV = [
    ("DH", 1.0, "Annahme", "Studie: Traeger hoeher [mm] (8,5 -> 9,5)"),
    ("T_RAW", 8.5, "bestaetigt", "Traegerhoehe V2 (Z_SPLIT - Z_UP)"),
    ("CON_D", 5.0, "Annahme", "Studie: Durchmesser Verbindungspunkt (Clip/Schraube als starre Bruecke modelliert)"),
    ("CON_GAP", 0.2, "Annahme", "Studie: Luft Deckel-Traeger ausserhalb der Verbindungspunkte (keine Kontaktkraft modelliert)"),
]
Q = {n: v for n, v, s, q in PV}
DH = Q["DH"]; f = (Q["T_RAW"] + DH) / Q["T_RAW"]
CON_XY = [(4, 4), (75, 3.5), (146, 4), (146.5, 75), (146, 146), (75, 146.5), (4, 146), (3.5, 75)]   # Ecken + Randmitten (Aussenrahmen)

mz = App.Matrix(); mz.move(V(0, 0, -Z_UP)); ms = App.Matrix(); ms.scale(1, 1, f); mz = ms.multiply(mz)
mb = App.Matrix(); mb.move(V(0, 0, Z_UP)); mz = mb.multiply(mz)
TRs = TR.transformGeometry(mz)
ZS = Z_SPLIT + DH
print("Traeger gestreckt: z", round(TRs.BoundBox.ZMin, 2), "-", round(TRs.BoundBox.ZMax, 2), "gueltig", TRs.isValid())

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
        zr = Z_UP + P["CLR_TOP"] * f
        rel = min(minuz(data, lambda p, c=c: abs(p.z - zr) < 0.08 and c[0] < p.x < c[2] and c[1] < p.y < c[3])[0] for c in CELLS)
        out[nm] = dict(stop=-min(st), stops=[-u for u in st], sag=-min(d.z for p, d in data), relief=-rel, vm995=pct(vm, 0.995),
                       load=LOADSUM[-1], soll=sum(n for _, n in loads), nodes=mesh.FemMesh.NodeCount)
        print(tag, nm, out[nm])
    App.closeDocument(doc.Name)
    return out

RESV = {}
# A) lose: nur Traeger (+1) traegt, Last auf Traeger-Oberseite der Felder
RESV["A lose"] = run_variant("A_lose", TRs, ZS, True)
# B) 8 Verbindungspunkte, Deckel mit 0,2 mm Luft darueber
g = Q["CON_GAP"]
DEb = DE.copy(); DEb.translate(V(0, 0, DH + g))
cons = [Part.makeCylinder(Q["CON_D"] / 2, g + 2.0, V(x, y, ZS - 1.0)) for x, y in CON_XY]
B = TRs.fuse([DEb] + cons).removeSplitter()
print("Variante B Koerper:", len(B.Solids))
RESV["B 8 Punkte"] = run_variant("B_8Punkte", B.Solids[0] if len(B.Solids) == 1 else B, Z_FLOOR + DH + g, False)
# C) vollflaechig verbunden
DEc = DE.copy(); DEc.translate(V(0, 0, DH))
C = TRs.fuse(DEc).removeSplitter()
RESV["C verbunden"] = run_variant("C_verbunden", C.Solids[0] if len(C.Solids) == 1 else C, Z_FLOOR + DH, False)

ref = json.load(open(OUT + "fem_ergebnisse.json"))
L = ["STUDIE Traeger +%.1f mm (%.1f -> %.1f mm) und Verbindung Deckel-Traeger  (E = %.0f MPa, Vollmaterial, Zellen starr)" % (DH, Q["T_RAW"], Q["T_RAW"] + DH, P["E_PLA"]),
     "Groesse: hoechste Absenkung an einem Anschlag (Spalt %.2f mm). Unter 0,40 mm = ok (0,1 mm Reserve)." % P["STOP_GAP"],
     "Referenz V2 (8,5 mm): lose  Ecke %.2f / verteilt %.2f mm;  vollflaechig verbunden  Ecke %.2f / verteilt %.2f mm" % (
         -min(ref["LF1 5 kg auf Feld 1|1 (Ecke vorne links)"]["stops"]), -min(ref["LF4 10 kg gleichmaessig auf 9 Feldern"]["stops"]),
         -min(ref["LV1 5 kg Behaelter auf Feld 1|1 (Ecke)"]["stops"]), -min(ref["LV4 10 kg gleichmaessig auf 9 Feldern"]["stops"]))]
for v, r in RESV.items():
    for nm, x in r.items():
        lim = P["M_FELD"] if nm.startswith("Ecke") else P["M_VOLL"]
        L.append("%-12s %-15s Anschlag %.2f mm  -> %s; Last bis Anschlag ca. %.1f kg; Freistich-Absenkung %.2f; max %.2f mm; vM99,5 %.1f MPa  [Last %.1f/%.1f N]" % (
            v, nm, x["stop"], "ok" if x["stop"] < P["STOP_GAP"] - 0.1 else "KRITISCH", lim * P["STOP_GAP"] / x["stop"], x["relief"], x["sag"], x["vm995"], x["load"], x["soll"]))
L.append("Annahmen: Verbindungspunkte starr (kein Lochspiel), ausserhalb keine Kontaktkraft (B konservativ fuer Druck, optimistisch fuer Schub).")
open(OUT + "studie_traeger_plus1.txt", "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(RESV, open(OUT + "studie_traeger_plus1.json", "w"), indent=1)
print("\n".join(L))
