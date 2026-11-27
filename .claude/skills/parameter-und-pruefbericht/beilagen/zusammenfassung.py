# -*- coding: utf-8 -*-
"""Zusammenfassung oben im Pruefbericht. Ins Build-Skript kopieren und vor dem Schreiben des Berichts aufrufen.

    L = [...]                     # Berichtszeilen (Details)
    harte = [("Koerper gueltig", ok1), ("Kollisionen 0", ok2), ...]
    platzhalter = [name for name, w, st, q in PARAMS if st == "PLATZHALTER"]
    L[0:0] = zusammenfassung(L, harte, platzhalter)
"""
import re

_RX_SOLL = re.compile(r"(-?\d+\.\d+)\s*(?:mm3?\s*)?(?:radial\s*)?\((?:Soll|erwartet)\s*(>=|<=)?\s*(-?\d+(?:[.,]\d+)?)")
_RX_DEHN = re.compile(r"Dehnung (-?\d+\.\d+) % \(<= (\d+(?:[.,]\d+)?) %\)")


def zusammenfassung(zeilen, harte, platzhalter, tol=0.005):
    fehler = [n for n, ok in harte if not ok]
    n_soll = 0
    for z in zeilen:
        for m in _RX_SOLL.finditer(z):
            n_soll += 1
            v, op, s = float(m.group(1)), m.group(2), float(m.group(3).replace(",", "."))
            ok = v >= s - tol if op == ">=" else (v <= s + tol if op == "<=" else abs(v - s) <= tol)
            if not ok:
                fehler.append("Sollwert: " + z.strip()[:110])
        for m in _RX_DEHN.finditer(z):
            n_soll += 1
            if float(m.group(1)) > float(m.group(2).replace(",", ".")) + tol:
                fehler.append("Dehnung: " + z.strip()[:110])
    hinweise = [z.strip() for z in zeilen if "<--" in z]
    kopf = ["ZUSAMMENFASSUNG: %s  (%d Abweichungen; %d harte Pruefungen, %d Sollwerte geprueft; %d Hinweise; %d PLATZHALTER)" % (
        "OK" if not fehler else "FEHLER", len(fehler), len(harte), n_soll, len(hinweise), len(platzhalter))]
    return kopf + ["  FEHLER: " + f for f in fehler] + ["  Hinweis: " + h for h in hinweise] + ["=" * 100]
