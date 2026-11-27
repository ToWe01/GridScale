# -*- coding: utf-8 -*-
# Zeichnet den Verdrahtungs-Lageplan (Draufsicht, echte Positionen aus dem 3D-Modell) und die Pin-Tabelle.
# Eingaben: lageplan_daten.json (von lageplan_export.py), verdrahtung_v2.yml (Pins, Farben, Zuschnittlaengen).
# Ausgabe: lageplan_v2.pdf (Seite 1 Lageplan, Seite 2 Pin-Tabelle), lageplan_v2.png, pintabelle_v2.png
# Aufruf: python3 lageplan_zeichnen.py
import json, os, math, yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "lageplan_daten.json"), encoding="utf-8"))
Y = yaml.safe_load(open(os.path.join(HERE, "verdrahtung_v2.yml"), encoding="utf-8"))
O = D["objs"]

INK, MUTED, GRID = "#222222", "#8a8a8a", "#d9d9d9"
F = dict(VCC="#d62728", GND="#222222", DATA_A="#1f5fbf", DATA_B="#14a3a3", BUS="#8e44ad", HX="#2e8b57")
COLNAME = dict(RD="#d62728", BK="#222222", BU="#1f5fbf", YE="#e3b505", WH="#ffffff", GN="#2e8b57")
BOARD = dict(ESP="#3a3a3a", HX="#c0392b", TCA="#1f4e9c", VT="#c79a5a", PN="#d64541", CELL="#b8b8b8", USB="#9aa0a6")

def rect(ax, key, fc, ec=None, lw=1.0, alpha=1.0, z=2, hatch=None):
    x0, y0, x1, y1 = O[key][:4]
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec or fc, lw=lw, alpha=alpha, zorder=z, hatch=hatch))
    return (x0 + x1) / 2, (y0 + y1) / 2

def label(ax, x, y, txt, size=7.5, color="white", weight="bold", z=6, **kw):
    ax.text(x, y, txt, ha="center", va="center", fontsize=size, color=color, weight=weight, zorder=z, **kw)

def frame(ax, title):
    ax.add_patch(Rectangle((0, 0), 150, 150, fc="#fafafa", ec=INK, lw=1.6, zorder=0))
    for g in (50, 100):
        ax.plot([g, g], [0, 150], color=GRID, lw=0.8, ls="--", zorder=0.5)
        ax.plot([0, 150], [g, g], color=GRID, lw=0.8, ls="--", zorder=0.5)
    ax.set_xlim(-8, 158); ax.set_ylim(-14, 158); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=11, weight="bold", loc="left", color=INK)
    ax.annotate("", xy=(75, -6), xytext=(75, -12), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1))
    ax.text(80, -9, "vorne (USB-C)", fontsize=7.5, color=MUTED, va="center")
    ax.text(150, 152, "x/y in mm, Ansicht von oben (durch Deckel und Platte gesehen)", fontsize=6.5, color=MUTED, va="bottom", ha="right")
    for v in (0, 50, 100, 150):
        ax.text(v, -2.5, str(v), fontsize=6, color=MUTED, ha="center", va="top")
        ax.text(-1.5, v, str(v), fontsize=6, color=MUTED, ha="right", va="center")

def path(ax, pts, color, lw, z=4, ls="-"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color="white", lw=lw + 2.2, solid_capstyle="round", solid_joinstyle="round", zorder=z - 0.1)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="round", solid_joinstyle="round", zorder=z)

def tag(ax, x, y, n, color):
    ax.add_patch(plt.Circle((x, y), 3.3, fc="white", ec=color, lw=1.4, zorder=8))
    ax.text(x, y, str(n), ha="center", va="center", fontsize=6.8, weight="bold", color=color, zorder=9)

def mid(pfade):   # Punkt auf halber Länge des laengsten Pfads
    best = max(pfade, key=lambda p: sum(math.dist(a, b) for a, b in zip(p, p[1:])))
    L = sum(math.dist(a, b) for a, b in zip(best, best[1:])) / 2
    for a, b in zip(best, best[1:]):
        s = math.dist(a, b)
        if s >= L and s > 0: t = L / s; return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        L -= s
    return best[-1]

