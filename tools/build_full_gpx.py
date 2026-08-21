# -*- coding: utf-8 -*-
"""Builds one GPX with the complete Morocco tour: 10 day tracks that follow the
actual roads (from map.html / OSRM) + all hotel and sight waypoints.

Output: Morocco_Tour_2026_FULL.gpx (and a .zip so iOS keeps the extension).
"""
import json, math, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "map.html"
OUT = ROOT / "Morocco_Tour_2026_FULL.gpx"
TOL = 0.0002          # ~20 m — keeps the roads accurate, cuts the point count


def grab(text, name):
    i = text.index(name + "=") + len(name) + 1
    return json.JSONDecoder().raw_decode(text[i:])[0]


def _perp(p, a, b):
    (py, px), (ay, ax), (by, bx) = p, a, b
    dy, dx = by - ay, bx - ax
    if dx == 0 and dy == 0:
        return math.hypot(py - ay, px - ax)
    t = max(0.0, min(1.0, ((py - ay) * dy + (px - ax) * dx) / (dy * dy + dx * dx)))
    return math.hypot(py - (ay + t * dy), px - (ax + t * dx))


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = _perp(pts[i], pts[0], pts[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)
    return [pts[0], pts[-1]]


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def main():
    html = SRC.read_text(encoding="utf-8")
    days, hotels, sights = grab(html, "const DAYS"), grab(html, "HOTELS"), grab(html, "SIGHTS")

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<gpx version="1.1" creator="Morocco Motorcycle Tour 2026 (Transmark)"',
           '     xmlns="http://www.topografix.com/GPX/1/1"',
           '     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
           '     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">',
           '  <metadata>',
           '    <name>Morocco Motorcycle Tour 2026 - full route (Morocco)</name>',
           '    <desc>10 riding days Nador - Guercif - Midelt - Merzouga - Dades - Ait Benhaddou - '
           'Marrakech - Ouzoud - Midelt - Nador. Tracks follow the actual roads. Hotels and sights as waypoints.</desc>',
           '  </metadata>']

    for lat, lon, name in hotels:
        out.append(f'  <wpt lat="{lat}" lon="{lon}"><name>{esc(name)}</name>'
                   f'<sym>Lodging</sym><type>Hotel</type></wpt>')
    for lat, lon, name in sights:
        out.append(f'  <wpt lat="{lat}" lon="{lon}"><name>{esc(name)}</name>'
                   f'<sym>Scenic Area</sym><type>Sight</type></wpt>')

    total = 0
    for d in days:
        pts = simplify([tuple(p) for p in d["pts"]], TOL)
        total += len(pts)
        label = esc(d["label"])
        out.append(f'  <trk><name>{label}</name><desc>Day {d["n"]} - follows the actual roads</desc>')
        out.append('    <trkseg>')
        out += [f'      <trkpt lat="{a:.5f}" lon="{b:.5f}"/>' for a, b in pts]
        out.append('    </trkseg>')
        out.append('  </trk>')
        print(f"  day {d['n']:>2}: {len(d['pts']):>5} -> {len(pts):>4} points  {d['label']}")

    out.append('</gpx>')
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT.with_suffix(".gpx.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT, OUT.name)

    print(f"\n{OUT.name}: {OUT.stat().st_size // 1024} kB, {len(hotels)} hotels, "
          f"{len(sights)} sights, {len(days)} day tracks, {total} track points")
    print(f"{OUT.with_suffix('.gpx.zip').name}: {OUT.with_suffix('.gpx.zip').stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
