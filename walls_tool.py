# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Peter Müller (PESI3D) — https://pesi3d.de
"""Walls — masonry from an imported floor plan.

Select a floor plan (the group Plan Import made from a PDF, or loose edges
of a DXF/DWG) and run Extensions ▸ Walls ▸ Walls from Plan…. The plugin
looks for the walls in the linework and preselects them:

- walls drawn as closed outlines (filled or hatched walls arrive as their
  outlines) — every thin face of the drawing between t min and t max;
- walls drawn as two parallel lines only — every pair of parallel lines
  at a wall's distance, with nothing in between;
- openings: a gap between two pieces of the same wall is a door; a gap
  holding a window symbol (thinner pieces or a glass line) is a window.

Stairs (rungs of thin steps) and dimension chains (lines crossing at the
corners) are left out. The preselection shows in the model: walls orange,
windows blue, doors green. Click a piece to switch it on or off, click an
opening to switch window → door → none. «Build» extrudes the walls to the
wall height as ONE group (tagged IfcWall), windows with parapet and
lintel, doors with lintel — one undo step.
"""
from __future__ import annotations

import math

KEY = "walls_tool"
VERSION = "1.2"

_TEXTS = {
    "de": {
        "Walls": "Mauerwerk",
        "Walls from Plan…": "Mauerwerk aus Plan…",
        "Build walls from the selected floor plan (preselected, click to correct).":
            "Erzeugt das Mauerwerk aus dem gewählten Grundriss (vorausgewählt, per Klick korrigierbar).",
        "Select the floor plan first (the plan group or its edges).":
            "Zuerst den Grundriss auswählen (die Plan-Gruppe oder ihre Kanten).",
        "The plan must lie flat (a floor plan, not an elevation).":
            "Der Plan muss flach liegen (Grundriss, keine Ansicht).",
        "Shapely is missing — this IngeTrazo cannot run the wall detection.":
            "Shapely fehlt — diese IngeTrazo-Version kann die Wanderkennung nicht ausführen.",
        "Detection": "Erkennung",
        "Wall thickness": "Wandstärke",
        "from": "von",
        "to": "bis",
        "Walls drawn as two lines": "Wände aus zwei Linien",
        "Openings": "Öffnungen",
        "Detect windows and doors": "Fenster und Türen erkennen",
        "Max. opening width": "Max. Öffnungsbreite",
        "Heights": "Höhen",
        "Wall height": "Wandhöhe",
        "Window sill": "Brüstung",
        "Lintel (underside)": "Sturz (Unterkante)",
        "Preview": "Vorschau",
        "Build": "Erzeugen",
        "Cancel": "Abbrechen",
        "Detecting…": "Erkenne…",
        "{w} wall piece(s), {m} m · {f} window(s) · {d} door(s)":
            "{w} Wandstück(e), {m} m · {f} Fenster · {d} Tür(en)",
        "Click a wall to switch it on/off, an opening to switch window → door → none. Shift-click adds any other face.":
            "Wand anklicken = an/aus, Öffnung anklicken = Fenster → Tür → keine. Umschalt-Klick nimmt jede andere Fläche dazu.",
        "Walls: click to correct the preselection":
            "Mauerwerk: zum Korrigieren der Vorauswahl klicken",
        "Built: {w} wall piece(s), {f} window(s), {d} door(s)":
            "Erzeugt: {w} Wandstück(e), {f} Fenster, {d} Tür(en)",
        "Nothing selected to build.": "Nichts zum Erzeugen ausgewählt.",
        "Masonry": "Mauerwerk",
        "All on": "Alle an",
        "All off": "Alle aus",
        "Fill": "Füllung",
        "Hairline": "Haarlinie",
        "Line {w} mm": "Linie {w} mm",
        "Line styles from the PDF — tick the walls":
            "Linienarten aus dem PDF — Wände anhaken",
        "{a} m²": "{a} m²",
        "{m} m": "{m} m",
        "Click an example wall…": "Beispielwand anklicken…",
        "Click a wall line or fill in the model: its line style is switched on (or off).":
            "Eine Wandlinie oder Wandfüllung im Modell anklicken: ihre Linienart wird an- (oder aus-)geschaltet.",
        "Tip: import the PDF again with Plan Import 1.2 — then the walls are picked by their line style.":
            "Tipp: das PDF mit Plan Import 1.2 neu importieren — dann werden die Wände nach Linienart gewählt.",
        "Wall style on: {s}": "Wand-Linienart an: {s}",
        "Wall style off: {s}": "Wand-Linienart aus: {s}",
        "Preview": "Vorschau",
        "Reset": "Zurücksetzen",
        "Source": "Quelle",
        "Plan": "Plan",
        "{name} — {n} lines, {s} line styles": "{name} — {n} Linien, {s} Linienarten",
        "{n} edges (no line styles)": "{n} Kanten (ohne Linienarten)",
        "While the dialog is open, a changed selection is read again by itself: select another floor plan and the walls follow.":
            "Solange der Dialog offen ist, wird eine geänderte Auswahl von selbst neu gelesen: einen anderen Grundriss wählen, die Wände folgen.",
        "Take the current selection as the source now.": "Die aktuelle Auswahl jetzt als Quelle nehmen.",
        "Walls: no floor plan in the selection — the source stays as it is.":
            "Mauerwerk: kein Grundriss in der Auswahl — die Quelle bleibt.",
        "Switch off pieces under": "Kleinteile abwählen unter",
        "Pieces smaller than this start switched off (window frame profiles, crumbs of the fill). 0 = keep all.":
            "Stücke kleiner als dies sind zu Beginn abgewählt (Fensterrahmen-Profile, Krümel der Füllung). 0 = alle behalten.",
        "Back to the default settings and the preselection.":
            "Zurück zu den Standardwerten und zur Vorauswahl.",
        "● Live Preview ON": "● Live-Vorschau AN",
        "The preview follows every change by itself — click to switch it off.":
            "Die Vorschau folgt jeder Änderung von selbst — Klick schaltet sie aus.",
        "Show the walls in the model; they then update by themselves on every change.":
            "Zeigt die Wände im Modell; sie folgen dann jeder Änderung von selbst.",
        "⟳ Updating the preview…": "⟳ Vorschau wird aktualisiert…",
        "Preview failed: {e}": "Vorschau fehlgeschlagen: {e}",
        "● <b>LIVE PREVIEW</b> — nothing selected to build":
            "● <b>LIVE-VORSCHAU</b> — nichts zum Erzeugen ausgewählt",
        "● <b>LIVE PREVIEW</b> — {w} wall piece(s), {f} window(s), {d} door(s) · height {h} m · changes apply instantly":
            "● <b>LIVE-VORSCHAU</b> — {w} Wandstück(e), {f} Fenster, {d} Tür(en) · Höhe {h} m · Änderungen wirken sofort",
    },
    "es": {
        "Walls": "Muros",
        "Walls from Plan…": "Muros desde plano…",
        "Build walls from the selected floor plan (preselected, click to correct).":
            "Crea los muros desde la planta seleccionada (preseleccionados, corregibles con clic).",
        "Select the floor plan first (the plan group or its edges).":
            "Primero seleccione la planta (el grupo del plano o sus aristas).",
        "The plan must lie flat (a floor plan, not an elevation).":
            "El plano debe estar horizontal (planta, no alzado).",
        "Shapely is missing — this IngeTrazo cannot run the wall detection.":
            "Falta Shapely: esta versión de IngeTrazo no puede detectar muros.",
        "Detection": "Detección",
        "Wall thickness": "Espesor de muro",
        "from": "de",
        "to": "a",
        "Walls drawn as two lines": "Muros dibujados con dos líneas",
        "Openings": "Huecos",
        "Detect windows and doors": "Detectar ventanas y puertas",
        "Max. opening width": "Ancho máx. de hueco",
        "Heights": "Alturas",
        "Wall height": "Altura del muro",
        "Window sill": "Antepecho",
        "Lintel (underside)": "Dintel (cara inferior)",
        "Preview": "Vista previa",
        "Build": "Crear",
        "Cancel": "Cancelar",
        "Detecting…": "Detectando…",
        "{w} wall piece(s), {m} m · {f} window(s) · {d} door(s)":
            "{w} tramo(s) de muro, {m} m · {f} ventana(s) · {d} puerta(s)",
        "Click a wall to switch it on/off, an opening to switch window → door → none. Shift-click adds any other face.":
            "Clic en un muro = activar/desactivar, en un hueco = ventana → puerta → ninguno. Mayús+clic añade cualquier otra cara.",
        "Walls: click to correct the preselection":
            "Muros: haga clic para corregir la preselección",
        "Built: {w} wall piece(s), {f} window(s), {d} door(s)":
            "Creado: {w} tramo(s), {f} ventana(s), {d} puerta(s)",
        "Nothing selected to build.": "No hay nada seleccionado para crear.",
        "Masonry": "Muros",
        "All on": "Todo activado",
        "All off": "Todo desactivado",
        "Fill": "Relleno",
        "Hairline": "Línea fina",
        "Line {w} mm": "Línea {w} mm",
        "Line styles from the PDF — tick the walls":
            "Estilos de línea del PDF — marque los muros",
        "Click an example wall…": "Clic en un muro de ejemplo…",
        "Click a wall line or fill in the model: its line style is switched on (or off).":
            "Haga clic en una línea o relleno de muro: su estilo se activa (o desactiva).",
        "Tip: import the PDF again with Plan Import 1.2 — then the walls are picked by their line style.":
            "Consejo: vuelva a importar el PDF con Plan Import 1.2 — los muros se eligen por estilo de línea.",
        "Wall style on: {s}": "Estilo de muro activado: {s}",
        "Wall style off: {s}": "Estilo de muro desactivado: {s}",
        "Preview": "Vista previa",
        "Reset": "Restablecer",
        "Source": "Origen",
        "{name} — {n} lines, {s} line styles": "{name} — {n} líneas, {s} estilos",
        "{n} edges (no line styles)": "{n} aristas (sin estilos de línea)",
        "While the dialog is open, a changed selection is read again by itself: select another floor plan and the walls follow.":
            "Con el diálogo abierto, una selección nueva se lee sola: elija otra planta y los muros la siguen.",
        "Take the current selection as the source now.": "Tomar ahora la selección actual como origen.",
        "Walls: no floor plan in the selection — the source stays as it is.":
            "Muros: no hay planta en la selección — el origen se mantiene.",
        "Switch off pieces under": "Desactivar piezas menores de",
        "Pieces smaller than this start switched off (window frame profiles, crumbs of the fill). 0 = keep all.":
            "Las piezas menores empiezan desactivadas (perfiles de ventana, restos del relleno). 0 = conservar todas.",
        "Back to the default settings and the preselection.":
            "Volver a los valores por defecto y a la preselección.",
        "● Live Preview ON": "● Vista previa ACTIVA",
        "The preview follows every change by itself — click to switch it off.":
            "La vista previa sigue cada cambio — clic para desactivarla.",
        "Show the walls in the model; they then update by themselves on every change.":
            "Muestra los muros en el modelo; se actualizan con cada cambio.",
        "⟳ Updating the preview…": "⟳ Actualizando la vista previa…",
        "Preview failed: {e}": "Falló la vista previa: {e}",
        "● <b>LIVE PREVIEW</b> — nothing selected to build":
            "● <b>VISTA PREVIA</b> — nada seleccionado para crear",
        "● <b>LIVE PREVIEW</b> — {w} wall piece(s), {f} window(s), {d} door(s) · height {h} m · changes apply instantly":
            "● <b>VISTA PREVIA</b> — {w} tramo(s), {f} ventana(s), {d} puerta(s) · altura {h} m · los cambios se aplican al instante",
    },
}


def _tr(text: str, **kw) -> str:
    """``text`` in the interface language, with ``{n}``-style fields."""
    try:
        from core.i18n import current_language
        lang = current_language()
    except Exception:  # noqa: BLE001
        lang = "en"
    out = _TEXTS.get(lang, {}).get(text, text)
    return out.format(**kw) if kw else out


def _num(v, dec=1) -> str:
    """A number with thousands separators the way the language writes
    them (1,234.5 / 1.234,5)."""
    s = f"{v:,.{dec}f}"
    try:
        from core.i18n import current_language
        lang = current_language()
    except Exception:  # noqa: BLE001
        lang = "en"
    if lang in ("de", "es"):
        s = s.replace(",", "\0").replace(".", ",").replace("\0", ".")
    return s


class WallsError(Exception):
    """A message for the user (already translated)."""


# ---------------------------------------------------------------------------
# 1. Detection — plan segments (metres, x/y) → wall pieces and openings.
#    Pure numpy + shapely, no IngeTrazo objects: testable outside the app.
# ---------------------------------------------------------------------------

def default_params() -> dict:
    return {
        "t_min": 0.05,        # thinnest wall (m)
        "t_max": 0.55,        # thickest wall (m)
        "pairs": True,        # walls drawn as two parallel lines only
        "openings": True,     # detect windows and doors
        "open_min": 0.40,     # narrowest opening (m)
        "open_max": 4.00,     # widest opening (m)
        "height": 2.50,       # wall height (m)
        "sill": 0.90,         # window parapet height (m)
        "lintel": 2.01,       # underside of lintels (m)
        "min_piece": 0.02,    # pieces smaller than this (m²) start switched off
    }