def umlaut(t):
    for a, b in (("ueber", "über"), ("Waege", "Wäge"), ("Loet", "Löt"), ("Buendel", "Bündel")): t = t.replace(a, b)
    return t

def kind(w):
    n = w["name"]
    if n.startswith("Daten"): return "DATA_B" if "TCA_B" in n else "DATA_A"
    if n.startswith("Strang"): return "VCC"
    if n.startswith("HX711"): return "HX"
    return "BUS"

W = D["wires"]
for i, w in enumerate(W, 1): w["nr"] = i
fig = plt.figure(figsize=(16.54, 11.69))   # A3 quer
fig.suptitle("GridScale - Prototyp 15x15 V2 - Verdrahtungs-Lageplan (Entwurf)", fontsize=14, weight="bold", x=0.02, ha="left", y=0.985)
fig.text(0.02, 0.952, "Positionen und Leitungswege aus build_prototyp_v2.py (Leitungen sind Platzhalter). Pins und Zuschnittlängen: verdrahtung_v2.yml. "
         "Elektrische Festlegungen (Spannung, GPIO, TCA-Kanäle) = Annahme, von der Elektronik zu bestätigen.", fontsize=8, color=MUTED)
axU = fig.add_axes([0.01, 0.30, 0.40, 0.63]); axP = fig.add_axes([0.42, 0.30, 0.40, 0.63])

# ---------- Ebene 1: Unterteil ----------
frame(axU, "1  Unterteil (fest, auf dem Boden)")
for k in ("REF_Waegezelle_1", "REF_Waegezelle_2"):
    cx, cy = rect(axU, k, BOARD["CELL"], alpha=0.55, z=1)
    label(axU, cx + 22, cy, "Wägezelle " + k[-1], color="#555555", size=7)
rect(axU, "REF_USB_Kabelwickel", BOARD["USB"], alpha=0.18, z=1, hatch="///")
label(axU, 131, 90, "Wickelkammer\nUSB-Kabel", color="#666666", size=6.5, weight="normal", rotation=90)
cx, cy = rect(axU, "REF_USB_C_Buchse", BOARD["USB"], alpha=0.35, z=1)
label(axU, 121, 8, "USB-C-Buchse\n(Delock 87824)", color="#555555", size=6.5, weight="normal")
cx, cy = rect(axU, "REF_ESP32_C6", BOARD["ESP"]); rect(axU, "REF_ESP32_C6_Stiftleisten", "#000000", alpha=0.55, z=2.5)
label(axU, cx, cy, "ESP32-C6-DevKitC-1")
for k, nm in (("REF_HX711_A", "HX711_A"), ("REF_HX711_B", "HX711_B")):
    cx, cy = rect(axU, k, BOARD["HX"]); rect(axU, k + "_Stiftleisten", "#000000", alpha=0.35, z=2.5)
    label(axU, cx, cy + 6, nm)
axU.add_patch(Rectangle((D["link_clip"][0] - 3, D["link_clip"][1] - 2), 6, 4, fc="white", ec=INK, lw=1, zorder=7))
axU.text(D["link_clip"][0] + 4.5, D["link_clip"][1] - 4.5, "Kabelgabel\n-> Schlaufe zur Platte", fontsize=6.5, color=INK, zorder=7)

# ---------- Ebene 2: Platte ----------
frame(axP, "2  Träger-Unterseite (an der Platte, bewegt sich mit)")
for k in ("REF_Waegezelle_1", "REF_Waegezelle_2"):
    rect(axP, k, BOARD["CELL"], alpha=0.22, z=1)
