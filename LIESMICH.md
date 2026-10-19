# Walls — Mauerwerk aus dem Grundriss für IngeTrazo

Erzeugt aus einem importierten Grundriss (PDF über **Plan Import**, DXF/DWG) das **Mauerwerk** als Volumenkörper: Wände auf Geschosshöhe, Fenster mit Brüstung und Sturz, Türen mit Sturz. Die Wände werden **automatisch vorausgewählt** und lassen sich per Klick korrigieren.

[English → README.md](README.md)

![Mauerwerk](screenshot.webp)

## Installation
1. In IngeTrazo: **Extensions ▸ Open plugins folder** (Windows: `%APPDATA%\ingetrazo\plugins\`, Linux: `~/.local/share/ingetrazo/plugins/`).
2. `walls_tool.py` in diesen Ordner kopieren.
3. IngeTrazo neu starten → **Extensions ▸ Mauerwerk ▸ Mauerwerk aus Plan…** (auch im Rechtsklick-Menü und als Icon in der eigenen Werkzeugleiste).

Benötigt IngeTrazo ≥ 0.5.6 (Extension-API 2) · getestet mit IngeTrazo 0.5.8.

## Bedienung
Den Grundriss auswählen (die Plan-Gruppe von Plan Import oder lose Kanten) und **Mauerwerk aus Plan…** starten. Die Vorauswahl erscheint farbig im Modell:

- **orange** = Wand · **blau** = Fenster · **grün** = Tür · gestrichelt = abgewählt
- **Klick auf eine Wand** schaltet sie an/aus.
- **Klick auf eine Öffnung** schaltet Fenster → Tür → keine Öffnung.
- **Umschalt-Klick** auf eine andere Fläche der Zeichnung (z. B. eine dicke Stütze) nimmt sie als Wand dazu.
- **Live Preview** (wie in allen PESI3D-Plugins): das Mauerwerk steht sofort im Modell und folgt jeder Änderung — so sieht man, ob alle Wände erwischt sind. **Reset** = Standardwerte und Vorauswahl.
- **Follow selection**: einen anderen Grundriss auswählen, die Wände folgen; **↻ Read selection** liest die Auswahl sofort.
- **OK** übernimmt alles als **eine Gruppe** (BIM: `IfcWall`) in einem Undo-Schritt; **Cancel** nimmt die Vorschau zurück.

### Wände nach Linienart (mit Plan Import ≥ 1.2)
CAD-Programme zeichnen geschnittene Wände auf ihre eigene Art — meist gefüllt, sonst mit dem dicksten Stift. Ein mit **Plan Import 1.2** importiertes Blatt merkt sich, wie jede Linie gezeichnet war. Der Dialog zeigt dann die Liste **Linienarten aus dem PDF** (Farbfeld, Füllung oder Strichstärke, Fläche oder Länge):

- Die wahrscheinliche Wand-Linienart ist **vorausgewählt** (eine Füllung aus überwiegend schmalen Flächen, sonst der dickste häufige Stift).
- **Wände anhaken**: Füllungen werden direkt Wand, Linien gehen durch die Linien-Erkennung (unten).
- **Beispielwand anklicken…**: dann eine Wandlinie oder Wandfüllung im Modell anklicken — ihre Linienart wird an- oder ausgeschaltet.
- Möbel, Sanitärobjekte, Maßketten und Schraffuren haben andere Linienarten und bleiben so von selbst draußen.
- **Taschen**: Flächen ohne Füllung, die (fast) ringsum Wand sind — Fugen zwischen zwei Füllungen, Dreiecke an schrägen Wandecken, Kreuzungen, Stützen mit X — werden bis 0,3 m² automatisch geschlossen, wenn sie ringsum Wand sind oder ihre freien Kanten genau die Wandkanten verlängern (Außenecken). Haarfeine Fugen zwischen zwei Füllungen (unter 1 cm) schließt der Volumenkörper von selbst. Größere (Installationsschächte, Hohlräume zwischen Doppelwänden) erscheinen gestrichelt: ein Klick nimmt sie dazu.

Ältere Importe und DXF/DWG haben keine Linienarten: dann gilt die Erkennung nach Geometrie.

### Was erkannt wird (nach Geometrie)
- **Gefüllte oder schraffierte Wände**: jede dünne geschlossene Fläche der Zeichnung zwischen *Wandstärke von … bis*. Schraffurlinien teilen die Wand nicht.
- **Wände aus zwei Linien** (ohne Füllung, auch mit Lücken): parallele Linienpaare im Wandabstand, ohne Linie dazwischen.
- **Fenster**: ein Fenstersymbol in einer Wandlücke (dünnere Streifen, Glaslinie) oder eine Glaslinie mitten in einer gefüllten Wand.
- **Türen**: eine leere Lücke zwischen zwei Enden derselben Wand (bis *Max. Öffnungsbreite*).
- **Nicht** als Wand: Treppen (Reihen gleicher Stufen), Maßketten (Hilfslinien mit Maßstrichen), Schnitt- und Achslinien, die quer durch den Plan laufen.

### Kleinteile
**Kleinteile abwählen unter … cm²** (Vorgabe 200 cm²): kleinere Stücke, die in einer Fenster- oder Türöffnung liegen (Rahmenprofile, wie die Wand gefüllt) oder lose herumliegen, sind zu Beginn abgewählt. Kleine Stücke, die an einer Wand hängen, bleiben — CAD zerlegt Wände oft in viele kleine Füllungen. 0 = alle behalten.

Fensterbänder und Glasfassaden breiter als *Max. Öffnungsbreite* (Vorgabe 4 m) bleiben offene Lücken — bei Bedarf den Wert erhöhen.

### Höhen
- **Wandhöhe**: kommt aus dem **Levels**-Panel (Abstand zur nächsten Ebene), sonst der zuletzt verwendete Wert.
- **Brüstung**: Fensterunterkante über Rohfußboden.
- **Sturz (Unterkante)**: Oberkante von Fenstern und Türen.

Tipp: Mit Plan Import nur den Grundriss zuschneiden (Crop), dann stören Plankopf und Rahmen nicht.

## Änderungen
- **1.2** — Vorschau wie in allen PESI3D-Plugins: Zeile **Quelle** mit *Follow selection* (einen anderen Grundriss wählen, die Wände folgen) und *↻ Read selection*; Knöpfe *● Live Preview ON · Reset · OK · Cancel*. Behoben: beim Neubau der Vorschau kam eine ältere Auswahl zurück. Screenshot vom Musterhaus-Beispiel.
- **1.1** — **Live-Vorschau** mit Banner, Zurücksetzen. Ungefüllte **Taschen** in den Wänden (Ecken, Fugen, Kreuzungen) werden geschlossen, Schächte zum Dazuklicken angeboten. **Kleinteile abwählen unter … cm²**: Rahmenprofile in Öffnungen und lose Krümel sind zu Beginn abgewählt. Behoben: zwei gleich große Füllungs-Hälften (z. B. die Dreiecke einer Gehrungsecke) galten als doppelt — eine fehlte. Wände nach **Linienart** (mit Plan Import 1.2): Liste der Linienarten, Vorauswahl der Wandfüllung, **Beispielwand anklicken**. Öffnungen: Fenster mit unterteilten Rahmen und Fensteranschlag werden als ein Fenster erkannt, Schächte zwischen zwei Wänden nicht mehr als Tür; wie die Wand gefüllte Fensterrahmen-Profile zerteilen keine Öffnung mehr. Mehrschichtige Wände gelten nicht mehr als Treppe. Fehler erscheinen als Meldung (und in `%LOCALAPPDATA%\IngeTrazo\walls_tool.log`). Große Pläne deutlich schneller.
- **1.0** — erste Veröffentlichung.

## Lizenz
GPL-3.0-or-later · © 2026 Pesi (pesi3d.de) · [Impressum](https://pesi3d.de)
