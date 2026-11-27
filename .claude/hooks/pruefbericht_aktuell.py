#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stop-Hook: Abschluss blockieren, wenn das Modell geaendert, aber nicht neu gebaut wurde.

Blockiert, wenn build_prototyp_v2.py oder params.py
  (a) gegenueber dem letzten Commit geaendert ist (git status) UND
  (b) neuer ist als gehaeuse/pruefberichte/pruefbericht_deckel_v2.txt.
(a) verhindert Fehlalarme nach clone/checkout, wo nur die Dateizeiten durcheinander sind.
Schutz gegen Endlosschleife: Ist stop_hook_active gesetzt (Claude laeuft schon wegen dieses Hooks weiter),
wird nicht noch einmal blockiert.
"""
import json, os, subprocess, sys

QUELLEN = ["gehaeuse/skripte/build_prototyp_v2.py", "gehaeuse/skripte/params.py"]
BERICHT = "gehaeuse/pruefberichte/pruefbericht_deckel_v2.txt"


def main():
    try:
        ein = json.load(sys.stdin)
    except ValueError:
        ein = {}
    if ein.get("stop_hook_active"):
        return 0
    wurzel = os.environ.get("CLAUDE_PROJECT_DIR") or ein.get("cwd") or os.getcwd()
    try:
        geaendert = subprocess.run(["git", "status", "--porcelain", "--"] + QUELLEN, cwd=wurzel,
                                   capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 0
    if not geaendert:
        return 0
    b = os.path.join(wurzel, BERICHT)
    t_bericht = os.path.getmtime(b) if os.path.exists(b) else 0
    neuer = [q for q in QUELLEN if os.path.exists(os.path.join(wurzel, q)) and os.path.getmtime(os.path.join(wurzel, q)) > t_bericht]
    if neuer:
        print(json.dumps({"decision": "block",
                          "reason": "Pruefbericht veraltet, erst /bauen (geaendert: %s)" % ", ".join(os.path.basename(q) for q in neuer)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