for i in (1, 2, 3):
    for j in (1, 2, 3):
        k = "REF_PN532_%d%d" % (i, j)
        x0, y0, x1, y1 = O[k][:4]
        axP.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=BOARD["PN"], ec=BOARD["PN"], alpha=0.12, lw=1.2, zorder=1.5))
        axP.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none", ec=BOARD["PN"], lw=1.2, zorder=1.6))
        side = D["i2c_side"]["%d%d" % (i, j)]
        sx = x1 - 2.2 if side > 0 else x0 + 2.2
        axP.add_patch(Rectangle((sx - 1.6, (y0 + y1) / 2 - 5.2), 3.2, 10.4, fc="#111111", ec="#111111", zorder=3))
        axP.text(sx + (-3.2 if side > 0 else 3.2), (y0 + y1) / 2 + 9, "I²C", fontsize=6, color="#111111", ha="center", zorder=6)
        if i == 3: axP.text(x1 - 2, y1 - 2, "PN532 %d%d" % (i, j), fontsize=7, weight="bold", color=BOARD["PN"], va="top", ha="right", zorder=6)
        else: axP.text(x0 + 2, y1 - 2, "PN532 %d%d" % (i, j), fontsize=7, weight="bold", color=BOARD["PN"], va="top", zorder=6)
for k, nm in (("REF_TCA9548A_A", "TCA_A\n0x70"), ("REF_TCA9548A_B", "TCA_B\n0x71")):
    cx, cy = rect(axP, k, BOARD["TCA"], z=2.2); label(axP, cx, cy, nm, size=7)
cx, cy = rect(axP, "REF_Loetverteiler", BOARD["VT"], z=2.2); label(axP, cx, cy + 1, "Löt-\nverteiler", color=INK, size=6.5)
axP.add_patch(Rectangle((D["link_clip"][0] - 3, D["link_clip"][1] - 2), 6, 4, fc="white", ec=INK, lw=1, zorder=7))

# ---------- Leitungen ----------
for w in W:
    ax = axU if w["teil"] in ("Unterteil",) else axP
    c = F[kind(w)]; lw = 1.0 + 0.45 * w["adern"]
    for p in w["pfade"]:
        path(ax, p, c, lw)
        if w["teil"] == "Schlaufe": path(axU, p, c, lw, ls=(0, (2, 1.5)))
    x, y = mid(w["pfade"]); tag(ax, x, y, w["nr"], c)
    if w["teil"] == "Schlaufe": tag(axU, x, y, w["nr"], c)

# ---------- Legende + Leitungstabelle ----------
axL = fig.add_axes([0.835, 0.30, 0.16, 0.63]); axL.axis("off"); axL.set_xlim(0, 1); axL.set_ylim(0, 1)
axL.text(0, 0.99, "Legende", fontsize=10, weight="bold", va="top")
leg = [(F["VCC"], "Versorgung Reader (VCC + GND)"), (F["DATA_A"], "Daten SDA/SCL -> TCA_A"), (F["DATA_B"], "Daten SDA/SCL -> TCA_B"),
       (F["BUS"], "Bus 4-adrig (VCC, GND, SDA, SCL)"), (F["HX"], "HX711 -> ESP32 (GND, DAT, CLK, VCC)")]
for n, (c, t) in enumerate(leg):
    yy = 0.93 - n * 0.045; axL.plot([0, 0.12], [yy, yy], color=c, lw=3.5, solid_capstyle="round"); axL.text(0.16, yy, t, fontsize=7.5, va="center")
yy = 0.93 - len(leg) * 0.045; axL.plot([0, 0.12], [yy, yy], color=F["BUS"], lw=2.5, ls=(0, (2, 1.5))); axL.text(0.16, yy, "Schlaufe über den Wägespalt", fontsize=7.5, va="center")
yy -= 0.045; axL.add_patch(Rectangle((0.02, yy - 0.012), 0.08, 0.024, fc="#111111")); axL.text(0.16, yy, "I²C-Leiste PN532 (4 Pins, Pins nach unten)", fontsize=7.5, va="center")
yy -= 0.045; axL.text(0, yy, "Linienstärke ~ Aderzahl. Zahl im Kreis = Nr. unten.", fontsize=7, color=MUTED, va="center")
yy -= 0.045; axL.text(0, yy, "Reihen: Reihe 1 = y 0-50 (vorne), Reihe 3 = y 100-150.\nReader-Nr. = Spalte|Reihe.", fontsize=7, color=MUTED, va="top")

