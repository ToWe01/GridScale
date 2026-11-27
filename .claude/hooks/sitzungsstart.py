#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SessionStart-Hook: kurzer Lagebericht als Kontext (stdout bei Exit 0 geht an Claude).
Git-Status, Anzahl offener PLATZHALTER in params.py, Datum und Zusammenfassung des letzten Pruefberichts."""
import ast, datetime, os, subprocess, sys

PARAMS = "gehaeuse/skripte/params.py"
BERICHT = "gehaeuse/pruefberichte/pruefbericht_deckel_v2.txt"


def main():
    w = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    z = ["[Sitzungsstart GridScale]"]
    try:
        st = subprocess.run(["git", "status", "--short", "--branch"], cwd=w, capture_output=True, text=True, timeout=10).stdout.splitlines()
        z.append("Git: %s, %d geaenderte/neue Dateien" % (st[0].lstrip("# ") if st else "?", max(len(st) - 1, 0)))
        z += ["  " + s for s in st[1:11]] + (["  ..."] if len(st) > 11 else [])
    except (OSError, subprocess.SubprocessError):
        z.append("Git: nicht verfuegbar")
    try:
        baum = ast.parse(open(os.path.join(w, PARAMS), encoding="utf-8").read())
        ph = [e.elts[0].value for k in ast.walk(baum) if isinstance(k, ast.Assign) and any(getattr(t, "id", "") == "PARAMS" for t in k.targets)
              for e in k.value.elts if isinstance(e, ast.Tuple) and len(e.elts) == 4 and getattr(e.elts[2], "value", "") == "PLATZHALTER"]
        z.append("Offene PLATZHALTER: %d%s" % (len(ph), (" (" + ", ".join(ph) + ")") if ph else ""))
    except (OSError, SyntaxError) as e:
        z.append("params.py nicht lesbar: %s" % e)
    b = os.path.join(w, BERICHT)
    if os.path.exists(b):
        t = datetime.datetime.fromtimestamp(os.path.getmtime(b)).strftime("%Y-%m-%d %H:%M")
        erste = open(b, encoding="utf-8").readline().strip()
        z.append("Letzter Pruefbericht: %s, %s" % (t, erste))
    else:
        z.append("Kein Pruefbericht vorhanden")
    print("\n".join(z))
    return 0


if __name__ == "__main__":
    sys.exit(main())
