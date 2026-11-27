# -*- coding: utf-8 -*-
# FEM-Studie V2: Durchbiegung Traeger (gewogene Platte) und Deckel unter Behaelterlast. CalculiX + Gmsh aus dem FreeCAD-Paket.
# Fragen: (1) Bleibt der Traeger unter Last frei von Anschlaegen, Zelle und Unterteil (kein Kraftnebenschluss)?
#         (2) Drueckt ein schwerer Behaelter den Deckel auf die Reader (Druckplatte hat 0,2 mm Luft)?
# Aufruf (headless, aus der Projektwurzel): freecadcmd -c "exec(open('gehaeuse/fem/fem_traeger_deckel.py').read())"
# Ausgabe: gehaeuse/fem/ergebnisse/pruefbericht_fem.txt, *.png, fem_ergebnisse.json (Rohdaten in Unterordnern, nicht im Repo)
import os, json, math
import FreeCAD as App, Part, ObjectsFem
from FreeCAD import Vector as V

# Projektwurzel: Umgebungsvariable MATTE_PROJ, sonst aktuelles Verzeichnis (wenn es die Projektwurzel ist), sonst Standardpfad dieses Macs
PROJ = os.environ.get("MATTE_PROJ") or (os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "gehaeuse", "skripte")) else "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte")
GEH = os.path.join(PROJ, "gehaeuse")
OUT = os.path.join(GEH, "fem", "ergebnisse") + "/"; os.makedirs(OUT, exist_ok=True)
PARAMS = [
    # (Name, Wert, Status, Quelle)
    ("E_PLA", 2500.0, "Annahme", "E-Modul PLA gedruckt [MPa]; Vollmaterial ca. 3500, FDM je nach Fuellung/Richtung 2000-3000. Ergebnis skaliert mit 1/E"),
    ("NU_PLA", 0.35, "Annahme", "Querkontraktion PLA"),
    ("R_PLA", 40.0, "Annahme", "Zugfestigkeit PLA gedruckt [MPa] (Vollmaterial ca. 50-60, quer zu den Schichten deutlich weniger)"),
    ("M_FELD", 5.0, "Annahme", "Last auf EINEM Feld [kg] (schwerer Behaelter, z. B. 2x2-Box voll)"),
    ("M_VOLL", 10.0, "Annahme", "Gesamtlast gleichmaessig auf allen 9 Feldern [kg] (= Nennlast 2 Zellen x 5 kg)"),
    ("MESH_MAX", 2.5, "Annahme", "max. Elementgroesse [mm]"),
    ("MESH_MIN", 0.5, "Annahme", "min. Elementgroesse [mm]"),
    ("STOP_GAP", 0.5, "bestaetigt", "aus build_prototyp_v2.py: Ueberlastspalt Sockel - Platte"),
    ("CLR_TOP", 0.8, "bestaetigt", "aus build_prototyp_v2.py: Freistich Platte ueber Zelle"),
    ("GAP_V", 1.2, "bestaetigt", "aus build_prototyp_v2.py: Fuge Schuerze - Schulter / Kragen - Platte"),
    ("PLUG_GAP", 0.2, "bestaetigt", "aus build_prototyp_v2.py: Luft Druckplatte - Reader-Rueckseite"),
]
P = {n: v for n, v, s, q in PARAMS}
G = 9.81
Z_UP, GF_H = 20.1, 4.75   # Z_SPLIT und Z_TOP werden aus dem Modell gelesen (Traeger +1 mm, 24.11.)
CELL_W = 12.7
PATCH = [(92.0, 50 - CELL_W/2, 112.5, 50 + CELL_W/2), (37.5, 100 - CELL_W/2, 58.0, 100 + CELL_W/2)]   # Auflage auf Zellen-Freiende (Loecher +-5 mm bis Zellenende)
STOPS = [(50.05, 10), (101.15, 12), (50.05, 140), (101.15, 140)]                                       # Anschlagsockel (Steg-Mitten)
CELLS = [(37.5, 43.65, 112.5, 56.35), (37.5, 93.65, 112.5, 106.35)]