axT = fig.add_axes([0.02, 0.015, 0.96, 0.26]); axT.axis("off")
rows = [["Nr", "Ebene", "Leitung / Bündel (Verlauf im Modell)", "Adern", "Länge Modell"]]
for w in W:
    rows.append([str(w["nr"]), w["teil"], umlaut(w["name"]).replace("->", "→"), str(w["adern"]), "%.0f mm" % w["laenge"]])
half = math.ceil((len(rows) - 1) / 2)
for col, part in enumerate((rows[1:half + 1], rows[half + 1:])):
    t = axT.table(cellText=part, colLabels=rows[0], loc="upper left", bbox=[col * 0.5, 0.0, 0.49, 1.0],
                  colWidths=[0.05, 0.11, 0.6, 0.09, 0.15], cellLoc="left")
    t.auto_set_font_size(False); t.set_fontsize(7.2)
    for (r, cidx), cell in t.get_celld().items():
        cell.set_edgecolor(GRID); cell.set_linewidth(0.6)
        if r == 0: cell.set_facecolor("#eeeeee"); cell.set_text_props(weight="bold")
        elif cidx == 0:
            w = W[int(part[r - 1][0]) - 1]; cell.set_text_props(color=F[kind(w)], weight="bold")
fig.text(0.02, 0.278, "Summe Adern x Modelllänge: %.1f m (ohne Zellkabel, ohne Zugabe). Zuschnitt je Kabel mit Zugabe: Seite 2."
         % (sum(w["adern"] * w["laenge"] for w in W) / 1000), fontsize=7.5, color=MUTED)

# ---------- Seite 2: Pin-Tabelle aus der YAML ----------
C, K = Y["connectors"], Y["cables"]
def expand(spec):
    out = []
    for s in spec:
        if isinstance(s, str) and "-" in s: a, b = map(int, s.split("-")); out += list(range(a, b + 1))
        else: out.append(s)
    return out
prow = []
for con in Y["connections"]:
    (ka, pa), = con[0].items(); (kw, ws), = con[1].items(); (kb, pb), = con[2].items()
    for a, wnr, b in zip(pa, expand(ws), pb):
        col = K[kw].get("colors", ["?"] * 8)[wnr - 1]
        L = K[kw].get("length"); prow.append([kw, str(wnr), col, "%s : %s" % (ka, a), "%s : %s" % (kb, b), ("%.0f" % (L * 1000)) if L else "Zelle"])
fig2 = plt.figure(figsize=(11.69, 16.54))  # A3 hoch
fig2.suptitle("Pin-Tabelle (aus verdrahtung_v2.yml) - je Zeile eine Ader", fontsize=13, weight="bold", x=0.04, ha="left", y=0.99)
fig2.text(0.04, 0.973, "Zuschnitt = (Modelllänge + 2 x 3 mm Steigleitung) x 1,3, auf 5 mm aufgerundet. Litze LiYv 0,25 mm² (Annahme). "
          "GPIO-Namen am ESP32 = PLATZHALTER.", fontsize=8, color=MUTED)
ax2 = fig2.add_axes([0.04, 0.015, 0.92, 0.95]); ax2.axis("off")
hdr = ["Kabel", "Ader", "Farbe", "von (Bauteil : Pin)", "nach (Bauteil : Pin)", "Zuschnitt mm"]
t = ax2.table(cellText=prow, colLabels=hdr, loc="upper left", bbox=[0, 0, 1, 1], colWidths=[0.14, 0.06, 0.07, 0.31, 0.31, 0.11], cellLoc="left")
t.auto_set_font_size(False); t.set_fontsize(7.4)
prev = None; shade = False
for (r, cidx), cell in t.get_celld().items():
    cell.set_edgecolor(GRID); cell.set_linewidth(0.5)
    if r == 0: cell.set_facecolor("#eeeeee"); cell.set_text_props(weight="bold"); continue
