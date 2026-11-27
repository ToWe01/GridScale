#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostToolUse-Hook (Edit|Write): Syntax- und Parameterpruefung fuer Python-Skripte in gehaeuse/skripte/.

- Syntax: ast.parse (ohne Ausfuehren, ohne FreeCAD, in Millisekunden).
- Parameter: jede Liste PARAMS = [...] im Skript; jeder Eintrag (Name, Wert, Status, Quelle) mit
  Status aus bestaetigt|Norm|Annahme|PLATZHALTER, nicht leerer Quelle und eindeutigem Namen.
Fehler -> Exit 2, Meldung auf stderr (Claude sieht sie). Sonst Exit 0 ohne Ausgabe.
Auch direkt aufrufbar: pruefe_skript.py <datei.py> [...]  (zum Testen, ohne stdin).
"""
import ast, json, os, sys

STATUS = {"bestaetigt", "Norm", "Annahme", "PLATZHALTER"}
ORDNER = os.path.join("gehaeuse", "skripte") + os.sep


def pruefe(pfad):
    fehler = []
    try:
        src = open(pfad, encoding="utf-8").read()
    except OSError as e:
        return ["%s: nicht lesbar (%s)" % (pfad, e)]
    try:
        baum = ast.parse(src, filename=pfad)
    except SyntaxError as e:
        return ["%s:%s: Syntaxfehler: %s" % (pfad, e.lineno, e.msg)]
    namen = {}
    for knoten in ast.walk(baum):
        if not (isinstance(knoten, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PARAMS" for t in knoten.targets)):
            continue
        if not isinstance(knoten.value, (ast.List, ast.Tuple)):
            continue   # z. B. PARAMS = _ns["PARAMS"] im Build-Skript: geprueft wird die Quelle params.py
        for e in knoten.value.elts:
            z = e.lineno
            if not isinstance(e, ast.Tuple) or len(e.elts) != 4:
                fehler.append("%s:%d: PARAMS-Eintrag ist kein 4-Tupel (Name, Wert, Status, Quelle)" % (pfad, z))
                continue
            n, _, st, q = e.elts
            name = n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None
            if name is None:
                fehler.append("%s:%d: Name ist kein Text" % (pfad, z))
            elif name in namen:
                fehler.append("%s:%d: Name %s doppelt (zuerst Zeile %d)" % (pfad, z, name, namen[name]))
            else:
                namen[name] = z
            if not (isinstance(st, ast.Constant) and st.value in STATUS):
                fehler.append("%s:%d: %s: Status %r nicht in %s" % (pfad, z, name, getattr(st, "value", "?"), "|".join(sorted(STATUS))))
            if not (isinstance(q, ast.Constant) and isinstance(q.value, str) and q.value.strip()):
                fehler.append("%s:%d: %s: Quelle fehlt oder leer" % (pfad, z, name))
    return fehler


def main():
    if len(sys.argv) > 1:
        dateien = sys.argv[1:]
    else:
        try:
            ein = json.load(sys.stdin)
        except ValueError:
            return 0
        pfad = (ein.get("tool_input") or {}).get("file_path") or ""
        if not pfad.endswith(".py") or ORDNER not in pfad:
            return 0
        dateien = [pfad]
    fehler = [f for d in dateien for f in pruefe(d)]
    if fehler:
        print("Pruefung gehaeuse/skripte fehlgeschlagen:\n" + "\n".join(fehler), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