src = App.openDocument(os.path.join(GEH, "modell", "Prototyp_15x15_Deckel_V2.FCStd"))
TR = src.getObject("Traeger").Shape.copy(); DE = src.getObject("Deckel").Shape.copy()
App.closeDocument(src.Name)
Z_SPLIT, Z_TOP = round(TR.BoundBox.ZMax, 3), round(DE.BoundBox.ZMax, 3)   # Trennebene / Oberkante Deckel
Z_FLOOR = Z_TOP - GF_H
print("Modell: Z_UP %.2f  Z_SPLIT %.2f  Z_TOP %.2f  Z_FLOOR %.2f" % (Z_UP, Z_SPLIT, Z_TOP, Z_FLOOR))

def rect(x0, y0, x1, y1, z): return Part.Face(Part.makePolygon([V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z), V(x0, y0, z)]))
def imprint(solid, faces):
    res, _ = solid.generalFuse(faces)
    sols = res.Solids
    assert len(sols) == 1, "Imprint lieferte %d Koerper" % len(sols)
    return sols[0]
def faces_at(shape, z, nz, inside=None):
    out = []
    for i, f in enumerate(shape.Faces):
        bb = f.BoundBox
        if abs(bb.ZMin - z) > 1e-4 or abs(bb.ZMax - z) > 1e-4: continue
        n = f.normalAt(*f.Surface.parameter(f.CenterOfMass)) if hasattr(f.Surface, "parameter") else f.normalAt(0, 0)
        if n.z * nz < 0.9: continue
        c = f.CenterOfMass
        if inside and not (inside[0] < c.x < inside[2] and inside[1] < c.y < inside[3]): continue
        out.append("Face%d" % (i + 1))
    return out

FIELDS = {"%d%d" % (i + 1, j + 1): (50 * i, 50 * j, 50 * i + 50, 50 * j + 50) for i in range(3) for j in range(3)}
TRi = imprint(imprint(TR, [rect(*PATCH[0], Z_UP), rect(*PATCH[1], Z_UP)]), [rect(*FIELDS[k], Z_SPLIT) for k in FIELDS])   # nacheinander: gemeinsam zerfiel der Koerper

def setup(name, shape):
    doc = App.newDocument(name)
    part = doc.addObject("Part::Feature", "Koerper"); part.Shape = shape
    ana = ObjectsFem.makeAnalysis(doc, "Analyse")
    solver = ObjectsFem.makeSolverCalculiXCcxTools(doc, "CCX"); ana.addObject(solver)
    solver.AnalysisType = "static"; solver.GeometricalNonlinearity = "linear"
    mat = ObjectsFem.makeMaterialSolid(doc, "PLA"); m = mat.Material
    m.update({"Name": "PLA gedruckt", "YoungsModulus": "%g MPa" % P["E_PLA"], "PoissonRatio": str(P["NU_PLA"]), "Density": "1240 kg/m^3"})
    mat.Material = m; ana.addObject(mat)
    mesh = ObjectsFem.makeMeshGmsh(doc, "Netz"); mesh.Shape = part
    mesh.CharacteristicLengthMax = P["MESH_MAX"]; mesh.CharacteristicLengthMin = P["MESH_MIN"]; mesh.ElementOrder = "2nd"
    mesh.SecondOrderLinear = True   # gerade Kanten: vermeidet verzerrte Elemente (nonpositive jacobian) in duennen Bereichen
    ana.addObject(mesh); doc.recompute()
    from femmesh.gmshtools import GmshTools
    err = GmshTools(mesh).create_mesh()
    if err: print("Gmsh:", err)
    print(name, "Netz: Knoten", mesh.FemMesh.NodeCount, "Volumenelemente", mesh.FemMesh.VolumeCount)
    return doc, part, ana, solver, mesh