for r in range(1, len(prow) + 1):
    if prow[r - 1][0] != prev: shade = not shade; prev = prow[r - 1][0]
    for cidx in range(len(hdr)):
        t[r, cidx].set_facecolor("#f4f6fa" if shade else "white")
    cc = COLNAME.get(prow[r - 1][2]);
    if cc: t[r, 2].set_facecolor(cc); t[r, 2].get_text().set_color("white" if prow[r - 1][2] not in ("WH", "YE") else INK)

# ---------- Seite 3: Potentialverteilung (aus der YAML abgeleitet) ----------
import collections
par = {}
def fnd(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
def uni(a, b): par[fnd(a)] = fnd(b)
nadern = collections.Counter(); edges = []   # (ka, pa, kb, pb, kabel)
for con in Y["connections"]:
    (ka, pa), = con[0].items(); (kw, ws), = con[1].items(); (kb, pb), = con[2].items()
    for a, b in zip(pa, pb):
        uni((ka, a), (kb, b)); nadern[(ka, a)] += 1; nadern[(kb, b)] += 1; edges.append((ka, a, kb, b, kw))
for k, c in C.items():
    for lp in c.get("loops", []): uni((k, c["pinlabels"][lp[0] - 1]), (k, c["pinlabels"][lp[1] - 1]))
def net_of(k, p): r = fnd((k, p)); return [x for x in par if fnd(x) == r]
NET = {"VCC": net_of("ESP32", "3V3"), "GND": net_of("ESP32", "GND"), "SDA": net_of("ESP32", "GPIO_SDA"), "SCL": net_of("ESP32", "GPIO_SCL")}

def tree(root, edge_ok):
    adj = collections.defaultdict(list)
    for ka, a, kb, b, kw in edges:
        if edge_ok(ka, a, kb, b):
            for x, y in ((ka, kb), (kb, ka)):
                if (y, kw) not in adj[x]: adj[x].append((y, kw))
    ch = collections.defaultdict(list); seen = {root}; q = [root]
    while q:
        x = q.pop(0)
        for y, kw in adj[x]:
            if y not in seen: seen.add(y); ch[x].append((y, kw)); q.append(y)
    return ch
def draw_tree(ax, root, ch, title, pins):
    pos = {}; leaf = [0]
    def lay(n, d):
        kids = ch.get(n, [])
        if not kids: pos[n] = (d, leaf[0]); leaf[0] += 1; return pos[n][1]
        ys = [lay(k, d + 1) for k, _ in kids]; pos[n] = (d, sum(ys) / len(ys)); return pos[n][1]
    via = {}
    lay(root, 0); nl = max(leaf[0], 1); dmax = max(d for d, _ in pos.values())
    X = lambda d: 0.02 + d * (0.96 / (dmax + 0.75)); Yp = lambda y: 0.92 - y * (0.86 / max(nl - 1, 1))
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_title(title, fontsize=10.5, weight="bold", loc="left")
    for n, kids in ch.items():
        for k, kw in kids:
            (d0, y0), (d1, y1) = pos[n], pos[k]; xm = X(d0) + 0.17
            ax.plot([X(d0) + 0.15, xm, xm, X(d1)], [Yp(y0), Yp(y0), Yp(y1), Yp(y1)], color=MUTED, lw=1.1, zorder=1)
            L = K[kw].get("length"); via[k] = "über %s  %s" % (kw, ("%.0f mm" % (L * 1000)) if L else "")
    for n, (d, y) in pos.items():
        c = BOARD["PN"] if n.startswith("PN532") else BOARD["TCA"] if n.startswith("TCA") else BOARD["VT"] if n == "VERTEILER" else BOARD["HX"] if n.startswith("HX") else BOARD["ESP"]
        tc = INK if n == "VERTEILER" else "white"
        ax.add_patch(FancyBboxPatch((X(d), Yp(y) - 0.03), 0.15, 0.06, boxstyle="round,pad=0.003,rounding_size=0.01", fc=c, ec=c, zorder=3))
        pp = pins(n); warn = n != "VERTEILER" and any(nadern[(n, p)] >= 3 for p in pp)
        ax.text(X(d) + 0.075, Yp(y) + 0.014, n, fontsize=7, color=INK if n == "VERTEILER" else "white", weight="bold", ha="center", va="center", zorder=4)
        ax.text(X(d) + 0.075, Yp(y) - 0.004, ", ".join("%s x%d" % (p, nadern[(n, p)]) for p in pp), fontsize=5.6, color=tc, ha="center", va="center", zorder=4)
        if n in via: ax.text(X(d) + 0.075, Yp(y) - 0.019, via[n], fontsize=5.4, color=tc, ha="center", va="center", zorder=4, style="italic")
        if warn: ax.add_patch(FancyBboxPatch((X(d) - 0.004, Yp(y) - 0.034), 0.158, 0.068, boxstyle="round,pad=0.003,rounding_size=0.012", fc="none", ec="#e67e22", lw=2.2, zorder=5))

vset = set(NET["VCC"]); iset = set(NET["SDA"])
ch_v = tree("ESP32", lambda ka, a, kb, b: (ka, a) in vset)
ch_i = tree("ESP32", lambda ka, a, kb, b: (ka, a) in iset or (ka.startswith("TCA") and a.startswith("SD")))
fig3 = plt.figure(figsize=(16.54, 11.69))
fig3.suptitle("Potentialverteilung (aus verdrahtung_v2.yml abgeleitet)", fontsize=14, weight="bold", x=0.02, ha="left", y=0.985)
fig3.text(0.02, 0.952, "Versorgung: EINE Spannung VCC = 3V3 vom ESP32 (Annahme, NP_WIRES offen). GND läuft in jedem Kabel parallel zu VCC (gleiche Topologie). "
          "Pin-Angabe 'x n' = Anzahl Adern an diesem Pin. Orange umrandet = 3 oder mehr Adern an einem Pin.", fontsize=8, color=MUTED)
def vpins(n): return [p for (k, p) in NET["VCC"] if k == n and nadern[(k, p)] > 0] + [p for (k, p) in NET["GND"] if k == n]
def ipins(n): return [p for (k, p) in NET["SDA"] + NET["SCL"] if k == n] or [p for p in C[n]["pinlabels"] if p in ("SDA", "SCL")]
draw_tree(fig3.add_axes([0.01, 0.40, 0.48, 0.53]), "ESP32", ch_v, "Versorgung VCC + GND (Baum ab ESP32)", vpins)
draw_tree(fig3.add_axes([0.51, 0.40, 0.48, 0.53]), "ESP32", ch_i, "I²C-Bus SDA + SCL (ESP32 → TCA, dann je Reader eigener Kanal)", ipins)

# Loetverteiler-Belegung
axV = fig3.add_axes([0.02, 0.03, 0.42, 0.33]); axV.axis("off"); axV.set_xlim(-2.2, 9.2); axV.set_ylim(-0.8, 6.9)
axV.set_title("Lötverteiler: Belegung (Streifenraster 6 Streifen x 8 Löcher, Kupfer unten)", fontsize=10.5, weight="bold", loc="left")
holes = collections.OrderedDict((p, []) for p in ("VCC", "GND", "SDA", "SCL"))
for ka, a, kb, b, kw in edges:
    if ka == "VERTEILER": holes[a].append("%s→%s" % (kw.replace("W_", ""), kb.replace("PN532_", "PN")))
    if kb == "VERTEILER": holes[b].append("%s←%s" % (kw.replace("W_", ""), ka))
strips = list(holes.items()) + [("Reserve", []), ("Reserve", [])]
scol = dict(VCC=F["VCC"], GND=F["GND"], SDA=F["DATA_A"], SCL="#e3b505", Reserve=GRID)
for r, (nm, used) in enumerate(strips):
    yy = 5.5 - r
    axV.add_patch(Rectangle((-0.45, yy - 0.32), 8.0 - 0.1, 0.64, fc=scol[nm], alpha=0.22, ec=scol[nm], lw=1))
    axV.text(-0.7, yy, "%s (%d/8)" % (nm, len(used)), ha="right", va="center", fontsize=8, weight="bold", color=INK)
    for h in range(8):
        occ = h < len(used)
        axV.add_patch(plt.Circle((h, yy), 0.17, fc=(scol[nm] if occ else "white"), ec=INK, lw=0.7, zorder=3))
        if occ: axV.text(h, yy + 0.27, used[h], fontsize=4.9, ha="center", va="bottom", rotation=0, zorder=4)
axV.text(-2.1, -0.55, "Streifen durchgehend, keine Trennung nötig. Belegung in Reihenfolge der YAML (Loch 1 = Zuleitung).", fontsize=7, color=MUTED)

# Netzliste
axN = fig3.add_axes([0.47, 0.03, 0.51, 0.33]); axN.axis("off")
axN.set_title("Netzliste: Versorgung und Bus", fontsize=10.5, weight="bold", loc="left")
nrows = []
for nm in ("VCC", "GND", "SDA", "SCL"):
    mem = sorted(NET[nm], key=lambda x: (x[0], x[1]))
    nrows.append([nm, str(len([m for m in mem if nadern[m] > 0])), ", ".join("%s:%s(%d)" % (k, p, nadern[(k, p)]) for k, p in mem if nadern[(k, p)] > 0)])
hint = [k + ":" + p for k, p in NET["VCC"] + NET["GND"] if nadern[(k, p)] >= 3 and k != "VERTEILER"]
import textwrap
tn = axN.table(cellText=[[a, b, "\n".join(textwrap.wrap(c, 125))] for a, b, c in nrows], colLabels=["Netz", "Punkte", "Teilnehmer  Bauteil:Pin(Adern)"],
               bbox=[0, 0.32, 1, 0.66], colWidths=[0.06, 0.07, 0.87], cellLoc="left")
tn.auto_set_font_size(False); tn.set_fontsize(6.6)
for (r, c_), cell in tn.get_celld().items():
    cell.set_edgecolor(GRID)
    if r == 0: cell.set_facecolor("#eeeeee"); cell.set_text_props(weight="bold")
axN.text(0, 0.24, "Hinweise", fontsize=8.5, weight="bold")
axN.text(0, 0.20, "• Am ESP32 hängen an %s je 3 Adern (HX711_A, HX711_B, Schlaufe). 3 Adern auf einem Stiftleisten-Pin sind schlecht lötbar:\n"
         "   besser die zweite GND-Leiste des DevKits nutzen oder im Unterteil einen kleinen Sammelpunkt (Lötstützpunkt) vorsehen. → Elektronik entscheiden.\n"
         "• HX711: VDD (Logik) auf der Platine mit VCC brücken.  TCA_B: A0 an VIN (Adresse 0x71).\n"
         "• Reader-Versorgung je Reihe durchgeschleift: 2 Adern je VCC/GND-Pin, nur der letzte Reader (31/32/33) hat 1.\n"
         "• Kanal-SDA/SCL der Reader laufen NICHT über den Verteiler (alle PN532 = 0x24), sondern einzeln vom TCA-Kanal." % " und ".join(hint),
         fontsize=7.2, va="top", color=INK)

with PdfPages(os.path.join(HERE, "lageplan_v2.pdf")) as pdf:
    pdf.savefig(fig); pdf.savefig(fig2); pdf.savefig(fig3)
fig3.savefig(os.path.join(HERE, "potentialverteilung_v2.png"), dpi=120)
fig.savefig(os.path.join(HERE, "lageplan_v2.png"), dpi=130)
fig2.savefig(os.path.join(HERE, "pintabelle_v2.png"), dpi=110)
print("OK", len(W), "Leitungen,", len(prow), "Adern in der Pin-Tabelle")
