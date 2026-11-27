---
name: parameter-und-pruefbericht
description: "Muster für skriptgebaute Modelle: jedes Maß als (Name, Wert, Status, Quelle) mit Status bestaetigt|Norm|Annahme|PLATZHALTER in einer eigenen Parameterdatei, automatischer Prüfbericht mit Zusammenfassung oben (OK/FEHLER, Abweichungen, Hinweise) und Hooks, die das prüfen. Verwenden beim Anlegen oder Ändern von Parametern, beim Ausbau des Prüfberichts oder beim Einrichten der Prüf-Hooks in einem neuen Projekt."
---

# Parameter mit Status und Quelle, automatischer Prüfbericht

## 1. Parameterliste
Eine eigene Datei (z. B. `skripte/params.py`) enthält nur die Liste. Sie besteht nur aus Literalen, damit Hooks sie ohne CAD-Programm per `ast` lesen können:
```python
PARAMS = [
    # Name, Wert, Status, Quelle/Hinweis
    ("WALL", 2.0, "Annahme", "Mindestwand FDM 1,2 + Reserve"),
    ("BOARD_L", 51.8, "bestaetigt", "Hersteller-Maßzeichnung v1.2"),
    ("SCREW_LEN", 12.0, "Norm", "DIN 912 M4x12"),
    ("CONN_W", 20.0, "PLATZHALTER", "Verbinder noch nicht festgelegt"),
]
```
- **Status:** `bestaetigt` = gemessen oder aus Herstellerquelle, mit Fundstelle. `Norm` = aus einer Norm. `Annahme` = begründete Schätzung, im Testdruck oder durch Messung prüfen. `PLATZHALTER` = fehlt, muss geliefert werden.
- **Quelle** nie leer: Datei mit Seite, „Nutzer TT.MM.“ mit Messwert, Normnummer oder die Begründung der Annahme.
- Namen sind eindeutig. Ein neuer Messwert ändert Wert, Status und Quelle zusammen.
- Das Build-Skript lädt die Datei über die Projektwurzel (auch per `exec` ohne `__file__` lauffähig) und baut daraus `P = {name: wert}`. Die Liste geht als Tabelle mit ins CAD-Dokument.

## 2. Prüfbericht
Das Build-Skript schreibt bei jedem Lauf eine Textdatei mit:
1. **Zusammenfassung oben**, eine Zeile: `ZUSAMMENFASSUNG: OK|FEHLER (n Abweichungen; k harte Prüfungen, m Sollwerte geprüft; h Hinweise; p PLATZHALTER)`. Darunter je `FEHLER:`- und `Hinweis:`-Zeile, dann ein Trennstrich.
2. **Details** mit festen Formaten, damit sie maschinell prüfbar sind:
   - Werte mit Sollwert: `... min 0.50 (Soll 0.50)`, `... 2.35 (Soll >= 2,0)`, `... 0.000 mm3 (erwartet 0)`
   - Hinweise mit `<--` am Zeilenende (bekannt, kein Fehler)
   - Ausnahmen ausdrücklich als `AUSNAHME` mit Begründung
   - Letzte Zeile: offene `PLATZHALTER` mit Namen
- **Harte Prüfungen:** Körper gültig, Überschneidung der Druckteile 0, Kollisionen mit Referenzteilen 0, Bewegungs-/Kollisionscheck 0 mm³. Dazu kommen alle Sollwerte, die per Regex aus den Details gelesen werden (Muster in `beilagen/zusammenfassung.py`).
- Der Bericht ist deterministisch (keine Zeitstempel im Text). So zeigt `git diff` des Berichts genau die Modelländerung. Nach einem reinen Umbau des Skripts muss der Bericht unterhalb der Zusammenfassung identisch bleiben.

## 3. Hooks (Beilagen)
| Datei | Ereignis | Wirkung |
|---|---|---|
| `beilagen/pruefe_params.py` | `PostToolUse`, Matcher `Edit\|Write` | Syntax (`ast.parse`) und jede `PARAMS`-Liste: 4-Tupel, Status gültig, Quelle nicht leer, Name eindeutig. Fehler → Exit 2, Meldung auf stderr an Claude. Ordner über `PARAM_HOOK_ORDNER`. |
| `beilagen/pruefbericht_aktuell.py` | `Stop` | Blockiert mit `{"decision": "block", "reason": ...}`, wenn eine Quelle gegenüber Git geändert und neuer als der Bericht ist. `stop_hook_active` verhindert eine Endlosschleife. Dateien über `PRUEF_QUELLEN` und `PRUEF_BERICHT`. |
| `beilagen/zusammenfassung.py` | (im Build-Skript) | Erzeugt die Zusammenfassung aus den Berichtszeilen. |

Beispiel `.claude/settings.json` (Format vorher gegen die aktuelle Claude-Code-Doku prüfen):
```json
{
  "hooks": {
    "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/pruefe_params.py\"", "timeout": 30}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/pruefbericht_aktuell.py\"", "timeout": 15}]}]
  }
}
```
Die Umgebungsvariablen `PARAM_HOOK_ORDNER`, `PRUEF_QUELLEN` und `PRUEF_BERICHT` setzt man im `env`-Block der Settings. Die Prüfskripte vorher selbst mit Fehlerfällen testen: falscher Status, leere Quelle, doppelter Name, Syntaxfehler, `stop_hook_active`.