def solve(doc, part, ana, solver, fixed, loads, wd):
    for o in [o for o in ana.Group if o.TypeId.startswith("Fem::Constraint") or o.isDerivedFrom("Fem::FemResultObject")]:
        ana.removeObject(o); doc.removeObject(o.Name)
    fx = ObjectsFem.makeConstraintFixed(doc, "Auflage"); fx.References = [(part, fixed)]; ana.addObject(fx)
    for k, (faces, newton) in enumerate(loads):
        f = ObjectsFem.makeConstraintForce(doc, "Last%d" % k); f.References = [(part, faces)]
        f.Force = "%.4f N" % newton   # Einheit noetig: Zahl allein = mN
        f.Direction = (part, [faces[0]]); f.Reversed = True; ana.addObject(f)
    doc.recompute()
    from femtools import ccxtools
    os.makedirs(wd, exist_ok=True)
    fea = ccxtools.FemToolsCcx(ana, solver); fea.update_objects(); fea.setup_working_dir(wd); fea.setup_ccx()
    msg = fea.check_prerequisites()
    if msg: raise RuntimeError(msg)
    def zsum():
        inp = open(fea.inp_file_name).read(); t = 0.0; i_ = inp.find("*CLOAD")
        while i_ >= 0:
            j_ = inp.find("\n*", i_ + 7); j_ = len(inp) if j_ < 0 else j_
            for l_ in inp[i_:j_].splitlines()[1:]:
                q_ = [x.strip() for x in l_.split(",")]
                if len(q_) == 3 and q_[1] == "3": t += float(q_[2])
            i_ = inp.find("*CLOAD", j_)
        return t
    fea.write_inp_file(); fsum = zsum()
    if fsum > 0:   # Flaechennormale zeigt bei manchen Flaechen nach unten -> Richtung drehen, Last muss nach -z
        for o in ana.Group:
            if o.TypeId == "Fem::ConstraintForce": o.Reversed = not o.Reversed
        doc.recompute(); fea.update_objects(); fea.write_inp_file(); fsum = zsum()
    fea.ccx_run(); fea.load_results()
    LOADSUM.append(-fsum)
    res = [o for o in ana.Group if o.isDerivedFrom("Fem::FemResultObject")][-1]
    nodes = res.Mesh.FemMesh.Nodes
    data = [(nodes[n], d) for n, d in zip(res.NodeNumbers, res.DisplacementVectors)]
    return data, list(res.vonMises)

def minuz(data, pred):
    vals = [d.z for (p, d) in data if pred(p)]
    return (min(vals), len(vals)) if vals else (float("nan"), 0)
def pct(vals, q): s = sorted(vals); return s[min(len(s) - 1, int(q * len(s)))]

rep = []; line = rep.append; RES = {}; LOADSUM = []
line("PRUEFBERICHT FEM  V2 Traeger + Deckel (linear-elastisch, CalculiX, Tetraeder 2. Ordnung)")
line("Material PLA: E = %.0f MPa (Annahme, Ergebnis ~ 1/E), nu = %.2f, Festigkeit %.0f MPa (Annahme)" % (P["E_PLA"], P["NU_PLA"], P["R_PLA"]))
line("Annahmen: Traeger vollmateriell (100 % Fuellung), Auflage auf den Zellen-Freienden starr eingespannt (Zellen selbst starr),")
line("          Deckel liegt auf der Traeger-Oberseite auf (dort fest), Lasten als Flaechenlast auf die Felder.")
line("Durchbiegung der Zellen selbst ist NICHT enthalten (siehe Messung Punkt 3); sie kommt bei den Spalten zum Unterteil hinzu.")

# ---------------- (1) Traeger ----------------
doc, part, ana, solver, mesh = setup("FEM_Traeger", TRi)
fixed = faces_at(TRi, Z_UP, -1, PATCH[0]) + faces_at(TRi, Z_UP, -1, PATCH[1])
top = {k: faces_at(TRi, Z_SPLIT, +1, FIELDS[k]) for k in FIELDS}
line("--- (1) Traeger: Netz %d Knoten / %d Elemente, Auflageflaechen %d, Lastflaechen je Feld %s" % (
    mesh.FemMesh.NodeCount, mesh.FemMesh.VolumeCount, len(fixed), "/".join(str(len(top[k])) for k in sorted(top))))