def normalize_params(p) -> dict:
    out = default_params()
    for k, v in (p or {}).items():
        if k in out:
            out[k] = type(out[k])(v)
    out["t_min"] = max(0.01, out["t_min"])
    out["t_max"] = max(out["t_min"] + 0.01, out["t_max"])
    out["open_min"] = max(0.05, out["open_min"])
    out["open_max"] = max(out["open_min"] + 0.05, out["open_max"])
    out["height"] = max(0.05, out["height"])
    out["lintel"] = min(max(0.0, out["lintel"]), out["height"])
    out["sill"] = min(max(0.0, out["sill"]), out["lintel"])
    out["min_piece"] = max(0.0, out["min_piece"])
    return out


_EPS = 1e-4          # geometric tolerance (m)
#: Pieces smaller than this (m²) — window frame profiles drawn like the
#: wall — are built but neither close nor split an opening.
_TINY = 0.02
_ANG = math.radians(2.0)


def _clean_segments(segs):
    """(N, 4) float array without zero-length and duplicate segments."""
    import numpy as np
    s = np.asarray(segs, dtype=float).reshape(-1, 4)
    if not len(s):
        return s
    d = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    s = s[d > _EPS]
    # Same segment either way round → once.
    flip = (s[:, 0] > s[:, 2]) | ((s[:, 0] == s[:, 2]) & (s[:, 1] > s[:, 3]))
    s[flip] = s[flip][:, [2, 3, 0, 1]]
    key = np.round(s / 1e-5).astype(np.int64)
    _u, idx = np.unique(key, axis=0, return_index=True)
    return _join_collinear(s[np.sort(idx)])


def _join_collinear(s, tol=2e-4):
    """Collinear segments that touch or overlap → one segment each (a line
    the PDF drew in pieces runs on as one)."""
    import numpy as np
    if len(s) < 2:
        return s
    vx, vy = s[:, 2] - s[:, 0], s[:, 3] - s[:, 1]
    ang = np.mod(np.arctan2(vy, vx), math.pi)
    ang[ang > math.pi - 1e-6] = 0.0
    groups = {}
    half = round(math.pi / 1e-4)
    for i in range(len(s)):
        ka = round(ang[i] / 1e-4) % half          # 0 and π: the same line
        a = ka * 1e-4
        ux, uy = math.cos(a), math.sin(a)
        off = -s[i, 0] * uy + s[i, 1] * ux             # distance from origin
        groups.setdefault((ka, round(off / tol)), []).append(i)
    out = []
    for (ka, _ko), members in groups.items():
        if len(members) == 1:
            out.append(s[members[0]])
            continue
        a = ka * 1e-4
        ux, uy = math.cos(a), math.sin(a)
        spans = []
        for i in members:
            t0 = s[i, 0] * ux + s[i, 1] * uy
            t1 = s[i, 2] * ux + s[i, 3] * uy
            if t0 <= t1:
                spans.append((t0, t1, s[i, 0], s[i, 1], s[i, 2], s[i, 3]))
            else:
                spans.append((t1, t0, s[i, 2], s[i, 3], s[i, 0], s[i, 1]))
        spans.sort()
        cur = list(spans[0])
        for sp in spans[1:]:
            if sp[0] <= cur[1] + tol:
                if sp[1] > cur[1]:
                    cur[1], cur[4], cur[5] = sp[1], sp[4], sp[5]
            else:
                out.append(np.array(cur[2:]))
                cur = list(sp)
        out.append(np.array(cur[2:]))
    return np.array(out, dtype=float).reshape(-1, 4)


def _through_lines(s, min_len=2.5, overhang=0.3, ext=0.02):
    """Indices of annotation lines drawn ACROSS the plan — section lines,
    grid axes: long, crossing two or more other lines straight through
    (both lines go on past the crossing) and running well past the last
    crossing. A wall line ends at the lines it meets."""
    import numpy as np
    out = []
    if len(s) < 3:
        return out
    from shapely.geometry import LineString
    from shapely.strtree import STRtree
    lines = [LineString([(a, b), (c, d)]) for a, b, c, d in s]
    tree = STRtree(lines)
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    for i in np.nonzero(L > min_len)[0]:
        a, b, c, d = s[i]
        ux, uy = (c - a) / L[i], (d - b) / L[i]
        ts = []
        for j in tree.query(lines[i]):
            j = int(j)
            if j == i:
                continue
            e, f, g, h = s[j]
            vx, vy = g - e, h - f
            den = ux * vy - uy * vx
            if abs(den) < 1e-9:
                continue
            # intersection: (a,b) + t·u = (e,f) + r·v
            t = ((e - a) * vy - (f - b) * vx) / den
            r = ((e - a) * uy - (f - b) * ux) / den
            lj = L[j]
            if ext < t < L[i] - ext and ext / lj < r < 1 - ext / lj:
                ts.append(t)
        if len(ts) >= 2 and (min(ts) > overhang or L[i] - max(ts) > overhang):
            out.append(int(i))
    return out


def _axis_of(poly):
    """``(w, L, ux, uy)``: short and long side of the minimum rotated
    rectangle and the unit direction of the long side."""
    r = poly.minimum_rotated_rectangle
    if r.geom_type != "Polygon":
        return 0.0, 0.0, 1.0, 0.0
    c = list(r.exterior.coords)[:4]
    a = (c[1][0] - c[0][0], c[1][1] - c[0][1])
    b = (c[2][0] - c[1][0], c[2][1] - c[1][1])
    la, lb = math.hypot(*a), math.hypot(*b)
    if la >= lb:
        return lb, la, a[0] / (la or 1), a[1] / (la or 1)
    return la, lb, b[0] / (lb or 1), b[1] / (lb or 1)


def _is_thin(poly, t_min, t_max) -> bool:
    """Nowhere thicker than ``t_max``, somewhere at least ``t_min``."""
    if poly.area < t_min * t_min * 0.5:
        return False
    if not poly.buffer(-t_max / 2.0, join_style=2).is_empty:
        return False
    return not poly.buffer(-t_min * 0.45, join_style=2).is_empty


def _faces(segs):
    """All bounded faces of the drawing (the linework noded)."""
    from shapely.geometry import MultiLineString
    from shapely.ops import polygonize, unary_union
    if not len(segs):
        return []
    ml = MultiLineString([((a, b), (c, d)) for a, b, c, d in segs])
    return [f for f in polygonize(unary_union(ml)) if f.area > _EPS * _EPS]


class _SegIndex:
    """Segment lookup: which drawn lines pass a point in a direction."""

    def __init__(self, segs):
        import numpy as np
        from shapely.geometry import LineString
        from shapely.strtree import STRtree
        self.s = np.asarray(segs, dtype=float)
        self.lines = [LineString([(a, b), (c, d)]) for a, b, c, d in self.s]
        self.tree = STRtree(self.lines)

    def near(self, geom):
        """Indices of segments whose box meets ``geom``'s box."""
        import numpy as np
        return np.asarray(self.tree.query(geom), dtype=int)

    def runs_past(self, x, y, ux, uy, ext=0.02, tol=1e-3, max_len=None) -> bool:
        """Is there a drawn line through (x, y) along (ux, uy) that goes on
        past the point by more than ``ext``? ``max_len``: only lines up to
        that length count."""
        from shapely.geometry import Point
        for i in self.near(Point(x, y).buffer(tol)):
            a, b, c, d = self.s[i]
            vx, vy = c - a, d - b
            L = math.hypot(vx, vy)
            if L < ext or (max_len is not None and L > max_len):
                continue
            vx, vy = vx / L, vy / L
            if abs(vx * uy - vy * ux) > math.sin(_ANG):
                continue
            # distance of the point from the line, its position along it
            if abs((x - a) * vy - (y - b) * vx) > tol:
                continue
            t = (x - a) * vx + (y - b) * vy
            sgn = 1.0 if vx * ux + vy * uy > 0 else -1.0
            # the segment must cover the point and reach ``ext`` beyond it
            ahead = (L - t) if sgn > 0 else t
            if -tol <= t <= L + tol and ahead > ext:
                return True
        return False

    def tick_at(self, x, y, ux, uy, tol=0.02) -> bool:
        """A dimension tick at (x, y): a short oblique stroke centred on
        the point (the architect's slash)."""
        from shapely.geometry import Point
        for i in self.near(Point(x, y).buffer(tol)):
            a, b, c, d = self.s[i]
            L = math.hypot(c - a, d - b)
            if L > 0.6 or L < 1e-3:
                continue
            if math.hypot((a + c) / 2 - x, (b + d) / 2 - y) > tol:
                continue
            cos = abs((c - a) * ux + (d - b) * uy) / L
            if 0.3 < cos < 0.95:
                return True
        return False


#: Longest line that still counts as a dimension's extension line (m).
_EXT_LINE_MAX = 2.5


def _x_corners(poly, idx) -> int:
    """Corners of ``poly``'s rotated rectangle where BOTH drawn lines run on
    past the corner and the line across is short — the extension lines of
    a dimension chain. (A long line across, a section or axis line, does
    not count: it crosses walls too.)"""
    r = poly.minimum_rotated_rectangle
    if r.geom_type != "Polygon":
        return 0
    c = list(r.exterior.coords)[:4]
    n = 0
    for i in range(4):
        x, y = c[i]
        out = []
        for j in ((i - 1) % 4, (i + 1) % 4):     # the two sides at this corner
            vx, vy = x - c[j][0], y - c[j][1]
            L = math.hypot(vx, vy) or 1.0
            out.append((vx / L, vy / L, L))
        (ax, ay, la), (bx, by, lb) = out
        # side ``a`` ends here: its line running on is along the side; the
        # line across is the one along the OTHER side, continuing.
        along, across = ((ax, ay), (bx, by)) if la >= lb else ((bx, by), (ax, ay))
        if idx.runs_past(x, y, *across, max_len=_EXT_LINE_MAX) and (
                idx.runs_past(x, y, *along) or idx.tick_at(x, y, *along)):
            n += 1
    return n


def _rectangular(poly) -> bool:
    r = poly.minimum_rotated_rectangle
    return r.area > 0 and poly.area / r.area > 0.95


def _shared_len(a, b) -> float:
    inter = a.boundary.intersection(b.boundary)
    return getattr(inter, "length", 0.0)


def _parallel(u, v, tol=math.radians(5)) -> bool:
    return abs(u[0] * v[1] - u[1] * v[0]) < math.sin(tol)


def _thin_faces(faces, p):
    """The faces thin enough to be a wall, as pieces."""
    out = []
    for f in faces:
        if _is_thin(f, p["t_min"], p["t_max"]):
            w, L, ux, uy = _axis_of(f)
            out.append({"poly": f, "w": w, "L": L, "u": (ux, uy), "src": "face"})
    return out


def _classify(thin, idx):
    """Wall pieces → ``(pieces, rejected)``: stairs and dimension chains
    dropped, every piece told its stack (pieces side by side along their
    long sides: a window symbol, a layered wall, the steps of a stair)."""
    from shapely.strtree import STRtree
    if not thin:
        return [], []
    # Rungs: rectangles that share a LONG side with a parallel thin
    # rectangle, chained four or more — the steps of a stair. (Hatching
    # cuts a wall into parallelograms: not rectangles, not a stair.)
    tree = STRtree([t["poly"] for t in thin])
    nb = {i: [] for i in range(len(thin))}
    for i, t in enumerate(thin):
        for j in tree.query(t["poly"]):
            j = int(j)
            if j <= i:
                continue
            o = thin[j]
            if not _parallel(t["u"], o["u"]):
                continue
            sh = _shared_len(t["poly"], o["poly"])
            if sh > 0.6 * min(t["L"], o["L"]) and sh > 1.5 * max(t["w"], o["w"]):
                nb[i].append(j)
                nb[j].append(i)
    stack_of, stacks = {}, []
    for i in range(len(thin)):
        if i in stack_of:
            continue
        comp, todo = [], [i]
        stack_of[i] = len(stacks)
        while todo:
            k = todo.pop()
            comp.append(k)
            for m in nb[k]:
                if m not in stack_of:
                    stack_of[m] = len(stacks)
                    todo.append(m)
        stacks.append(comp)
    pieces, rejected = [], []
    for comp in stacks:
        members = [thin[k] for k in comp]
        # the rungs: four or more rectangles of about the same length
        rects = [t["L"] for t in members if _rectangular(t["poly"])]

        # A step is a tread's depth deep (18–40 cm); the layers of a
        # layered wall (plaster, masonry, insulation) are thinner or vary.
        treads = [t for t in members if _rectangular(t["poly"])
                  and 0.18 <= t["w"] <= 0.40]

        def is_rung(t):
            if t not in treads:
                return False
            alike = [o for o in treads if abs(o["L"] - t["L"]) <= 0.3 * t["L"]
                     and abs(o["w"] - t["w"]) <= 0.15 * t["w"]]
            return len(alike) >= 4

        ladder = any(is_rung(t) for t in members)
        for k, t in zip(comp, members):
            t["stack"] = stack_of[k]
            t["stack_size"] = len(comp)
            if ladder and is_rung(t):
                t["why"] = "stair"
                rejected.append(t)
            elif t["src"] == "face" and _x_corners(t["poly"], idx) >= 2:
                t["why"] = "dimension"
                rejected.append(t)
            else:
                pieces.append(t)
    return pieces, rejected


