---
name: cad-konstruktion-freecad
description: "Vorgehen für parametrische Gehäusekonstruktion in FreeCAD per Python-Skript: Maße zuerst klären, mit markierten Platzhaltern bauen, FreeCAD über MCP-Bridge oder headless ausführen, Konstruktionsregeln für Elektronikgehäuse im FDM-Druck (PLA) und für Wägezellen-Mechanik, Prüfliste vor dem Abschluss. Verwenden bei jeder Änderung an Geometrie, Maßen oder Bauteillage eines skriptgebauten FreeCAD-Modells."
---

# CAD-Konstruktion mit FreeCAD-Skripten

Die projektspezifischen Angaben (Pfade, Maße, Bauteile, Aufrufe) stehen in der `CLAUDE.md` des Projekts, in der Parameterdatei und im Stand-Dokument. Dieser Skill beschreibt nur das Vorgehen.

## 1. Vorgehen
1. **Stand lesen:** zuerst das Stand-Dokument und die Parameterdatei lesen. Das Build-Skript nur gezielt per `grep` nach Parametername oder Bauteil lesen, nicht komplett.
2. **Erst fragen, dann bauen:** Fehlt ein kritisches Maß (Bauteilmaß, Lochbild, Steckerlage), kurz beim Nutzer nachfragen. Kommt das Maß aus einer Datei (Datenblatt, Herstellerzeichnung, Eagle/KiCad-Board, DXF), dort nachsehen und die Quelle angeben. Danach darf mit einem Wert weitergebaut werden, der als `Annahme` oder `PLATZHALTER` markiert ist.
3. **Maße nur in der Parameterliste ändern** (Name, Wert, Status, Quelle, siehe Skill `parameter-und-pruefbericht`). Nie im FreeCAD-Dokument von Hand ändern, das Skript baut alles neu.
4. **Bauen und den Prüfbericht lesen**, nicht nur „lief ohne Fehler“ melden. Mit dem letzten Stand vergleichen (`git diff` des Prüfberichts).
5. **Entscheidung festhalten:** im Entscheidungslog Datum, Entscheidung, Begründung und verworfene Varianten eintragen. Das Stand-Dokument überschreiben, nicht ergänzen.
6. **Committen**, wenn der Schritt fertig ist. Keine manuellen Kopien `skript_vor_xyz.py`.

## 2. FreeCAD ausführen
- **MCP Bridge for FreeCAD** (`execute_python`): Das Skript per `exec(compile(open(pfad, encoding="utf-8").read(), name, "exec"))` in der laufenden GUI ausführen. In der GUI bleiben die Farben erhalten. Ohne die Einstellung „Unrestricted“ fragt FreeCAD vor jedem Lauf nach, der Job-Token läuft ab.
- **Headless:** `freecadcmd -c "import FreeCAD as App; exec(compile(open('<skript>', encoding='utf-8').read(), '<skript>', 'exec'))"` aus der Projektwurzel. Die FCStd hat dann keine Farben. Lange Läufe (Minuten) im Hintergrund oder mit großem Timeout starten.
- **Skripte für `exec` schreiben:** Es gibt kein `__file__` und kein Skriptverzeichnis in `sys.path`. Die Projektwurzel aus einer Umgebungsvariablen nehmen, sonst aus dem aktuellen Verzeichnis, sonst aus einem festen Pfad. Hilfsdateien (z. B. die Parameterliste) über diese Wurzel laden: `exec(compile(open(os.path.join(WURZEL, ...)).read(), ...), ns)`.
- Das Skript löscht seine Objekte, baut alles neu, speichert die FCStd und schreibt den Prüfbericht. `App.GuiUp` abfragen, bevor GUI-Befehle laufen.

## 3. Konstruktionsregeln Elektronikgehäuse (FDM, PLA)
- **Wand** mindestens 1,2 mm (3 Perimeter bei 0,4-mm-Düse). Ausnahmen im Prüfbericht als AUSNAHME mit Begründung nennen.
- **Löcher** drucken ca. 0,1–0,2 mm kleiner. M3/M4 als Schneidschrauben direkt ins PLA. Unter Schraubenköpfen auf PLA eine Scheibe gegen Kriechen vorsehen.
- **Passungen** 0,3–0,5 mm für lose Teile, Presssitz über Quetschrippen (Nennmaß 0, der Schwund gibt die Pressung).
- **Überhänge vermeiden:** Druckorientierung früh festlegen. Brücken kurz halten. An Senkungen, die zum Bett offen sind, Opferschichten vorsehen (Schicht 1 Schlitz, Schicht 2 Quadrat).
- **Rasthaken:** Arm lang genug für eine Dehnung ≤ 2 %. Der Arm muss in Schichtrichtung biegen, nicht quer zu den Schichten.
- **Platinen:** Header-Pins bleiben, wenn später an die Pins gelötet wird. Taschen und Rahmen lassen die Pins frei, mit Luft zum Löten. Halterung bevorzugt gedruckt (Rasthaken, Zentrierzapfen), wenig Normteile.
- **Steckverbinder:** Stecker samt Umspritzung und Biegeradius des Kabels modellieren, nicht nur die Buchse.
- **Staubschutz:** Fugen so legen, dass sie nach unten zeigen. Überdeckung mit kleinem Spalt.

## 4. Wägezellen-Mechanik (allgemein)
- **Kein Kraftnebenschluss:** Die gewogene Platte berührt nur die Freienden der Zellen. Rundherum Luft, auch zu Kleber/Silikon und Kabelaustritt der Zelle.
- **Kabel über den Wägespalt** als lockere Schlaufe, so wenige Adern wie möglich. Die Schlaufe berührt nur ihre beiden Befestigungspunkte.
- **Überlast- und Kippanschläge** mit definiertem Spalt (kleiner als die zulässige Zellendurchbiegung). Zapfen mit Radialspiel, damit nichts reibt.
- **Bewegungscheck:** Platte bis zum Anschlag kippen, absenken und verschieben. In keinem Fall darf sie das feste Teil berühren (Überschneidung 0 mm³).
- Steifigkeit der Platte bei Ecklast prüfen (FEM oder Abschätzung). Sonst überbrückt die Durchbiegung den Anschlagspalt.

## 5. Prüfliste vor dem Abschluss
- [ ] Alle Körper gültig, je Druckteil ein Körper
- [ ] 0 Kollisionen mit Referenzteilen, Bewegungscheck 0 mm³
- [ ] Spalte gleich den Sollwerten (Zusammenfassung im Prüfbericht OK)
- [ ] Mindestwand eingehalten oder als Ausnahme begründet
- [ ] Pins frei, Lötzugang vorhanden
- [ ] Druckorientierung ohne kritische Überhänge
- [ ] Neue Maße mit Status und Quelle, offene Platzhalter benannt
- [ ] Entscheidung geloggt, Stand-Dokument aktuell, Commit