cases = [("LF1 %g kg auf Feld 1|1 (Ecke vorne links)" % P["M_FELD"], [(top["11"], P["M_FELD"] * G)]),
         ("LF2 %g kg auf Feld 3|3 (Ecke hinten rechts)" % P["M_FELD"], [(top["33"], P["M_FELD"] * G)]),
         ("LF3 %g kg auf Feld 2|2 (Mitte)" % P["M_FELD"], [(top["22"], P["M_FELD"] * G)]),
         ("LF4 %g kg gleichmaessig auf 9 Feldern" % P["M_VOLL"], [(top[k], P["M_VOLL"] * G / 9) for k in sorted(top)])]
Z_SK = Z_UP - 3.0   # Schuerzen-Unterkante (SKIRT_H 3,0); tiefster Punkt des Traegers sind Rasthaken
plots = []
for nm, loads in cases:
    data, vm = solve(doc, part, ana, solver, fixed, loads, OUT + "ccx_" + nm[:3])
    near = lambda p, xy, r: (p.x - xy[0]) ** 2 + (p.y - xy[1]) ** 2 < r * r
    st = [minuz(data, lambda p, s=s: abs(p.z - Z_UP) < 0.05 and near(p, s, 5.0))[0] for s in STOPS]
    rel = min(minuz(data, lambda p, c=c: abs(p.z - (Z_UP + P["CLR_TOP"])) < 0.05 and c[0] < p.x < c[2] and c[1] < p.y < c[3])[0] for c in CELLS)
    sk = minuz(data, lambda p: abs(p.z - Z_SK) < 0.05 and (min(p.x, p.y) < 3.0 or max(p.x, p.y) > 145.5))[0]
    edge = minuz(data, lambda p: abs(p.z - Z_UP) < 0.05 and (min(p.x, p.y) < 6.5 or max(p.x, p.y) > 142))[0]
    umax = max(d.Length for p, d in data); uzmin = min(d.z for p, d in data)
    s995 = pct(vm, 0.995); smax = max(vm)
    worst = min(st)
    line("%s   [Lastsumme im Solver %.2f N, Soll %.2f N]" % (nm, LOADSUM[-1], sum(n_ for _, n_ in loads)))
    line("   max. Verschiebung %.3f mm, max. Absenkung %.3f mm" % (umax, -uzmin))
    line("   Absenkung an den Anschlaegen (Platte ueber Sockel, Spalt %.2f): %s mm -> Rest %.2f mm %s" % (
        P["STOP_GAP"], " / ".join("%.3f" % -u for u in st), P["STOP_GAP"] + worst, "ok" if P["STOP_GAP"] + worst > 0.1 else "<-- KRITISCH"))
    line("   Freistich ueber den Zellen (Spalt %.2f): max. Absenkung %.3f -> Rest %.2f mm %s" % (P["CLR_TOP"], -rel, P["CLR_TOP"] + rel, "ok" if P["CLR_TOP"] + rel > 0.1 else "<-- KRITISCH"))
    line("   Schuerzen-Unterkante (Fuge %.2f zur Schulter): %.3f -> Rest %.2f mm; Plattenrand ueber Kragen (%.2f): %.3f -> Rest %.2f mm" % (
        P["GAP_V"], -sk, P["GAP_V"] + sk, P["GAP_V"], -edge, P["GAP_V"] + edge))
    line("   Vergleichsspannung von Mises: 99,5-%%-Wert %.2f MPa, Maximum %.2f MPa (Spitzen an Einspannkanten = numerisch ueberhoeht) -> Sicherheit %.1f" % (s995, smax, P["R_PLA"] / s995))
    RES[nm] = dict(umax=umax, uz_min=uzmin, stops=st, relief=rel, skirt=sk, edge=edge, vm995=s995, vmmax=smax)
    plots.append((nm, [(p.x, p.y, d.z) for p, d in data if abs(p.z - Z_UP) < 0.05 or abs(p.z - Z_SPLIT) < 0.05]))
App.closeDocument(doc.Name)