def _pair_strips(segs, idx, p):
    """Walls drawn as two lines: strips between parallel lines at a wall's
    distance with no other parallel line between them and no rungs across."""
    import numpy as np
    from shapely.geometry import LineString, Polygon
    if not len(segs):
        return []
    vx, vy = segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]
    L = np.hypot(vx, vy)
    keep = L >= max(p["t_min"] * 2, 0.20)
    segs, vx, vy, L = segs[keep], vx[keep], vy[keep], L[keep]
    if not len(segs):
        return []
    ang = np.mod(np.arctan2(vy, vx), math.pi)
    out = []
    t_min, t_max = p["t_min"], p["t_max"]
    n = len(segs)
    for i in range(n):
        a0 = ang[i]
        ux, uy = math.cos(a0), math.sin(a0)
        nx, ny = -uy, ux
        x0, y0 = segs[i, 0], segs[i, 1]
        oi_off = 0.0
        si = sorted(((segs[i, 0] - x0) * ux + (segs[i, 1] - y0) * uy,
                     (segs[i, 2] - x0) * ux + (segs[i, 3] - y0) * uy))
        # parallel neighbours (angle wraps at 0/π) beside it, overlapping it
        da = np.abs(ang - a0)
        da = np.minimum(da, math.pi - da)
        o_all = (segs[:, 0] - x0) * nx + (segs[:, 1] - y0) * ny
        p0 = (segs[:, 0] - x0) * ux + (segs[:, 1] - y0) * uy
        p1 = (segs[:, 2] - x0) * ux + (segs[:, 3] - y0) * uy
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        ok = ((da <= _ANG) & (o_all > -t_max - _EPS) & (o_all < t_max + _EPS)
              & (hi > si[0] + _EPS) & (lo < si[1] - _EPS))
        ok[i] = False
        cands = [(float(o_all[j]), (float(lo[j]), float(hi[j])), int(j))
                 for j in np.nonzero(ok)[0]]
        for o, sj, j in cands:
            if not (t_min - _EPS <= o <= t_max + _EPS):
                continue          # only the positive side: each pair once
            s0, s1 = max(si[0], sj[0]), min(si[1], sj[1])
            if s1 - s0 < 0.15:
                continue
            # cut away where another parallel line runs between the two
            free = [(s0, s1)]
            for o2, sk, k in cands:
                if k == j or not (oi_off + 0.01 < o2 < o - 0.01):
                    continue
                nxt = []
                for a, b in free:
                    if sk[1] <= a or sk[0] >= b:
                        nxt.append((a, b))
                        continue
                    if sk[0] > a:
                        nxt.append((a, sk[0]))
                    if sk[1] < b:
                        nxt.append((sk[1], b))
                free = nxt
            for a, b in free:
                if b - a < max(0.15, o * 0.5):
                    continue
                quad = [(x0 + ux * a, y0 + uy * a), (x0 + ux * b, y0 + uy * b),
                        (x0 + ux * b + nx * o, y0 + uy * b + ny * o),
                        (x0 + ux * a + nx * o, y0 + uy * a + ny * o)]
                poly = Polygon(quad)
                # rungs: short lines across both lines inside the strip
                rungs = 0
                for k in idx.near(poly):
                    sx = idx.s[k]
                    kx, ky = sx[2] - sx[0], sx[3] - sx[1]
                    kl = math.hypot(kx, ky)
                    if kl > 3.0 or kl < _EPS:
                        continue
                    if abs(kx * ux + ky * uy) / kl > 0.5:      # not across
                        continue
                    seg = idx.lines[k]
                    inner = LineString([quad[0], quad[1]])
                    outer = LineString([quad[3], quad[2]])
                    if seg.distance(inner) > 1e-3 or seg.distance(outer) > 1e-3:
                        continue
                    # inside the strip, not at its ends
                    m = ((sx[0] + sx[2]) / 2 - x0) * ux + ((sx[1] + sx[3]) / 2 - y0) * uy
                    if a + 0.02 < m < b - 0.02:
                        rungs += 1
                if rungs >= 2:
                    continue
                out.append({"poly": poly, "w": o, "L": b - a, "u": (ux, uy),
                            "src": "pair"})
    return out


