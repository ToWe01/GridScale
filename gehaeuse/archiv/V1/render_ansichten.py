import FreeCAD as App, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
OUT = "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte/cad/ansichten/archiv_V1/"
import os
CAD = "/Users/tomke/Documents/Hochschule/Master/3.Semester/SmartSystems2/Projekt_Matte/cad/archiv/V1/"
VARIANT = os.environ.get("VARIANT", globals().get("VARIANT", "deckel"))
d = App.openDocument(CAD + ("Prototyp_15x15.FCStd" if VARIANT == "einteilig" else "Prototyp_15x15_Deckel.FCStd"))
def tris(shape, dz=0.0, tol=0.15):
    v, f = shape.tessellate(tol); v = np.array([[p.x, p.y, p.z + dz] for p in v]); return v[np.array(f)]
COL = {"Unterteil": (0.80, 0.81, 0.83), "Oberteil": (0.30, 0.45, 0.62), "Traeger": (0.45, 0.58, 0.72), "Deckel": (0.22, 0.32, 0.46)}
def render(name, objs, elev, azim, title, zoom=1.0):
    fig = plt.figure(figsize=(10, 8), dpi=130); ax = fig.add_subplot(111, projection="3d")
    L = np.array([0.4, -0.5, 0.8]); L /= np.linalg.norm(L)
    allp = []; allT = []; allC = []
    for (o, dz, col, a) in objs:
        T = tris(d.getObject(o).Shape, dz)
        n = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
        sh = 0.35 + 0.65*np.abs(n @ L)
        fc = np.clip(np.outer(sh, col), 0, 1); fc = np.hstack([fc, np.full((len(fc),1), a)])
        allT.append(T); allC.append(fc); allp.append(T.reshape(-1,3))
    ax.add_collection3d(Poly3DCollection(np.vstack(allT), facecolors=np.vstack(allC), edgecolors="none"))
    P_ = np.vstack(allp); c = (P_.max(0)+P_.min(0))/2; r = (P_.max(0)-P_.min(0)).max()/2/zoom
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev, azim); ax.set_axis_off(); ax.set_title(title)
    plt.tight_layout(); plt.savefig(OUT + name, facecolor="white"); plt.close(fig); print("ok", name)
refs = [o.Name for o in d.Objects if o.Name.startswith("REF_")]
def refcol(n): return (0.85,0.65,0.2) if "Waege" in n else (0.8,0.15,0.15) if "PN532" in n else (0.1,0.5,0.25) if any(k in n for k in ("ESP","HX","TCA")) else (0.25,0.25,0.25)
U = ("Unterteil", 0, COL["Unterteil"], 1)
if VARIANT == "einteilig":
    O = [("Oberteil", 0, COL["Oberteil"], 1)]
    render("01_iso_zusammengebaut.png", [U] + O, 28, -55, "Zusammengebaut")
    render("02_iso_explodiert.png", [U, ("Oberteil",45,COL["Oberteil"],1)] + [(n, 45 if "PN532" in n else 0, refcol(n), 1) for n in refs], 25, -55, "Explosionsansicht mit Bauteilen (Oberteil +45 mm)")
    render("03_unterteil_innen.png", [U] + [(n,0,refcol(n),1) for n in refs if "PN532" not in n], 50, -60, "Unterteil mit Waegezellen und Platinen")
    render("04_oberteil_unten.png", [("Oberteil",0,COL["Oberteil"],1)], -40, -60, "Oberteil von unten (Druckseite)")
    render("05_unterteil_unten.png", [U], -60, -90, "Unterteil von unten")
    render("06_detail_fuge_ecke.png", [U] + O, 10, -45, "Detail Ecke / Schattenfuge", zoom=4.0)
else:
    T = ("Traeger", 0, COL["Traeger"], 1); D = ("Deckel", 0, COL["Deckel"], 1)
    render("D01_iso_zusammengebaut.png", [U, T, D], 28, -55, "Variante Deckel: zusammengebaut")
    render("D02_iso_explodiert.png", [U, ("Traeger",35,COL["Traeger"],1), ("Deckel",70,COL["Deckel"],1)] + [(n, 35 if "PN532" in n else 0, refcol(n), 1) for n in refs], 22, -55, "Explosion: Unterteil / Traeger (+35) / Deckel (+70)")
    render("D03_traeger_oben.png", [T], 55, -60, "Traeger von oben: M4-Koepfe Freiende + Zentrierloecher")
    render("D04_deckel_unten.png", [D], -40, -60, "Deckel von unten: geschlossener Boden + Zentrierzapfen")
    render("D05_detail_fugen_ecke.png", [U, T, D], 10, -45, "Detail Ecke: Schattenfuge + Trennfuge Traeger/Deckel", zoom=4.0)