# ---------------- (2) Deckel ----------------
DEi = DE   # kein Aufpraegen: Ebene schneidet die Druckplatten-Ansaetze
doc, part, ana, solver, mesh = setup("FEM_Deckel", DEi)
fixedD = faces_at(DEi, Z_SPLIT, -1)
floor11 = faces_at(DEi, Z_FLOOR, +1, FIELDS["11"]); floor22 = faces_at(DEi, Z_FLOOR, +1, FIELDS["22"])
plug_z = min(f.BoundBox.ZMin for f in DEi.Faces)
line("--- (2) Deckel: Netz %d Knoten / %d Elemente, Auflageflaechen %d, Feldboden 1|1 %d Flaeche(n), Unterseite Druckplatte z = %.2f" % (
    mesh.FemMesh.NodeCount, mesh.FemMesh.VolumeCount, len(fixedD), len(floor11), plug_z))
for nm, fl, fld in (("LD1 %g kg Behaelter auf Feld 1|1" % P["M_FELD"], floor11, FIELDS["11"]), ("LD2 %g kg Behaelter auf Feld 2|2" % P["M_FELD"], floor22, FIELDS["22"])):
    data, vm = solve(doc, part, ana, solver, fixedD, [(fl, P["M_FELD"] * G)], OUT + "ccx_" + nm[:3])
    pl = minuz(data, lambda p: abs(p.z - plug_z) < 0.05 and fld[0] < p.x < fld[2] and fld[1] < p.y < fld[3])[0]
    fl_ = minuz(data, lambda p: abs(p.z - Z_FLOOR) < 0.05 and fld[0] < p.x < fld[2] and fld[1] < p.y < fld[3])[0]
    s995 = pct(vm, 0.995)
    line("%s   [Lastsumme im Solver %.2f N, Soll %.2f N]" % (nm, LOADSUM[-1], P["M_FELD"] * G))
    line("   Absenkung Feldboden %.3f mm, Unterseite Druckplatte %.3f mm; Luft zum Reader %.2f -> Rest %.2f mm %s" % (
        -fl_, -pl, P["PLUG_GAP"], P["PLUG_GAP"] + pl, "ok (Reader bleibt lastfrei)" if P["PLUG_GAP"] + pl > 0.05 else "<-- Druckplatte liegt auf dem Reader auf"))
    line("   von Mises 99,5-%%-Wert %.2f MPa, Maximum %.2f MPa -> Sicherheit %.1f" % (s995, max(vm), P["R_PLA"] / s995))
    RES[nm] = dict(plug=pl, floor=fl_, vm995=s995)
App.closeDocument(doc.Name)
# ---------------- (3) Verbund Traeger + Deckel (fest verbunden = obere Grenze der Steifigkeit) ----------------
# Real liegt der Deckel lose auf (nur 4 Zapfen, keine Schubuebertragung): Wirklichkeit liegt zwischen (1) und (3).
VB = TR.fuse(DE).removeSplitter()
VB = VB.Solids[0] if len(VB.Solids) == 1 else max(VB.Solids, key=lambda x: x.Volume)
VBi = imprint(VB, [rect(*PATCH[0], Z_UP), rect(*PATCH[1], Z_UP)])
doc, part, ana, solver, mesh = setup("FEM_Verbund", VBi)
fixedV = faces_at(VBi, Z_UP, -1, PATCH[0]) + faces_at(VBi, Z_UP, -1, PATCH[1])
floors = {k: faces_at(VBi, Z_FLOOR, +1, FIELDS[k]) for k in FIELDS}
line("--- (3) Verbund Traeger+Deckel fest verbunden (obere Grenze; real liegt der Deckel lose auf -> Wirklichkeit zwischen (1) und (3))")
line("    Netz %d Knoten / %d Elemente, Auflageflaechen %d, Bodenflaechen je Feld %s" % (
    mesh.FemMesh.NodeCount, mesh.FemMesh.VolumeCount, len(fixedV), "/".join(str(len(floors[k])) for k in sorted(floors))))