def _merge_units(pieces):
    """Pieces → clickable units: pieces split by oblique lines (hatching)
    merge, pieces meeting along their own axis or at right angles stay
    apart (one unit per wall run)."""
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    if not pieces:
        return []
    polys = [q["poly"] for q in pieces]
    tree = STRtree(polys)
    parent = list(range(len(pieces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, q in enumerate(pieces):
        for j in tree.query(q["poly"]):
            j = int(j)
            if j <= i:
                continue
            o = pieces[j]
            inter = q["poly"].intersection(o["poly"])
            if inter.area > 0.2 * min(q["poly"].area, o["poly"].area):
                parent[find(i)] = find(j)          # overlapping (face + pair)
                continue
            sh = q["poly"].boundary.intersection(o["poly"].boundary)
            if getattr(sh, "length", 0.0) < 1e-3:
                continue
            # direction of the shared border
            geoms = getattr(sh, "geoms", [sh])
            seg = max(geoms, key=lambda g: getattr(g, "length", 0.0))
            cs = list(getattr(seg, "coords", []))
            if len(cs) < 2:
                continue
            dx, dy = cs[-1][0] - cs[0][0], cs[-1][1] - cs[0][1]
            dl = math.hypot(dx, dy) or 1.0
            c1 = abs(dx * q["u"][0] + dy * q["u"][1]) / dl
            c2 = abs(dx * o["u"][0] + dy * o["u"][1]) / dl
            oblique = all(0.26 < c < 0.97 for c in (c1, c2))
            if oblique and _parallel(q["u"], o["u"]):
                parent[find(i)] = find(j)
    groups = {}
    for i in range(len(pieces)):
        groups.setdefault(find(i), []).append(i)
    units = []
    for members in groups.values():
        poly = unary_union([pieces[k]["poly"] for k in members]).buffer(0)
        best = max(members, key=lambda k: pieces[k]["poly"].area)
        units.append({"poly": poly, "w": pieces[best]["w"], "u": pieces[best]["u"],
                      "src": pieces[best]["src"],
                      "stack": pieces[best].get("stack"),
                      "stack_size": pieces[best].get("stack_size", 1)})
    return units


def _window_stacks(units, p):
    """Units that are a window symbol: a stack of two or three thin pieces
    side by side, no longer than an opening, whose two ends both touch a
    wall of the stack's full thickness. Returns the indices."""
    from shapely.ops import unary_union
    by_stack = {}
    for i, u in enumerate(units):
        if u.get("stack") is not None and u.get("stack_size", 1) in (2, 3):
            by_stack.setdefault(u["stack"], []).append(i)
    out = set()
    for members in by_stack.values():
        poly = unary_union([units[k]["poly"] for k in members])
        w, L, ux, uy = _axis_of(poly)
        if not (p["open_min"] - 0.05 <= L <= p["open_max"]):
            continue
        # Both short ends of the stack against a wall that spans the stack's
        # whole thickness there.
        ends = 0
        for k, o in enumerate(units):
            if k in members:
                continue
            sh = poly.boundary.intersection(o["poly"].boundary)
            if getattr(sh, "length", 0.0) > 0.8 * w:
                ends += 1
        if ends >= 2:
            out.update(members)
    return out


def _openings(walls, segs_idx, window_polys, p):
    """Gaps in the walls: two wall ends facing each other across an empty
    gap of an opening's width. Window if the gap holds a window symbol or a
    line along the wall, door otherwise."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    if walls.is_empty:
        return []
    t_min, t_max = p["t_min"], p["t_max"]
    # The jambs: short straight pieces of the walls' outline.
    from shapely.geometry.polygon import orient
    jambs = []
    polys = getattr(walls, "geoms", [walls])
    for poly in polys:
        # Exterior ccw, holes cw: the wall is always on the left, so the
        # right-hand normal points out of the wall.
        poly = orient(poly.simplify(0), 1.0)
        for ring in [poly.exterior, *poly.interiors]:
            cs = list(ring.coords)
            for (x0, y0), (x1, y1) in zip(cs, cs[1:]):
                L = math.hypot(x1 - x0, y1 - y0)
                if not (t_min * 0.9 <= L <= t_max * 1.05):
                    continue
                ux, uy = (x1 - x0) / L, (y1 - y0) / L
                jambs.append((x0, y0, x1, y1, ux, uy, uy, -ux, L))
    window_area = unary_union(window_polys) if window_polys else None
    found = []
    used = set()
    cand = []
    # Jamb midpoints in a grid of the widest opening: only neighbours meet.
    cell = max(p["open_max"], 0.5)
    grid = {}
    for k, j in enumerate(jambs):
        mx, my = (j[0] + j[2]) / 2, (j[1] + j[3]) / 2
        grid.setdefault((int(mx // cell), int(my // cell)), []).append(k)
    for a in range(len(jambs)):
        xa0, ya0, xa1, ya1, uxa, uya, nxa, nya, La = jambs[a]
        ca = (int(((xa0 + xa1) / 2) // cell), int(((ya0 + ya1) / 2) // cell))
        near = [b for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                for b in grid.get((ca[0] + dx, ca[1] + dy), ()) if b > a]
        for b in near:
            xb0, yb0, xb1, yb1, uxb, uyb, nxb, nyb, Lb = jambs[b]
            if nxa * nxb + nya * nyb > -0.996:        # facing each other
                continue
            mx, my = (xb0 + xb1) / 2 - (xa0 + xa1) / 2, (yb0 + yb1) / 2 - (ya0 + ya1) / 2
            gap = mx * nxa + my * nya
            if not (p["open_min"] <= gap <= p["open_max"]):
                continue
            # side by side: the two jambs overlap across the wall
            sa = sorted((0.0, La))
            pb = sorted(((xb0 - xa0) * uxa + (yb0 - ya0) * uya,
                         (xb1 - xa0) * uxa + (yb1 - ya0) * uya))
            ov = min(sa[1], pb[1]) - max(sa[0], pb[0])
            if ov < 0.8 * max(La, Lb):
                continue
            cand.append((-round(min(La, Lb), 2), gap, a, b,
                         max(sa[0], pb[0]), min(sa[1], pb[1])))
    # The full wall's jambs first (widest across), then the narrowest gap:
    # a window's frame profiles inside the opening come too late to split it.
    cand.sort()
    from shapely.strtree import STRtree
    # Tiny pieces (frame profiles, drawn like the wall) do not close a gap.
    wall_polys = [g for g in polys if g.area >= _TINY]
    wall_tree = STRtree(wall_polys) if wall_polys else None

    def wall_area_in(geom):
        if wall_tree is None:
            return 0.0
        return sum(wall_polys[int(i)].intersection(geom).area
                   for i in wall_tree.query(geom))

    for _neg_t, gap, a, b, s0, s1 in cand:
        if a in used or b in used:
            continue
        xa0, ya0, _x1, _y1, uxa, uya, nxa, nya, _L = jambs[a]
        q = [(xa0 + uxa * s0, ya0 + uya * s0), (xa0 + uxa * s1, ya0 + uya * s1)]
        quad = Polygon([q[0], q[1], (q[1][0] + nxa * gap, q[1][1] + nya * gap),
                        (q[0][0] + nxa * gap, q[0][1] + nya * gap)])
        if wall_area_in(quad) > 0.02 * quad.area:
            continue
        if any(o["poly"].intersection(quad).area > 0.3 * min(quad.area, o["poly"].area)
               for o in found):
            continue                      # inside an opening already found
        # An opening has free sides (the rooms): a gap with walls along its
        # sides is a shaft or a niche between two walls.
        sides = 0.0
        for (px, py) in q:
            side = LineString([(px, py), (px + nxa * gap, py + nya * gap)])
            sides += wall_area_in(side.buffer(0.01, cap_style=2))
        if sides > 0.2 * (2 * gap * 0.02):
            continue
        kind = "door"
        if window_area is not None and window_area.intersection(quad).area > 0.3 * quad.area:
            kind = "window"
        else:
            # glass: drawn lines along the wall (frame, glazing — often in
            # pieces) that together span most of the gap, inside it
            inner_q = quad.buffer(-1e-3)
            spans = []
            for k in segs_idx.near(quad):
                sx = segs_idx.s[k]
                kx, ky = sx[2] - sx[0], sx[3] - sx[1]
                kl = math.hypot(kx, ky) or 1.0
                if abs(kx * nxa + ky * nya) / kl < 0.99:
                    continue
                seg = segs_idx.lines[k].intersection(inner_q)
                if getattr(seg, "length", 0.0) <= 1e-3:
                    continue
                ts = [(x - q[0][0]) * nxa + (y - q[0][1]) * nya
                      for g in getattr(seg, "geoms", [seg]) for x, y in g.coords]
                spans.append((min(ts), max(ts)))
            spans.sort()
            cover, end = 0.0, -1e9
            for t0, t1 in spans:
                if t1 <= end:
                    continue
                cover += t1 - max(t0, end)
                end = t1
            if cover > 0.7 * gap:
                kind = "window"
        used.update((a, b))
        found.append({"poly": quad, "kind": kind, "w": gap, "t": s1 - s0})
    found = _merge_openings(found)
    found.extend(_glass_lines(walls, segs_idx, found, p))
    return found


def _merge_openings(found):
    """Openings side by side across the wall (a rebate steps the jamb, so
    the gap is found once per step) → one opening; a window if any part
    holds glass."""
    from shapely.ops import unary_union
    parent = list(range(len(found)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            a, b = found[i], found[j]
            if a["poly"].distance(b["poly"]) > 1e-4:
                continue
            sh = a["poly"].buffer(1e-4).intersection(b["poly"].boundary)
            if getattr(sh, "length", 0.0) > 0.5 * min(a["w"], b["w"]):
                parent[root(i)] = root(j)
    groups = {}
    for i in range(len(found)):
        groups.setdefault(root(i), []).append(found[i])
    out = []
    for parts in groups.values():
        if len(parts) == 1:
            out.append(parts[0])
            continue
        poly = unary_union([o["poly"] for o in parts]).buffer(0)
        kind = "window" if any(o["kind"] == "window" for o in parts) else "door"
        out.append({"poly": poly, "kind": kind,
                    "w": max(o["w"] for o in parts),
                    "t": sum(o["t"] for o in parts)})
    return out


def _glass_lines(walls, idx, found, p):
    """Windows drawn INTO a filled wall: a loose line inside the wall,
    along it, as long as an opening — the glass. The window is the wall's
    band across that line."""
    import numpy as np
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    from shapely.prepared import prep
    from shapely.strtree import STRtree
    inner = walls.buffer(-1e-3)
    if inner.is_empty:
        return []
    inside = prep(inner)
    wall_polys = _polys(walls)
    wall_tree = STRtree(wall_polys)
    taken = unary_union([o["poly"] for o in found]) if found else None
    taken_p = prep(taken) if taken is not None else None
    out = []
    L_all = np.hypot(idx.s[:, 2] - idx.s[:, 0], idx.s[:, 3] - idx.s[:, 1])
    for k in np.nonzero((L_all >= p["open_min"]) & (L_all <= p["open_max"]))[0]:
        line = idx.lines[k]
        L = line.length
        if not inside.contains(line):
            continue
        if taken_p is not None and taken_p.intersects(line):
            continue
        a, b, c, d = idx.s[k]
        ux, uy = (c - a) / L, (d - b) / L
        nx, ny = -uy, ux
        r = p["t_max"]
        band = LineString([(a, b), (c, d)]).buffer(r, cap_style=2)
        part = unary_union([wall_polys[int(i)].intersection(band)
                            for i in wall_tree.query(band)])
        parts = [g for g in getattr(part, "geoms", [part]) if g.geom_type == "Polygon"]
        part = next((g for g in parts if g.intersects(line)), None)
        if part is None:
            continue
        # the wall's thickness across the line's middle
        mx, my = (a + c) / 2, (b + d) / 2
        cut = LineString([(mx - nx * r, my - ny * r), (mx + nx * r, my + ny * r)])
        cross = part.intersection(cut)
        cs = [g for g in getattr(cross, "geoms", [cross]) if g.length > 0]
        seg = next((g for g in cs if g.distance(line) < 1e-3), None)
        if seg is None:
            continue
        xs = [(x - mx) * nx + (y - my) * ny for x, y in seg.coords]
        o0, o1 = min(xs), max(xs)
        if not (p["t_min"] * 0.9 <= o1 - o0 <= p["t_max"] * 1.05):
            continue
        from shapely.geometry import Polygon
        quad = Polygon([(a + nx * o0, b + ny * o0), (c + nx * o0, d + ny * o0),
                        (c + nx * o1, d + ny * o1), (a + nx * o1, b + ny * o1)])
        out.append({"poly": quad, "kind": "window", "w": L, "t": o1 - o0,
                    "inside": True})
        taken = quad if taken is None else taken.union(quad)
        taken_p = prep(taken)
    return out


def detect(segs, params=None) -> dict:
    """Plan segments ``[(x0, y0, x1, y1), …]`` in metres → preselection.

    Returns ``{"walls": [unit], "openings": [opening], "faces": [poly],
    "rejected": [piece]}``; a unit / opening is a dict with ``poly`` (a
    shapely Polygon) and ``on``; an opening has ``kind`` window/door."""
    p = normalize_params(params)
    segs = _clean_segments(segs)
    if not len(segs):
        return {"walls": [], "openings": [], "faces": [], "rejected": []}
    from shapely.ops import unary_union
    import numpy as np
    through = _through_lines(segs)
    if through:
        segs = np.delete(segs, through, axis=0)
    idx = _SegIndex(segs)
    faces = _faces(segs)
    thin = _thin_faces(faces, p)
    if p["pairs"]:
        # Two lines with no closed outline between them (open line
        # drawings, gaps in the lines): the strips not already a face.
        covered = unary_union([q["poly"] for q in thin]) if thin else None
        for s in _pair_strips(segs, idx, p):
            if covered is not None:
                rest = s["poly"].difference(covered)
                if rest.area < 0.25 * s["poly"].area:
                    continue
            thin.append(s)
    pieces, rejected = _classify(thin, idx)
    units = _merge_units(pieces)
    win_units = _window_stacks(units, p) if p["openings"] else set()
    walls = [dict(u, on=True) for i, u in enumerate(units) if i not in win_units]
    openings = []
    if p["openings"]:
        big = [u["poly"] for u in walls if u["poly"].area >= _TINY]
        wall_geom = unary_union(big) if big else None
        if wall_geom is not None:
            openings = _openings(wall_geom, idx,
                                 [units[i]["poly"] for i in win_units], p)
    for o in openings:
        o["on"] = True
    _settle_small(walls, openings, p)
    used = unary_union([u["poly"] for u in units]) if units else None
    spare = [f for f in faces if used is None
             or f.intersection(used).area < 0.5 * f.area]
    return {"walls": walls, "openings": openings, "faces": spare,
            "rejected": rejected}


# ---------------------------------------------------------------------------
# 1b. Detection by LINE STYLE — the plan as Plan Import (1.2+) keeps it:
#     every line and filled shape with how it was drawn. CAD draws the cut
#     walls in their own way (a fill, a heavy pen): pick that style and the
#     walls come without furniture, stairs or dimensions.
# ---------------------------------------------------------------------------

PLAN_KEY = "plan_import_tool"      # Plan Import's record on a sheet group


def _unpack(rec) -> dict:
    import base64
    import json
    import zlib
    return json.loads(zlib.decompress(base64.b64decode(rec["data"])))


def source_from_record(rec, matrix=None) -> dict:
    """Plan Import's style record → the plan in model metres:
    ``{"styles", "segs": {sid: (N, 4)}, "fills": [(sid, Polygon)],
    "all": (M, 4), "sid_all": (M,), "z"}``. ``matrix``: a 4×4 numpy
    array, the group's placement since the import (None = as imported)."""
    import numpy as np
    from shapely import affinity
    data = _unpack(rec)
    g = float(rec.get("grid", 1000))
    mpp = float(rec["mpp"])
    o = np.asarray(rec["offset"], dtype=float)
    U = np.asarray(rec["axes"][0], dtype=float) * mpp / g
    V = np.asarray(rec["axes"][1], dtype=float) * mpp / g
    if abs(U[2]) > 1e-9 or abs(V[2]) > 1e-9:
        raise WallsError(_tr("The plan must lie flat (a floor plan, not an elevation)."))
    # sheet → model: x' = o + x·U + y·V (then the group's own move)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 3] = U, V, o
    if matrix is not None:
        M = np.asarray(matrix, dtype=float) @ M
    A = M[:2, [0, 1, 3]]                      # the plan's 2-D affine part
    z = float(M[2, 3])
    styles = []
    for st in rec["styles"]:
        st = dict(st)
        st["len_m"] = float(st.get("len", 0.0)) * mpp
        st["area_m2"] = float(st.get("area", 0.0)) * mpp * mpp
        styles.append(st)

    def xy(flat):
        a = np.asarray(flat, dtype=float).reshape(-1, 2)
        return a @ A[:, :2].T + A[:, 2]

    segs, all_s, sid_all = {}, [], []
    for key, runs in data.get("runs", {}).items():
        sid = int(key)
        parts = []
        for run in runs:
            pts = xy(run)
            if len(pts) >= 2:
                parts.append(np.hstack([pts[:-1], pts[1:]]))
        if parts:
            segs[sid] = np.vstack(parts)
            all_s.append(segs[sid])
            sid_all.append(np.full(len(segs[sid]), sid))
    fills = []
    aff = [A[0, 0], A[0, 1], A[1, 0], A[1, 1], A[0, 2], A[1, 2]]
    for f in data.get("fills", []):
        rings = [np.asarray(r, dtype=float).reshape(-1, 2) for r in f["rings"]]
        poly = _fill_poly([r.tolist() for r in rings], f.get("eo", False))
        if poly is None:
            continue
        poly = affinity.affine_transform(poly, aff)
        for part in _polys(poly):
            fills.append((int(f["s"]), part))
    return {"styles": styles, "segs": segs, "fills": fills,
            "all": np.vstack(all_s) if all_s else np.zeros((0, 4)),
            "sid_all": np.concatenate(sid_all) if sid_all else np.zeros(0, int),
            "z": z}


def style_label(st) -> str:
    """«Fill» / «Line 0.35 mm» (+ «hairline»), translated."""
    if st.get("fill"):
        return _tr("Fill")
    w = float(st.get("w") or 0.0)
    if w <= 0.0:
        return _tr("Hairline")
    return _tr("Line {w} mm", w=f"{w:.2f}")


def style_rgb(st) -> tuple:
    c = st.get("fill") or st.get("stroke") or (0.5, 0.5, 0.5)
    return tuple(int(round(v * 255)) for v in c[:3])


def _fill_poly(rings, evenodd):
    """A filled path's area: even-odd = rings toggle, non-zero ≈ union."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    polys = []
    for r in rings:
        if len(r) >= 3:
            g = Polygon(r).buffer(0)
            if not g.is_empty:
                polys.append(g)
    if not polys:
        return None
    if evenodd:
        g = polys[0]
        for q in polys[1:]:
            g = g.symmetric_difference(q)
    else:
        g = unary_union(polys)
    return g.buffer(0) if not g.is_empty else None


def guess_wall_styles(src, params=None) -> list:
    """The styles that are most likely the walls: fills that are mostly
    thin shapes (cut walls, columns); without such a fill the heaviest pen
    that draws a fair share of the lines."""
    p = normalize_params(params)
    styles = src["styles"]
    area, thin = {}, {}
    for sid, poly in src["fills"]:
        a = poly.area
        area[sid] = area.get(sid, 0.0) + a
        if _is_thin(poly, 0.005, max(p["t_max"], 0.6)):
            thin[sid] = thin.get(sid, 0.0) + a
    cand = [(area[s], s) for s in area
            if area[s] >= 1.0 and thin.get(s, 0.0) >= 0.6 * area[s]]
    if cand:
        top = max(a for a, _s in cand)
        return sorted(s for a, s in cand if a >= 0.05 * top)
    lengths = {}
    for sid, segs in src["segs"].items():
        if styles[sid].get("fill"):
            continue
        import numpy as np
        lengths[sid] = float(np.hypot(segs[:, 2] - segs[:, 0],
                                      segs[:, 3] - segs[:, 1]).sum())
    total = sum(lengths.values()) or 1.0
    pens = [(styles[s]["w"], s) for s, L in lengths.items()
            if L >= 0.03 * total and styles[s]["w"] > 0]
    return [max(pens)[1]] if pens else []


def _settle_small(walls, openings, p) -> None:
    """Pieces smaller than ``min_piece`` start switched off where they are
    not wall: inside an opening (the frame profiles of a window, drawn like
    the wall) or lying loose. Small pieces that hang on a wall stay — CAD
    cuts walls into many small fills."""
    from shapely.strtree import STRtree
    limit = p.get("min_piece", 0.0)
    if limit <= 0 or not walls:
        return
    small = [w for w in walls if w["poly"].area < limit]
    if not small:
        return
    big = [w["poly"] for w in walls if w["poly"].area >= limit]
    btree = STRtree(big) if big else None
    holes = [o["poly"] for o in openings]
    otree = STRtree(holes) if holes else None
    for w in small:
        g = w["poly"]
        if otree is not None and any(
                holes[int(i)].intersection(g).area > 0.5 * g.area
                for i in otree.query(g)):
            w["on"] = False                       # a frame profile
            continue
        if btree is None or not any(big[int(i)].distance(g) < 1e-3
                                    for i in btree.query(g.buffer(1e-3))):
            w["on"] = False                       # a loose crumb


#: Cracks up to twice this wide (m) between wall pieces close in the solid.
_SEAM = 0.005

#: A pocket up to this size (m²), walled in all round, is closed by itself.
_POCKET_AUTO = 0.30


def _completes_walls(g, rim_p, pieces, tree, ang=math.radians(2.0), tol=0.003) -> bool:
    """Does the pocket ``g`` complete the walls? Every edge of it either
    lies on a wall, or runs on in line with a wall's own outline from one
    of its ends — the triangle a mitred corner fill leaves open is bounded
    by the two walls' outer faces carried on to the corner."""
    from shapely.geometry import LineString, Point
    cs = list(g.exterior.coords)
    free = 0
    for (x0, y0), (x1, y1) in zip(cs, cs[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-6:
            continue
        if rim_p.contains(LineString([(x0, y0), (x1, y1)])):
            continue                                   # on a wall
        free += 1
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        found = False
        for (px, py) in ((x0, y0), (x1, y1)):
            for i in tree.query(Point(px, py).buffer(tol)):
                ring = pieces[int(i)].exterior.coords
                for (a, b), (c, d) in zip(ring, ring[1:]):
                    m = math.hypot(c - a, d - b)
                    if m < 1e-6:
                        continue
                    vx, vy = (c - a) / m, (d - b) / m
                    if abs(ux * vy - uy * vx) > math.sin(ang):
                        continue                       # not in line
                    # the wall edge ends at the pocket's corner, on its line
                    if min(math.hypot(a - px, b - py),
                           math.hypot(c - px, d - py)) > tol:
                        continue
                    if abs((px - a) * vy - (py - b) * vx) > tol:
                        continue
                    found = True
                    break
                if found:
                    break
            if found:
                break
        if not found:
            return False
    return free > 0


def _pockets(all_segs, walls, p):
    """Unfilled pockets in the walls: faces of the drawing walled in (mostly)
    all round — the hairline seams between two fills, the crossing of two
    walls, a column drawn with an X, an installation shaft. Faces split by
    lines inside (the X) count as one pocket. Small pockets walled in all
    round come switched on, bigger ones (shafts) switched off — they show
    dashed and a click adds them."""
    from shapely.ops import unary_union
    from shapely.prepared import prep
    from shapely.strtree import STRtree
    if not walls or not len(all_segs):
        return []
    pieces = [w["poly"] for w in walls]
    tree = STRtree(pieces)
    near = prep(unary_union(pieces).buffer(0.005))

    def wall_in(geom):
        return sum(pieces[int(i)].intersection(geom).area for i in tree.query(geom))

    cand = []
    for f in _faces(_clean_segments(all_segs)):
        if f.area > 1.5 or not near.intersects(f):
            continue
        if wall_in(f) > 0.5 * f.area:
            continue                                  # wall already
        cand.append(f)
    if not cand:
        return []
    rim = unary_union(pieces).buffer(0.005)
    rim_p = prep(rim)
    out = []
    # A face that completes a wall corner by itself (the triangle a mitred
    # fill leaves open) is taken as it is, before faces are joined.
    rest = []
    for f in cand:
        if f.area < _POCKET_AUTO and _completes_walls(f, rim_p, pieces, tree):
            w, L, ux, uy = _axis_of(f)
            out.append({"poly": f, "w": w, "u": (ux, uy), "src": "pocket",
                        "on": True})
        else:
            rest.append(f)
    cand = rest
    if not cand:
        return out
    # faces of one pocket side by side (an X splits a pocket in four)
    ct = STRtree(cand)
    parent = list(range(len(cand)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, f in enumerate(cand):
        for j in ct.query(f):
            j = int(j)
            if j > i and f.buffer(1e-4).intersection(cand[j].boundary).length > 1e-3:
                parent[root(i)] = root(j)
    groups = {}
    for i in range(len(cand)):
        groups.setdefault(root(i), []).append(cand[i])
    for faces in groups.values():
        poly = unary_union(faces).buffer(0)
        for g in _polys(poly):
            if g.area > 1.5:
                continue
            touch = g.boundary.intersection(rim).length / (g.boundary.length or 1.0)
            corner = g.area < _POCKET_AUTO and _completes_walls(g, rim_p, pieces, tree)
            if touch < 0.6 and not corner:
                continue
            thin = _is_thin(g, 0.0005, p["t_max"] * 1.2)
            if not thin and g.area >= _POCKET_AUTO:
                continue                            # a small room, not wall
            # on by itself: walled in all round (a crossing, a seam, a thin
            # cavity), or its free edges carry the walls' own outlines on (a
            # corner the fill left open). Shafts and cavities stay a choice.
            on = corner or (touch >= 0.97 and g.area < _POCKET_AUTO) or \
                (touch >= 0.9 and _is_thin(g, 0.0005, 0.06))
            w, L, ux, uy = _axis_of(g)
            out.append({"poly": g, "w": w, "u": (ux, uy), "src": "pocket",
                        "on": on})
    return out


def styled_detect(src, chosen, params=None) -> dict:
    """Walls from the chosen styles: their fills are wall pieces as they
    are; their lines go through the line detection (thin faces, pairs).
    Openings are looked for between the pieces, judged with ALL lines (a
    window's glass is drawn in a style of its own)."""
    import numpy as np
    from shapely.ops import unary_union
    p = normalize_params(params)
    styles = src["styles"]
    chosen = set(chosen)
    walls, seen = [], set()
    for sid, poly in src["fills"]:
        if sid not in chosen:
            continue
        # the same fill drawn twice — two halves of a square (same area,
        # same box) are NOT the same: the centre tells them apart
        c = poly.centroid
        key = (round(poly.area, 6), round(c.x, 4), round(c.y, 4)) + \
            tuple(round(v, 4) for v in poly.bounds)
        if key in seen:
            continue
        seen.add(key)
        w, L, ux, uy = _axis_of(poly)
        walls.append({"poly": poly, "w": w, "u": (ux, uy), "src": "fill",
                      "sid": sid, "on": True})
    lines = [src["segs"][s] for s in chosen
             if s in src["segs"] and not styles[s].get("fill")]
    lines = [a for a in lines if len(a)]
    if lines:
        r = detect(np.concatenate(lines), dict(p, openings=False))
        walls.extend(r["walls"])
    openings = []
    if p["openings"] and walls:
        geom = unary_union([w["poly"] for w in walls if w["poly"].area >= _TINY])
        idx = _SegIndex(_clean_segments(src["all"]))
        openings = _openings(geom, idx, [], p)
        for o in openings:
            o["on"] = True
    _settle_small(walls, openings, p)
    walls.extend(_pockets(src["all"], [w for w in walls if w.get("on", True)], p))
    spare = [poly for sid, poly in src["fills"] if sid not in chosen]
    return {"walls": walls, "openings": openings, "faces": spare,
            "rejected": []}


# ---------------------------------------------------------------------------
# 2. Solids — wall plan + openings → one closed mesh (pure, testable).
# ---------------------------------------------------------------------------

def _polys(geom):
    """The polygons of a shapely geometry (any kind), cleaned."""
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom] if geom.area > 1e-8 else []
    out = []
    for g in getattr(geom, "geoms", []):
        out.extend(_polys(g))
    return out


def _tidy(geom):
    """Snap to a 0.01 mm grid and drop collinear points: shared corners
    stay shared between the layers."""
    try:
        import shapely
        geom = shapely.set_precision(geom, 1e-5)
    except Exception:  # noqa: BLE001 — older shapely
        geom = geom.buffer(0)
    return geom.simplify(0)


def solid_layers(walls, openings, p):
    """``[(z0, z1, region)]``: the plan of the walls in each height band.
    A window is open between sill and lintel, a door below the lintel;
    above and below that the opening is wall (parapet, lintel)."""
    from shapely.ops import unary_union
    H = p["height"]
    # Hairline cracks between two fills (a few mm, no line around them to
    # make a pocket) would stand as slits in the solid: closed here.
    walls = walls.buffer(_SEAM, join_style=2, mitre_limit=5.0) \
                 .buffer(-_SEAM, join_style=2, mitre_limit=5.0)
    voids = []
    for o in openings:
        if o["kind"] == "window":
            voids.append((o["poly"], p["sill"], p["lintel"]))
        elif o["kind"] == "door":
            voids.append((o["poly"], 0.0, p["lintel"]))
    cuts = {0.0, H}
    for _poly, z0, z1 in voids:
        cuts.update(z for z in (z0, z1) if 1e-6 < z < H - 1e-6)
    zs = sorted(cuts)
    every = unary_union([walls] + [o["poly"] for o in openings])
    out = []
    for z0, z1 in zip(zs, zs[1:]):
        zm = (z0 + z1) / 2
        holes = [poly for poly, a, b in voids if a < zm < b]
        region = every.difference(unary_union(holes)) if holes else every
        out.append((z0, z1, _tidy(region)))
    # bands with the same plan merge (no needless seams)
    merged = []
    for z0, z1, r in out:
        if merged and merged[-1][2].symmetric_difference(r).area < 1e-8:
            merged[-1] = (merged[-1][0], z1, merged[-1][2])
        else:
            merged.append((z0, z1, r))
    return merged


def solid_faces(layers, z_base=0.0):
    """Faces of the stacked bands as ``[(outer_loop, [hole_loops])]`` with
    3-D points, every normal pointing out of the wall."""
    from shapely.geometry.polygon import orient
    faces = []

    def horiz(geom, z, up):
        for poly in _polys(geom):
            poly = orient(poly, 1.0)                 # exterior ccw from above
            ext = [(x, y, z) for x, y in poly.exterior.coords[:-1]]
            holes = [[(x, y, z) for x, y in h.coords[:-1]] for h in poly.interiors]
            if not up:
                ext = ext[::-1]
                holes = [h[::-1] for h in holes]
            faces.append((ext, holes))

    if not layers:
        return faces
    horiz(layers[0][2], z_base + layers[0][0], up=False)
    horiz(layers[-1][2], z_base + layers[-1][1], up=True)
    for (_a0, a1, ra), (_b0, _b1, rb) in zip(layers, layers[1:]):
        z = z_base + a1
        horiz(_tidy(ra.difference(rb)), z, up=True)     # tops of parapets
        horiz(_tidy(rb.difference(ra)), z, up=False)    # undersides of lintels
    for z0, z1, region in layers:
        za, zb = z_base + z0, z_base + z1
        for poly in _polys(region):
            poly = orient(poly, 1.0)    # wall on the left of every ring
            for ring in [poly.exterior, *poly.interiors]:
                cs = list(ring.coords)[:-1]
                for (x0, y0), (x1, y1) in zip(cs, cs[1:] + cs[:1]):
                    if math.hypot(x1 - x0, y1 - y0) < 1e-7:
                        continue
                    faces.append(([(x0, y0, za), (x1, y1, za),
                                   (x1, y1, zb), (x0, y0, zb)], []))
    return faces


# ---------------------------------------------------------------------------
# 3. IngeTrazo: the plan from the selection, the group, one undo step.
# ---------------------------------------------------------------------------

def _xyz(p) -> tuple:
    return (float(p.x()), float(p.y()), float(p.z()))


def _world_edges(group):
    from core.group import world_mesh
    try:
        return list(world_mesh(group).edges)
    except Exception:  # noqa: BLE001
        return list(group.mesh.edges)


def walls_data(group):
    data = (getattr(group, "ext", None) or {}).get(KEY)
    return data if isinstance(data, dict) else None


def gather(scene):
    """``(segs, z)``: the plan lines of the selection (loose edges, every
    edge inside selected groups) as ``[(x0, y0, x1, y1)]`` and the plan's
    height. Raises WallsError when there is nothing or it is not flat."""
    from core.group import Group
    from core.mesh import Edge
    raw, seen = [], set()
    for ent in scene.selection:
        if isinstance(ent, Edge):
            edges = [ent]
        elif isinstance(ent, Group) and walls_data(ent) is None:
            edges = _world_edges(ent)
        else:
            continue
        for e in edges:
            a, b = _xyz(e.a), _xyz(e.b)
            k = (a, b) if a <= b else (b, a)
            if k in seen or a == b:
                continue
            seen.add(k)
            raw.append(a + b)
    if not raw:
        raise WallsError(_tr("Select the floor plan first (the plan group or its edges)."))
    zs = sorted(v for s in raw for v in (s[2], s[5]))
    z = zs[len(zs) // 2]
    flat = [s for s in raw if abs(s[2] - z) < 1e-3 and abs(s[5] - z) < 1e-3]
    if len(flat) < 0.9 * len(raw):
        raise WallsError(_tr("The plan must lie flat (a floor plan, not an elevation)."))
    return [(s[0], s[1], s[3], s[4]) for s in flat], z


def level_height(scene, z):
    """Storey height from the Levels panel: from the level at ``z`` to the
    next one up (None if the levels do not tell)."""
    data = (getattr(scene, "plugin_data", None) or {}).get("niveles") or {}
    try:
        zs = sorted(float(lv["z"]) for lv in data.get("levels", []))
    except Exception:  # noqa: BLE001
        return None
    if not any(abs(v - z) < 0.05 for v in zs):
        return None
    above = [v for v in zs if v > z + 0.05]
    return (above[0] - z) if above else None


def _group_matrix(group):
    """The group's own placement as a 4×4 numpy array (None = none)."""
    import numpy as np
    m = getattr(group, "xform", None)
    if m is None:
        return None
    try:
        a = np.array([[m.row(i).x(), m.row(i).y(), m.row(i).z(), m.row(i).w()]
                      for i in range(4)], dtype=float)
    except Exception:  # noqa: BLE001
        return None
    return None if np.allclose(a, np.eye(4)) else a


def plan_source(scene):
    """The selected sheet of Plan Import 1.2+ with its line styles, in
    model metres (see ``source_from_record``) — None if the selection holds
    no such sheet. Should the stored drawing not sit where the sheet's
    edges are now (the sheet was moved in a way the record cannot know),
    it is shifted onto them."""
    import numpy as np
    from core.group import Group
    for ent in scene.selection:
        if not isinstance(ent, Group) or walls_data(ent) is not None:
            continue
        rec = (getattr(ent, "ext", None) or {}).get(PLAN_KEY)
        if not isinstance(rec, dict) or "data" not in rec:
            continue
        src = source_from_record(rec, _group_matrix(ent))
        try:
            pts = np.array([_xyz(v) for e in _world_edges(ent) for v in (e.a, e.b)])
        except Exception:  # noqa: BLE001
            pts = np.zeros((0, 3))
        if len(pts) and len(src["all"]):
            a = src["all"]
            lo = np.array([min(a[:, 0].min(), a[:, 2].min()),
                           min(a[:, 1].min(), a[:, 3].min())])
            hi = np.array([max(a[:, 0].max(), a[:, 2].max()),
                           max(a[:, 1].max(), a[:, 3].max())])
            d_lo = pts[:, :2].min(axis=0) - lo
            d_hi = pts[:, :2].max(axis=0) - hi
            if np.abs(d_lo - d_hi).max() < 0.05 and np.abs(d_lo).max() > 0.01:
                T = np.eye(4)
                T[:2, 3] = d_lo
                T[2, 3] = float(np.median(pts[:, 2])) - src["z"]
                base = _group_matrix(ent)
                src = source_from_record(rec, T if base is None else T @ base)
        return src
    return None


def _next_name(scene) -> str:
    base = _tr("Masonry")
    used = {g.name for g in scene.groups}
    if base not in used:
        return base
    n = 2
    while f"{base} {n}" in used:
        n += 1
    return f"{base} {n}"


def build_group(walls, openings, p, z, name):
    """The masonry as ONE group (IfcWall) holding a closed mesh."""
    from PySide6.QtGui import QVector3D
    from core.group import Group
    from core.mesh import Mesh
    layers = solid_layers(walls, openings, p)
    mesh = Mesh()
    for ext, holes in solid_faces(layers, z):
        f = mesh.add_face([QVector3D(*q) for q in ext],
                          [[QVector3D(*q) for q in h] for h in holes])
        if f is not None and getattr(f, "attrs", None) is None:
            f.attrs = {}
    g = Group(mesh=mesh, name=name)
    g.ifc = {"class": "IfcWall", "name": name}
    g.ext = {KEY: {
        "version": VERSION,
        "params": dict(p),
        "z": z,
        "walls": walls.wkt,
        "openings": [{"kind": o["kind"], "poly": o["poly"].wkt} for o in openings],
    }}
    return g


_CMD = None


def _command_class():
    """Insert the masonry as one undo step. ``select=False`` (the live
    preview) leaves the user's selection alone — the plan stays selected
    while the dialog is open; OK switches it to selecting the walls."""
    global _CMD
    if _CMD is not None:
        return _CMD
    from core.history import Command, InsertGroupCommand

    class WallsCommand(Command):
        def __init__(self, new, select=True):
            self.new = new
            self.select = select
            self._insert = InsertGroupCommand(new)
            self.rev = None

        # The selection as it is NOW stays (minus the walls): the preview
        # is rebuilt while the user selects another plan («Follow
        # selection») — an older selection must not come back with it.
        def do(self, scene):
            before = set(scene.selection)
            self._insert.do(scene)
            scene.selection.clear()
            if self.select:
                scene.selection.add(self.new)
            else:
                scene.selection.update(before - {self.new})
            scene.version += 1

        def undo(self, scene):
            before = set(scene.selection)
            self._insert.undo(scene)
            scene.selection.clear()
            scene.selection.update(before - {self.new})
            scene.version += 1

    _CMD = WallsCommand
    return _CMD


def run_build(viewport, walls, openings, p, z, select=True):
    """Build and insert — one undo step. Returns the command (None when
    there is nothing to build). Raises on a failed insert."""
    if walls.is_empty and not openings:
        return None
    g = build_group(walls, openings, p, z, _next_name(viewport.scene))
    cmd = _command_class()(g, select)
    hist = viewport.history
    hist.execute(cmd)
    err = getattr(hist, "last_error", None)
    if err:
        raise RuntimeError(str(err).split(": ", 1)[-1])
    notify = getattr(viewport, "notify_scene_changed", None)
    if callable(notify):
        notify()
    viewport.update()
    return cmd


def _warn(viewport, text) -> None:
    from PySide6.QtWidgets import QMessageBox
    QMessageBox.warning(viewport.window(), _tr("Walls"), text)


# ---------------------------------------------------------------------------
# 4. The preselection in the model: overlay + a click tool to correct it.
# ---------------------------------------------------------------------------

_STATE = {"dialog": None, "result": None, "z": 0.0, "tool": None,
          "on_change": None, "src": None, "pick_style": False,
          "on_pick": None}


def _style_at(viewport, x, y, tol=6.0):
    """The line style under the pixel: a fill containing it (the smallest),
    else the nearest drawn line within ``tol`` pixels."""
    import numpy as np
    from PySide6.QtCore import QPointF
    src = _STATE.get("src")
    if not src:
        return None
    z = _STATE["z"]
    best = None
    for sid, poly in src["fills"]:
        path = _path(viewport, poly, z)
        if path is not None and path.contains(QPointF(x, y)):
            if best is None or poly.area < best[1]:
                best = (sid, poly.area)
    if best is not None:
        return best[0]
    a = src["all"]
    if not len(a):
        return None
    n = len(a)
    pts = np.empty((2 * n, 3))
    pts[0::2, :2], pts[1::2, :2] = a[:, :2], a[:, 2:]
    pts[:, 2] = z
    px, py, front = viewport.world_to_pixels(pts)
    px, py, front = np.asarray(px), np.asarray(py), np.asarray(front, bool)
    ax, ay, bx, by = px[0::2], py[0::2], px[1::2], py[1::2]
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = np.clip(((x - ax) * vx + (y - ay) * vy) / np.where(L2 > 0, L2, 1), 0, 1)
    d = np.hypot(ax + t * vx - x, ay + t * vy - y)
    d[~(front[0::2] & front[1::2])] = np.inf
    i = int(np.argmin(d))
    return int(src["sid_all"][i]) if d[i] <= tol else None

_RGB = {"wall": (243, 115, 41), "window": (30, 120, 255),
        "door": (24, 160, 80)}


def _path(viewport, poly, z):
    """A shapely polygon as a QPainterPath in screen pixels (None when a
    point is behind the camera)."""
    import numpy as np
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QPainterPath, QPolygonF
    path = QPainterPath()
    path.setFillRule(Qt.OddEvenFill)
    for g in _polys(poly):
        for ring in [g.exterior, *g.interiors]:
            cs = np.array([(x, y, z) for x, y in ring.coords], dtype=float)
            px, py, front = viewport.world_to_pixels(cs)
            if not all(front):
                return None
            path.addPolygon(QPolygonF([QPointF(float(a), float(b))
                                       for a, b in zip(px, py)]))
    return path


def _draw_overlay(viewport, painter) -> None:
    res = _STATE.get("result")
    if not res or _STATE.get("dialog") is None:
        return
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QBrush, QColor, QPen
    z = _STATE["z"]
    painter.setRenderHint(painter.RenderHint.Antialiasing, True)
    items = [(w, "wall" if w.get("on", True) else "off") for w in res["walls"]] + \
            [(o, o["kind"] if o["kind"] in _RGB else "off") for o in res["openings"]]
    for item, kind in items:
        path = _path(viewport, item["poly"], z)
        if path is None:
            continue
        if kind in _RGB:
            rgb = _RGB[kind]
            painter.setPen(QPen(QColor(*rgb), 1.2))
            painter.setBrush(QBrush(QColor(*rgb, 130)))
        else:
            painter.setPen(QPen(QColor(120, 120, 120), 1.2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)


def _hit(viewport, x, y, shift=False):
    """The item under the pixel: ``("opening"|"wall"|"face", index)``."""
    from PySide6.QtCore import QPointF
    res = _STATE.get("result")
    if not res:
        return None
    z, pt = _STATE["z"], QPointF(x, y)
    groups = [("opening", res["openings"]), ("wall", res["walls"])]
    if shift:
        groups.append(("face", res.get("faces", [])))
    for kind, items in groups:
        best = None
        for i, item in enumerate(items):
            poly = item["poly"] if isinstance(item, dict) else item
            path = _path(viewport, poly, z)
            if path is not None and path.contains(pt):
                if best is None or poly.area < best[1]:
                    best = (i, poly.area)
        if best is not None:
            return kind, best[0]
    return None


def _toggle(hit) -> None:
    res = _STATE["result"]
    kind, i = hit
    if kind == "wall":
        w = res["walls"][i]
        w["on"] = not w.get("on", True)
    elif kind == "opening":
        o = res["openings"][i]
        # window → door → none → window
        nxt = {"window": "door", "door": "none", "none": "window"}
        o["kind"] = nxt.get(o["kind"], "window")
    elif kind == "face":
        f = res["faces"].pop(i)
        _w, _L, ux, uy = _axis_of(f)
        res["walls"].append({"poly": f, "w": _w, "u": (ux, uy), "src": "user",
                             "on": True})
    cb = _STATE.get("on_change")
    if callable(cb):
        cb()


def _make_tool_class():
    """Built inside a function on purpose: a ``Tool`` subclass at module
    level would become a one-shot entry in the Extensions menu."""
    from PySide6.QtCore import Qt
    from tools.base import Tool

    class WallsPickTool(Tool):
        name = "Walls"
        shortcut = None
        description = ("Click a wall to switch it on/off, an opening to "
                       "switch window → door → none.")
        uses_snap = False
        box_select = False

        def on_activate(self, viewport) -> None:
            viewport.flash_status(_tr(
                "Click a wall to switch it on/off, an opening to switch window → door → none. Shift-click adds any other face."),
                8000)

        def on_deactivate(self, viewport) -> None:
            viewport.update()

        def on_hover(self, ctx) -> None:
            pass

        def on_click(self, ctx) -> None:
            if _STATE.get("pick_style"):
                sid = _style_at(ctx.viewport, ctx.screen.x(), ctx.screen.y())
                cb = _STATE.get("on_pick")
                if sid is not None and callable(cb):
                    cb(sid)
                return
            shift = bool(ctx.modifiers & Qt.ShiftModifier)
            hit = _hit(ctx.viewport, ctx.screen.x(), ctx.screen.y(), shift)
            if hit is not None:
                _toggle(hit)
                ctx.viewport.update()

        def on_key(self, viewport, key, modifiers) -> bool:
            return False

    return WallsPickTool


def _activate_tool(app) -> None:
    if _STATE["tool"] is None:
        _STATE["tool"] = _make_tool_class()()
    vp, win = app.viewport, app.window
    vp.set_active_tool(_STATE["tool"])
    for action in getattr(win, "_tool_actions", {}).values():
        action.setChecked(False)
    label = getattr(win, "_tool_label", None)
    if label is not None:
        label.setText(_tr("Walls: click to correct the preselection"))


def _back_to_select(app) -> None:
    vp = app.viewport
    if _STATE["tool"] is not None and getattr(vp, "active_tool", None) is _STATE["tool"]:
        fn = getattr(app.window, "_activate_tool", None)
        if callable(fn):
            try:
                fn("select")
            except Exception:  # noqa: BLE001
                pass


# ---------------------------------------------------------------------------
# 5. The dialog (non-modal).
# ---------------------------------------------------------------------------

def read_source(scene) -> dict:
    """The plan of the selection: ``{"src", "segs", "z", "label", "key"}`` —
    a Plan Import 1.2+ sheet with its line styles, else the edges (loose or
    in selected groups). Raises WallsError when there is no plan."""
    from core.group import Group
    src = plan_source(scene)
    if src is not None:
        name = next((g.name for g in scene.selection if isinstance(g, Group)
                     and isinstance((getattr(g, "ext", None) or {}).get(PLAN_KEY), dict)), "")
        n = len(src["all"])
        return {"src": src, "segs": None, "z": src["z"],
                "label": _tr("{name} — {n} lines, {s} line styles",
                             name=name or _tr("Plan"), n=_num(n, 0), s=len(src["styles"])),
                "key": ("src", name, n, round(float(src["all"].sum()), 3) if n else 0)}
    segs, z = gather(scene)
    return {"src": None, "segs": segs, "z": z,
            "label": _tr("{n} edges (no line styles)", n=_num(len(segs), 0)),
            "key": ("segs", len(segs), round(sum(map(sum, segs)), 3))}


def _load_params() -> dict:
    import json
    try:
        from PySide6.QtCore import QSettings
        raw = QSettings().value(f"plugins/{KEY}/params", "")
        return normalize_params(json.loads(raw) if raw else {})
    except Exception:  # noqa: BLE001
        return default_params()


def _save_params(p) -> None:
    import json
    try:
        from PySide6.QtCore import QSettings
        QSettings().setValue(f"plugins/{KEY}/params", json.dumps(p))
    except Exception:  # noqa: BLE001
        pass


def _log_path():
    import os
    from pathlib import Path
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return Path(base) / "IngeTrazo" / "walls_tool.log"


def open_dialog(app) -> None:
    """Menu entry: the dialog — any error shows as a message (and goes to
    walls_tool.log) instead of vanishing in the menu's slot."""
    try:
        _open_dialog(app)
    except Exception:  # noqa: BLE001
        import traceback
        text = traceback.format_exc()
        try:
            path = _log_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(f"--- Walls {VERSION}\n{text}\n")
        except Exception:  # noqa: BLE001
            pass
        try:
            _warn(app.viewport, f"Walls {VERSION}: error\n\n{text}")
        except Exception:  # noqa: BLE001
            pass


def _open_dialog(app) -> None:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog,
                                   QDoubleSpinBox,
                                   QFormLayout, QGroupBox, QHBoxLayout,
                                   QLabel, QListWidget, QListWidgetItem,
                                   QPushButton, QVBoxLayout)
    viewport = app.viewport
    try:
        import shapely  # noqa: F401
    except Exception:  # noqa: BLE001
        _warn(viewport, _tr("Shapely is missing — this IngeTrazo cannot run the wall detection."))
        return
    try:
        S = read_source(viewport.scene)
    except WallsError as exc:
        _warn(viewport, str(exc))
        return
    old = _STATE.get("dialog")
    if old is not None:
        old.close()

    p = _load_params()
    h = level_height(viewport.scene, S["z"])
    if h is not None:
        p["height"] = round(h, 3)

    dlg = QDialog(viewport.window())
    dlg.setWindowTitle(f"{_tr('Walls')} {VERSION}")
    dlg.setModal(False)
    dlg.setAttribute(Qt.WA_DeleteOnClose, True)
    lay = QVBoxLayout(dlg)

    def spin(val, lo, hi, dec, suffix, step):
        s = QDoubleSpinBox(dlg)
        s.setRange(lo, hi)
        s.setDecimals(dec)
        s.setSingleStep(step)
        s.setSuffix(suffix)
        s.setValue(val)
        s.setKeyboardTracking(False)
        return s

    # -- the source: the plan read at opening, followed while open --
    boxs = QGroupBox(_tr("Source"), dlg)
    vs = QVBoxLayout(boxs)
    src_lbl = QLabel(dlg)
    src_lbl.setWordWrap(True)
    vs.addWidget(src_lbl)
    srow = QHBoxLayout()
    follow = QCheckBox("Follow selection", dlg)
    follow.setToolTip(_tr("While the dialog is open, a changed selection is read again by itself: select another floor plan and the walls follow."))
    srow.addWidget(follow)
    srow.addStretch(1)
    b_read = QPushButton("↻ Read selection", dlg)
    b_read.setToolTip(_tr("Take the current selection as the source now."))
    srow.addWidget(b_read)
    vs.addLayout(srow)
    lay.addWidget(boxs)

    # -- line styles (plans from Plan Import 1.2+) --
    box0 = QGroupBox(_tr("Line styles from the PDF — tick the walls"), dlg)
    v0 = QVBoxLayout(box0)
    style_list = QListWidget(dlg)
    style_list.setMinimumHeight(150)
    v0.addWidget(style_list)
    pick_btn = QPushButton(_tr("Click an example wall…"), dlg)
    pick_btn.setCheckable(True)
    pick_btn.setToolTip(_tr("Click a wall line or fill in the model: its line style is switched on (or off)."))
    v0.addWidget(pick_btn)
    lay.addWidget(box0)

    def fill_styles():
        """The style list for the current source (hidden without styles)."""
        src = S["src"]
        style_list.blockSignals(True)
        style_list.clear()
        box0.setVisible(src is not None)
        if src is not None:
            guess = set(guess_wall_styles(src, p))
            styles = src["styles"]
            order = sorted(range(len(styles)), key=lambda s: (
                not styles[s].get("fill"),
                -(styles[s]["area_m2"] if styles[s].get("fill") else styles[s]["len_m"])))
            for sid in order:
                st = styles[sid]
                if st["len_m"] < 0.5 and st["area_m2"] < 0.05:
                    continue
                pm = QPixmap(28, 16)
                pm.fill(Qt.transparent)
                pt = QPainter(pm)
                col = QColor(*style_rgb(st))
                if st.get("fill"):
                    pt.fillRect(2, 2, 24, 12, col)
                else:
                    pen = QPen(col, max(1.0, float(st.get("w") or 0) * 6))
                    pt.setPen(pen)
                    pt.drawLine(2, 8, 26, 8)
                pt.end()
                size = (_tr("{a} m²", a=_num(st['area_m2'], 1)) if st.get("fill")
                        else _tr("{m} m", m=_num(st['len_m'], 0)))
                it = QListWidgetItem(QIcon(pm), f"{style_label(st)} · {size}")
                it.setData(Qt.UserRole, sid)
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                it.setCheckState(Qt.Checked if sid in guess else Qt.Unchecked)
                style_list.addItem(it)
        style_list.blockSignals(False)
        src_lbl.setText(S["label"])
        hint.setText(hint_base + ("" if src is not None else "\n" + _tr(
            "Tip: import the PDF again with Plan Import 1.2 — then the walls are picked by their line style.")))

    box1 = QGroupBox(_tr("Detection"), dlg)
    f1 = QFormLayout(box1)
    t_lo = spin(p["t_min"] * 100, 1, 200, 1, " cm", 0.5)
    t_hi = spin(p["t_max"] * 100, 2, 300, 1, " cm", 0.5)
    row = QHBoxLayout()
    row.addWidget(QLabel(_tr("from"), dlg))
    row.addWidget(t_lo, 1)
    row.addWidget(QLabel(_tr("to"), dlg))
    row.addWidget(t_hi, 1)
    f1.addRow(_tr("Wall thickness"), row)
    pairs = QCheckBox(_tr("Walls drawn as two lines"), dlg)
    pairs.setChecked(p["pairs"])
    f1.addRow(pairs)
    small = spin(p["min_piece"] * 1e4, 0, 1e5, 0, " cm²", 50)
    small.setToolTip(_tr("Pieces smaller than this start switched off (window frame profiles, crumbs of the fill). 0 = keep all."))
    f1.addRow(_tr("Switch off pieces under"), small)
    lay.addWidget(box1)

    box2 = QGroupBox(_tr("Openings"), dlg)
    f2 = QFormLayout(box2)
    opens = QCheckBox(_tr("Detect windows and doors"), dlg)
    opens.setChecked(p["openings"])
    f2.addRow(opens)
    o_max = spin(p["open_max"], 0.5, 20, 2, " m", 0.1)
    f2.addRow(_tr("Max. opening width"), o_max)
    lay.addWidget(box2)

    box3 = QGroupBox(_tr("Heights"), dlg)
    f3 = QFormLayout(box3)
    height = spin(p["height"], 0.1, 50, 3, " m", 0.05)
    sill = spin(p["sill"], 0, 50, 3, " m", 0.05)
    lintel = spin(p["lintel"], 0, 50, 3, " m", 0.05)
    f3.addRow(_tr("Wall height"), height)
    f3.addRow(_tr("Window sill"), sill)
    f3.addRow(_tr("Lintel (underside)"), lintel)
    lay.addWidget(box3)

    info = QLabel(dlg)
    info.setWordWrap(True)
    lay.addWidget(info)
    hint_base = _tr(
        "Click a wall to switch it on/off, an opening to switch window → door → none. Shift-click adds any other face.")
    hint = QLabel(hint_base, dlg)
    hint.setWordWrap(True)
    hint.setStyleSheet("color: palette(mid);")
    lay.addWidget(hint)
    row2 = QHBoxLayout()
    b_all = QPushButton(_tr("All on"), dlg)
    b_none = QPushButton(_tr("All off"), dlg)
    row2.addWidget(b_all)
    row2.addWidget(b_none)
    row2.addStretch(1)
    lay.addLayout(row2)
    pv_lbl = QLabel(dlg)
    pv_lbl.setWordWrap(True)
    pv_lbl.setVisible(False)
    lay.addWidget(pv_lbl)
    row3 = QHBoxLayout()
    pv_btn = QPushButton("Preview", dlg)
    pv_btn.setCheckable(True)
    reset = QPushButton("Reset", dlg)
    reset.setToolTip(_tr("Back to the default settings and the preselection."))
    ok = QPushButton("OK", dlg)
    ok.setDefault(True)
    cancel = QPushButton("Cancel", dlg)
    row3.addWidget(pv_btn)
    row3.addWidget(reset)
    row3.addStretch(1)
    row3.addWidget(ok)
    row3.addWidget(cancel)
    lay.addLayout(row3)

    def params() -> dict:
        return normalize_params({
            "t_min": t_lo.value() / 100, "t_max": t_hi.value() / 100,
            "pairs": pairs.isChecked(), "openings": opens.isChecked(),
            "open_max": o_max.value(), "height": height.value(),
            "sill": sill.value(), "lintel": lintel.value(),
            "min_piece": small.value() / 1e4})

    def chosen_styles():
        if S["src"] is None:
            return []
        return [style_list.item(i).data(Qt.UserRole)
                for i in range(style_list.count())
                if style_list.item(i).checkState() == Qt.Checked]

    # -- live preview (as in every PESI3D plugin): the masonry stands in
    #    the model as ONE undo step and is rebuilt on every change; OK keeps
    #    it, Cancel takes it back.
    pv_style_on = ("QPushButton { background: #2e9e4f; color: white; "
                   "font-weight: bold; border: 1px solid #1f7a3a; "
                   "border-radius: 3px; padding: 3px 8px; }")
    banners = {
        "live": "background: #1f5f33; color: #e8ffe9;",
        "busy": "background: #7a5a12; color: #fff6e0;",
        "error": "background: #7a1f1f; color: #ffecec;",
    }
    pv = {"cmd": None, "rev": 0}

    def banner(kind, text):
        pv_lbl.setStyleSheet(banners[kind] + " padding: 6px 8px; border-radius: 3px;")
        pv_lbl.setText(text)
        pv_lbl.setVisible(True)

    def style_preview(on):
        if on:
            pv_btn.setText("● Live Preview ON")
            pv_btn.setStyleSheet(pv_style_on)
            pv_btn.setToolTip(_tr("The preview follows every change by itself — click to switch it off."))
        else:
            pv_btn.setText("Preview")
            pv_btn.setStyleSheet("")
            pv_btn.setToolTip(_tr("Show the walls in the model; they then update by themselves on every change."))
            pv_lbl.setVisible(False)

    def chosen_parts():
        """``(walls, openings, counts)`` as they would be built now."""
        from shapely.ops import unary_union
        res = _STATE["result"] or {}
        ws = [w["poly"] for w in res.get("walls", []) if w.get("on", True)]
        walls = unary_union(ws) if ws else unary_union([])
        ops = [o for o in res.get("openings", []) if o["kind"] in ("window", "door")]
        nf = sum(1 for o in ops if o["kind"] == "window")
        return walls, ops, (len(ws), nf, len(ops) - nf)

    def undo_preview():
        cmd, pv["cmd"] = pv["cmd"], None
        if cmd is None:
            return
        stack = getattr(viewport.history, "undo_stack", [])
        if stack and stack[-1] is cmd:
            viewport.history.undo()
            viewport.update()

    def refresh_preview():
        undo_preview()
        if not pv_btn.isChecked():
            return
        banner("busy", "⟳ Updating the preview…")
        QApplication.processEvents()
        walls, ops, (nw, nf, nd) = chosen_parts()
        pp = params()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            cmd = run_build(viewport, walls, ops, pp, S["z"], select=False)
        except Exception as exc:  # noqa: BLE001
            banner("error", f"Preview failed: {exc}")
            return
        finally:
            QApplication.restoreOverrideCursor()
        if cmd is None:
            banner("live", "● <b>LIVE PREVIEW</b> — nothing switched on to build")
            return
        cmd.rev = pv["rev"]
        pv["cmd"] = cmd
        banner("live", f"● <b>LIVE PREVIEW</b> — {nw} wall pieces, {nf} windows, "
               f"{nd} doors · height {pp['height']:.2f} m · changes apply instantly")

    pv_timer = QTimer(dlg)
    pv_timer.setSingleShot(True)
    pv_timer.setInterval(300)
    pv_timer.timeout.connect(refresh_preview)

    def changed():
        """Something the result depends on changed: a new revision."""
        pv["rev"] += 1
        if pv_btn.isChecked():
            banner("busy", "⟳ Updating the preview…")
            pv_timer.start()

    def preview_toggled(on):
        style_preview(on)
        try:
            from PySide6.QtCore import QSettings
            QSettings().setValue(f"plugins/{KEY}/preview", bool(on))
        except Exception:  # noqa: BLE001
            pass
        if on:
            refresh_preview()
        else:
            pv_timer.stop()
            undo_preview()

    def count_text():
        res = _STATE["result"] or {}
        ws = [w for w in res.get("walls", []) if w.get("on", True)]
        metres = sum(_axis_of(w["poly"])[1] for w in ws if w["poly"].area >= _TINY)
        nf = sum(1 for o in res.get("openings", []) if o["kind"] == "window")
        nd = sum(1 for o in res.get("openings", []) if o["kind"] == "door")
        info.setText(_tr("{w} wall piece(s), {m} m · {f} window(s) · {d} door(s)",
                         w=len(ws), m=_num(metres, 1), f=nf, d=nd))
        viewport.update()
        changed()

    def detect_now():
        info.setText(_tr("Detecting…"))
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if S["src"] is not None:
                _STATE["result"] = styled_detect(S["src"], chosen_styles(), params())
            else:
                _STATE["result"] = detect(S["segs"], params())
        finally:
            QApplication.restoreOverrideCursor()
        count_text()

    timer = QTimer(dlg)
    timer.setSingleShot(True)
    timer.setInterval(250)
    timer.timeout.connect(detect_now)

    def set_all(on):
        res = _STATE["result"] or {}
        for w in res.get("walls", []):
            w["on"] = on
        count_text()

    def do_reset():
        d = default_params()
        if h is not None:
            d["height"] = round(h, 3)
        widgets = (t_lo, t_hi, o_max, height, sill, lintel, pairs, opens, small)
        for w in widgets:
            w.blockSignals(True)
        t_lo.setValue(d["t_min"] * 100)
        t_hi.setValue(d["t_max"] * 100)
        o_max.setValue(d["open_max"])
        height.setValue(d["height"])
        sill.setValue(d["sill"])
        lintel.setValue(d["lintel"])
        small.setValue(d["min_piece"] * 1e4)
        pairs.setChecked(d["pairs"])
        opens.setChecked(d["openings"])
        for w in widgets:
            w.blockSignals(False)
        if S["src"] is not None:
            guess0 = set(guess_wall_styles(S["src"], d))
            style_list.blockSignals(True)
            for i in range(style_list.count()):
                it = style_list.item(i)
                it.setCheckState(Qt.Checked if it.data(Qt.UserRole) in guess0
                                 else Qt.Unchecked)
            style_list.blockSignals(False)
        detect_now()

    def picked_style(sid):
        """A click on the model in «example wall» mode: that style on/off."""
        if S["src"] is None:
            return
        for i in range(style_list.count()):
            it = style_list.item(i)
            if it.data(Qt.UserRole) == sid:
                on = it.checkState() != Qt.Checked
                it.setCheckState(Qt.Checked if on else Qt.Unchecked)
                style_list.scrollToItem(it)
                style_list.setCurrentItem(it)
                viewport.flash_status(
                    (_tr("Wall style on: {s}") if on else _tr("Wall style off: {s}"))
                    .format(s=it.text()), 4000)
                return

    def on_pick_toggled(on):
        _STATE["pick_style"] = bool(on)
        if on:
            viewport.flash_status(_tr("Click a wall line or fill in the model: its line style is switched on (or off)."), 6000)

    def on_ok():
        pending = timer.isActive()           # a change not detected yet
        timer.stop()
        if pending:
            detect_now()
        pv_timer.stop()
        pp = params()
        _save_params(pp)
        walls, ops, (nw, nf, nd) = chosen_parts()
        cmd = pv["cmd"]
        stack = getattr(viewport.history, "undo_stack", [])
        if cmd is not None and cmd.rev == pv["rev"] and stack and stack[-1] is cmd:
            # The preview IS the result: keep it (already one undo step).
            pv["cmd"] = None
            cmd.select = True
            scene = viewport.scene
            scene.selection.clear()
            scene.selection.add(cmd.new)
            scene.version += 1
            notify = getattr(viewport, "notify_scene_changed", None)
            if callable(notify):
                notify()
            viewport.update()
        else:
            undo_preview()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                cmd = run_build(viewport, walls, ops, pp, S["z"])
            except Exception as exc:  # noqa: BLE001
                QApplication.restoreOverrideCursor()
                _warn(viewport, str(exc))
                return
            QApplication.restoreOverrideCursor()
            if cmd is None:
                _warn(viewport, _tr("Nothing selected to build."))
                return
        viewport.flash_status(_tr("Built: {w} wall piece(s), {f} window(s), {d} door(s)",
                                  w=nw, f=nf, d=nd), 5000)
        sel_timer.stop()
        dlg.accept()

    def on_rejected():
        sel_timer.stop()
        timer.stop()
        pv_timer.stop()
        undo_preview()
        _save_params(params())

    def on_finished(*_a):
        if _STATE.get("dialog") is not dlg:
            return
        _STATE.update(dialog=None, result=None, on_change=None, src=None,
                      pick_style=False, on_pick=None)
        _back_to_select(app)
        try:
            viewport.update()
        except RuntimeError:          # the window is already gone
            pass

    def sel_sig():
        try:
            return frozenset(id(e) for e in viewport.scene.selection)
        except Exception:  # noqa: BLE001
            return frozenset()

    sig = {"v": sel_sig()}

    def read_selection(manual):
        """Take the current selection as the new source. A selection without
        a plan — nothing, or only the walls — keeps the source as it is."""
        try:
            new = read_source(viewport.scene)
        except WallsError:
            if manual:
                viewport.flash_status(_tr("Walls: no floor plan in the selection — the source stays as it is."), 4000)
            return
        if not manual and new["key"] == S["key"]:
            return
        S.update(new)
        _STATE.update(z=S["z"], src=S["src"])
        fill_styles()
        detect_now()

    def poll_selection():
        if not follow.isChecked() or timer.isActive():
            return
        s = sel_sig()
        if s != sig["v"]:
            sig["v"] = s
            read_selection(False)

    def follow_toggled(on):
        try:
            from PySide6.QtCore import QSettings
            QSettings().setValue(f"plugins/{KEY}/follow", bool(on))
        except Exception:  # noqa: BLE001
            pass
        if on:                     # catch up with what changed meanwhile
            sig["v"] = sel_sig()
            read_selection(False)

    sel_timer = QTimer(dlg)
    sel_timer.setInterval(400)
    sel_timer.timeout.connect(poll_selection)

    for w in (t_lo, t_hi, o_max, small):
        w.valueChanged.connect(lambda *_a: timer.start())
    for w in (pairs, opens):
        w.toggled.connect(lambda *_a: timer.start())
    for w in (height, sill, lintel):
        w.valueChanged.connect(lambda *_a: changed())
    style_list.itemChanged.connect(lambda *_a: timer.start())
    pick_btn.toggled.connect(on_pick_toggled)
    follow.toggled.connect(follow_toggled)
    b_read.clicked.connect(lambda: read_selection(True))
    b_all.clicked.connect(lambda: set_all(True))
    b_none.clicked.connect(lambda: set_all(False))
    ok.clicked.connect(on_ok)
    cancel.clicked.connect(dlg.reject)
    reset.clicked.connect(do_reset)
    pv_btn.toggled.connect(preview_toggled)
    dlg.rejected.connect(on_rejected)
    dlg.finished.connect(on_finished)
    dlg.destroyed.connect(on_finished)

    _STATE.update(dialog=dlg, z=S["z"], on_change=count_text, src=S["src"],
                  pick_style=False, on_pick=picked_style)
    try:
        from PySide6.QtCore import QSettings
        follow.blockSignals(True)
        follow.setChecked(QSettings().value(f"plugins/{KEY}/follow", True, type=bool))
        follow.blockSignals(False)
    except Exception:  # noqa: BLE001
        follow.setChecked(True)
    fill_styles()
    style_preview(False)
    dlg.show()
    dlg.raise_()
    detect_now()
    _activate_tool(app)
    sel_timer.start()
    try:
        from PySide6.QtCore import QSettings
        want = QSettings().value(f"plugins/{KEY}/preview", True, type=bool)
    except Exception:  # noqa: BLE001
        want = True
    pv_btn.setChecked(bool(want))


# ---------------------------------------------------------------------------
# 6. Registration.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Toolbar (PESI3D): icons drawn in IngeTrazo's own icon style
# ---------------------------------------------------------------------------

def _pesi3d_icons():
    """Icon key → draw(painter, ink, accent) on a 48 px canvas."""
    from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: F401
    from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF  # noqa: F401

    def walls_icon(p, ink, acc):
        # a plan corner (two lines) rising into a brick wall
        p.setBrush(Qt.NoBrush)
        p.drawPolyline(QPolygonF([QPointF(6, 42), QPointF(6, 26), QPointF(22, 18)]))
        p.drawLine(QPointF(12, 42), QPointF(12, 29))
        p.save()
        p.setPen(Qt.NoPen)
        p.setBrush(acc)
        for x, y in ((18, 33), (31, 33), (24, 25), (37, 25), (18, 41), (31, 41)):
            p.drawRect(QRectF(x, y - 6, 11, 6))
        p.restore()
        p.drawRect(QRectF(17, 18, 26, 24))

    return {"walls": walls_icon}


def _pesi3d_toolbar(app, title, entries):
    """A toolbar of this plugin's own — one icon per command (PESI3D).

    ``entries`` = (icon key, text, tip, callable). The icons are drawn
    like IngeTrazo's own (views/icons.py: 48 px, ink = the palette's text
    colour, 3 px pen, the orange accent) and redrawn when the theme flips.
    The toolbar moves, floats and hides like the built-in ones (right-click
    on any toolbar); its place is kept by its objectName."""
    try:
        from PySide6.QtCore import QEvent, QObject, QSize, Qt
        from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
        from PySide6.QtWidgets import QApplication, QToolBar
    except Exception:  # noqa: BLE001 — no Qt, no toolbar
        return None
    win = getattr(app, "window", None)
    if win is None:
        return None
    draws = _pesi3d_icons()

    def make_icon(key):
        draw = draws.get(key)
        if draw is None:
            return QIcon()
        qa = QApplication.instance()
        ink = (QColor(qa.palette().windowText().color()) if qa is not None
               else QColor(40, 44, 52))
        pm = QPixmap(48, 48)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(ink, 3.0)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        try:
            draw(p, ink, QColor(243, 115, 41))
        finally:
            p.end()
        return QIcon(pm)

    name = f"pesi3d_{getattr(app, 'key', title)}"
    tb = None
    make = getattr(win, "_new_toolbar", None)     # the host's own builder
    if callable(make):
        try:
            tb = make(title, name)
        except Exception:  # noqa: BLE001
            tb = None
    if tb is None:
        tb = QToolBar(title, win)
        tb.setObjectName(name)
        tb.setMovable(True)
        tb.setFloatable(True)
        try:
            from views.icons import toolbar_icon_px
            px = int(toolbar_icon_px())
        except Exception:  # noqa: BLE001
            px = 24
        tb.setIconSize(QSize(px, px))
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        win.addToolBar(Qt.TopToolBarArea, tb)

    actions = []
    for key, text, tip, fn in entries:
        act = QAction(make_icon(key), text, tb)
        act.setToolTip(f"{text}\n{tip}" if tip else text)
        if tip:
            act.setStatusTip(tip)
        act.triggered.connect(lambda _c=False, f=fn: f())
        tb.addAction(act)
        actions.append((act, key))

    class _ThemeWatch(QObject):
        def eventFilter(self, obj, event):  # noqa: N802 — Qt override
            if event.type() in (QEvent.PaletteChange,
                                QEvent.ApplicationPaletteChange,
                                QEvent.StyleChange):
                for a, k in actions:
                    a.setIcon(make_icon(k))
            return False

    watch = _ThemeWatch(tb)
    tb.installEventFilter(watch)
    tb._pesi3d_watch = watch
    _pesi3d_place_later(win)
    return tb


def _pesi3d_place_later(win):
    """A toolbar the saved window layout does not know yet lands at the end
    of the top row, squeezed behind the built-in ones. Once the window is
    laid out, put new PESI3D toolbars on a row of their own under the
    built-in ones — only the first time each one appears; after that the
    user's own arrangement (saved with the window) wins. Every PESI3D
    plugin carries this code; the first one to get here does it for all."""
    if getattr(win, "_pesi3d_place_pending", False):
        return
    win._pesi3d_place_pending = True
    from PySide6.QtCore import QSettings, Qt, QTimer
    from PySide6.QtWidgets import QToolBar

    def place():
        win._pesi3d_place_pending = False
        try:
            st = QSettings()
            key = "plugins/pesi3d/placed_toolbars"
            placed = st.value(key) or []
            if isinstance(placed, str):
                placed = [placed]
            placed = list(placed)
            bars = [t for t in win.findChildren(QToolBar)
                    if t.objectName().startswith("pesi3d_")]
            new = [t for t in bars if t.objectName() not in placed]
            if not new:
                return
            fresh = not placed            # no PESI3D row yet → open one
            for i, t in enumerate(sorted(new, key=lambda t: t.objectName())):
                shown = not t.isHidden()
                win.removeToolBar(t)
                if fresh and i == 0:
                    win.addToolBarBreak(Qt.TopToolBarArea)
                win.addToolBar(Qt.TopToolBarArea, t)
                t.setVisible(shown)
            st.setValue(key, placed + [t.objectName() for t in new])
        except Exception:  # noqa: BLE001 — layout only, never break the app
            pass

    QTimer.singleShot(0, place)


def setup(app) -> None:
    """Extensions ▸ Walls ▸ Walls from Plan…, the same entry in the
    viewport's right-click menu, and a toolbar button."""
    from PySide6.QtCore import QTimer

    tip = _tr("Build walls from the selected floor plan (preselected, click to correct).")
    sub = app.add_menu(_tr("Walls"))
    if sub is not None:
        a = sub.addAction(_tr("Walls from Plan…"))
        a.setStatusTip(tip)
        a.triggered.connect(lambda _c=False: open_dialog(app))
    else:  # pragma: no cover - no Extensions menu
        app.add_menu_action(_tr("Walls from Plan…"), lambda: open_dialog(app), tip=tip)

    def context(menu, selection) -> None:
        if not selection:
            return
        menu.addSeparator()
        act = menu.addAction(_tr("Walls from Plan…"))
        act.triggered.connect(
            lambda _c=False: QTimer.singleShot(0, lambda: open_dialog(app)))

    app.add_context_menu(context)
    app.add_overlay(_draw_overlay)

    _pesi3d_toolbar(app, _tr("Walls"), [
        ("walls", _tr("Walls from Plan…"), tip, lambda: open_dialog(app)),
    ])