casesV = [("LV1 %g kg Behaelter auf Feld 1|1 (Ecke)" % P["M_FELD"], [(floors["11"], P["M_FELD"] * G)]),
          ("LV3 %g kg Behaelter auf Feld 2|2 (Mitte)" % P["M_FELD"], [(floors["22"], P["M_FELD"] * G)]),
          ("LV4 %g kg gleichmaessig auf 9 Feldern" % P["M_VOLL"], [(floors[k], P["M_VOLL"] * G / 9) for k in sorted(floors)])]
for nm, loads in casesV:
    data, vm = solve(doc, part, ana, solver, fixedV, loads, OUT + "ccx_" + nm[:3])
    near = lambda p, xy, r: (p.x - xy[0]) ** 2 + (p.y - xy[1]) ** 2 < r * r
    st = [minuz(data, lambda p, s=s: abs(p.z - Z_UP) < 0.05 and near(p, s, 5.0))[0] for s in STOPS]
    rel = min(minuz(data, lambda p, c=c: abs(p.z - (Z_UP + P["CLR_TOP"])) < 0.05 and c[0] < p.x < c[2] and c[1] < p.y < c[3])[0] for c in CELLS)
    sk = minuz(data, lambda p: abs(p.z - Z_SK) < 0.05 and (min(p.x, p.y) < 3.0 or max(p.x, p.y) > 145.5))[0]
    uzmin = min(d.z for p, d in data); s995 = pct(vm, 0.995); worst = min(st)
    line("%s   [Lastsumme im Solver %.2f N, Soll %.2f N]" % (nm, LOADSUM[-1], sum(n_ for _, n_ in loads)))
    line("   max. Absenkung %.3f mm; an den Anschlaegen %s mm -> Rest %.2f mm %s" % (
        -uzmin, " / ".join("%.3f" % -u for u in st), P["STOP_GAP"] + worst, "ok" if P["STOP_GAP"] + worst > 0.1 else "<-- KRITISCH"))
    line("   Freistich ueber Zellen Rest %.2f mm, Schuerze Rest %.2f mm, von Mises 99,5-%%-Wert %.2f MPa -> Sicherheit %.1f" % (
        P["CLR_TOP"] + rel, P["GAP_V"] + sk, s995, P["R_PLA"] / s995))
    RES[nm] = dict(uz_min=uzmin, stops=st, relief=rel, skirt=sk, vm995=s995)
App.closeDocument(doc.Name)
ph = [n for n, v, s, q in PARAMS if s in ("Annahme", "PLATZHALTER")]
line("--- Annahmen (Status 'Annahme'): " + ", ".join(ph))
open(OUT + "pruefbericht_fem.txt", "w", encoding="utf-8").write("\n".join(rep) + "\n")
json.dump(RES, open(OUT + "fem_ergebnisse.json", "w"), indent=1)

# ---------------- Bilder: Absenkung Traeger von oben ----------------
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, axs = plt.subplots(2, 2, figsize=(12, 11))
vmin = min(min(z for _, _, z in pts) for _, pts in plots)
for ax, (nm, pts) in zip(axs.flat, plots):
    xs, ys, zs = zip(*pts)
    sc_ = ax.scatter(xs, ys, c=[-z for z in zs], s=2, cmap="viridis", vmin=0, vmax=-vmin)
    for c in PATCH: ax.add_patch(plt.Rectangle((c[0], c[1]), c[2] - c[0], c[3] - c[1], fill=False, ec="red", lw=1.5))
    for s in STOPS: ax.plot(*s, "kx", ms=8)
    ax.set_aspect("equal"); ax.set_xlim(-2, 152); ax.set_ylim(-2, 152); ax.set_title(nm, fontsize=10)
fig.colorbar(sc_, ax=axs, shrink=0.6, label="Absenkung [mm]")
fig.suptitle("Traeger V2: Absenkung unter Last (rot = Auflage auf Zellen, x = Anschlagsockel), E = %.0f MPa" % P["E_PLA"])
fig.savefig(OUT + "traeger_absenkung.png", dpi=110)
print("\n".join(rep))
