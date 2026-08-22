# -*- coding: utf-8 -*-
"""Bouwt Zumo XT-proof GPX-bestanden voor de Marokko motorreis 2026.

Per dag twee varianten:
  gpx-zumo/        <rte>  - route met via-punten (Trip op de Zumo, turn-by-turn)
  gpx-zumo-track/  <trk>  - spoor over de echte weg + waypoints (geen routeberekening nodig)

Alle via-punten worden op de dichtstbijzijnde begaanbare weg gezet (OSRM nearest)
en elke dag wordt bij OSRM getest of hij daadwerkelijk te routeren is.
"""
import json, math, re, subprocess, time
from pathlib import Path

ROOT = Path("/Users/claudeagent/transm-contact/morocco-2026")
OUT_R = ROOT / "gpx-zumo"
OUT_T = ROOT / "gpx-zumo-track"
OSRM = "https://router.project-osrm.org"
SNAP_MAX = 400.0     # m: verder dan dit verplaatsen we niet automatisch
TOL = 0.00015        # ~15 m Douglas-Peucker
MAX_TRKPT = 1000


def curl(url):
    for _ in range(3):
        r = subprocess.run(["curl", "-s", "-m", "40", "-A", "morocco-gpx-fix/1.0"],
                           capture_output=True, text=True, input=None) if False else \
            subprocess.run(["curl", "-s", "-m", "40", "-A", "morocco-gpx-fix/1.0", url],
                           capture_output=True, text=True)
        if r.stdout.strip().startswith(("{", "[")):
            return r.stdout
        time.sleep(2)
    raise RuntimeError(f"curl faalde: {url}")


def nearest(lat, lon):
    w = json.loads(curl(f"{OSRM}/nearest/v1/driving/{lon},{lat}?number=1"))["waypoints"][0]
    return w["distance"], w["location"][1], w["location"][0]


def route(pts):
    coords = ";".join(f"{lo},{la}" for la, lo, _ in pts)
    d = json.loads(curl(f"{OSRM}/route/v1/driving/{coords}?overview=full&geometries=geojson"))
    if d.get("code") != "Ok":
        raise RuntimeError(d.get("code"))
    r = d["routes"][0]
    return [(c[1], c[0]) for c in r["geometry"]["coordinates"]], r["distance"] / 1000, r["duration"] / 3600


def _perp(p, a, b):
    (py, px), (ay, ax), (by, bx) = p, a, b
    dy, dx = by - ay, bx - ax
    if dx == 0 and dy == 0:
        return math.hypot(py - ay, px - ax)
    t = max(0.0, min(1.0, ((py - ay) * dy + (px - ax) * dx) / (dy * dy + dx * dx)))
    return math.hypot(py - (ay + t * dy), px - (ax + t * dx))


def simplify(pts, tol):
    """Douglas-Peucker, iteratief (geen recursielimiet bij 3000+ punten)."""
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        dmax, idx = 0.0, i
        for k in range(i + 1, j):
            d = _perp(pts[k], pts[i], pts[j])
            if d > dmax:
                dmax, idx = d, k
        if dmax > tol:
            keep[idx] = True
            stack += [(i, idx), (idx, j)]
    return [p for p, k in zip(pts, keep) if k]


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


# ---------------------------------------------------------------- dagdefinities
# (lat, lon, naam) - coordinaten geverifieerd via Nominatim/OSRM, zie rapport
DAYS = [
    dict(n="00", file="Dag-00-Moraira-Almeria-ferry",
         name="Dag 0 (11 okt) Moraira - Almeria + nachtferry",
         desc_tail="Kust en binnenland naar de haven. Avond/nachtferry naar Nador.",
         pts=[(38.6873, 0.1440, "Moraira"),
              (38.3452, -0.4810, "Alicante (kust)"),
              (37.9922, -1.1307, "Murcia"),
              (37.1773, -1.8210, "Aguilas (kust)"),
              (36.8315, -2.4766, "Haven Almeria")]),
    dict(n="01", file="Dag-01-Nador-Guercif",
         name="Dag 1 (12 okt) Nador - Guercif",
         desc_tail="Grens Beni Ansar, dan Rif-uitlopers zuidwaarts. Rustige eerste dag.",
         pts=[(35.2680, -2.9330, "Haven Nador (Beni Ansar)"),
              (35.0645, -2.9286, "Selouane"),
              (34.4127, -2.8942, "Taourirt"),
              (34.2270, -3.3530, "Guercif")]),
    dict(n="02", file="Dag-02-Guercif-Midelt-N15",
         name="Dag 2 (13 okt) Guercif - Midelt (N15)",
         desc_tail="Favoriete weg N15: vloeiend, rustig, klimmend berglandschap.",
         pts=[(34.2270, -3.3530, "Guercif"),
              (33.3417, -3.6903, "Outat El Haj (N15)"),
              (33.0470, -3.9890, "Missour"),
              (32.6800, -4.7450, "Midelt - Moonrise Villa VIP")]),
    dict(n="03", file="Dag-03-Midelt-Ifrane-Azrou-lus",
         name="Dag 3 (14 okt) Midelt - Ifrane - Azrou - Midelt",
         desc_tail="Lus zonder bagage. Cederbos, berbermakaken, Ifrane. Terug naar Midelt.",
         pts=[(32.6800, -4.7450, "Midelt"),
              (33.2350, -5.0600, "Timahdite (N13)"),
              (33.5228, -5.1106, "Ifrane"),
              (33.4081, -5.2331, "Cederbos Cedre Gouraud"),
              (33.4342, -5.2214, "Azrou (lunch)"),
              (32.6800, -4.7450, "Midelt - Moonrise Villa VIP")]),
    dict(n="04", file="Dag-04-Midelt-Ziz-Merzouga",
         name="Dag 4 (15 okt) Midelt - Ziz-vallei - Merzouga",
         desc_tail="N13 door de Ziz-vallei de Sahara in. Voor zonsondergang bij Erg Chebbi. Tanken!",
         pts=[(32.6800, -4.7450, "Midelt"),
              (32.2578, -4.5060, "Rich - Tunnel du Legionnaire (N13)"),
              (31.9314, -4.4244, "Errachidia"),
              (31.6884, -4.1794, "Aoufous - Ziz-vallei (N13)"),
              (31.4370, -4.2380, "Erfoud"),
              (31.0990, -4.0130, "Merzouga - Erg Chebbi")]),
    dict(n="05", file="Dag-05-Merzouga-Todra-Dades",
         name="Dag 5 (16 okt) Merzouga - Todra-kloof - Dades",
         desc_tail="Soek van Rissani, Todra-kloof, overnachten in de Dades-kloof.",
         pts=[(31.0990, -4.0130, "Merzouga"),
              (31.2810, -4.2600, "Rissani - soek"),
              (31.5147, -5.5326, "Tinghir"),
              (31.5874, -5.5915, "Todra-kloof"),
              (31.5147, -5.5326, "Tinghir (terug)"),
              (31.3727, -5.9866, "Boumalne Dades")]),
    dict(n="06", file="Dag-06-Dades-Ouarzazate-AitBenhaddou",
         name="Dag 6 (17 okt) Dades-haarspelden - Ouarzazate - Ait Benhaddou",
         desc_tail="R704-haarspelden heen en terug, dan via Ouarzazate naar de UNESCO-ksar.",
         pts=[(31.3727, -5.9866, "Boumalne Dades"),
              (31.5219, -5.9290, "Dades-haarspelden (R704)"),
              (31.3727, -5.9866, "Boumalne (terug)"),
              (31.0604, -6.5576, "Skoura (palmoase)"),
              (30.9200, -6.8930, "Ouarzazate - tank + lunch"),
              (31.0448, -7.1308, "Ait Benhaddou")]),
    dict(n="07", file="Dag-07-AitBenhaddou-Tichka-Marrakech",
         name="Dag 7 (18 okt) Ait Benhaddou - Tizi n Tichka - Marrakech",
         desc_tail="Hoogste pas van de reis (2260 m). Warm aankleden. Defensief rijden in Marrakech.",
         pts=[(31.0448, -7.1308, "Ait Benhaddou"),
              (31.2870, -7.2350, "Kasbah Telouet (optioneel)"),
              (31.2861, -7.3811, "Tizi n Tichka pas 2260 m"),
              (31.3553, -7.3912, "Taddert"),
              (31.6258, -7.9891, "Marrakech - medina")]),
    dict(n="08", file="Dag-08-Marrakech-Ouzoud-BeniMellal",
         name="Dag 8 (19 okt) Marrakech - Ouzoud - Beni Mellal",
         desc_tail="Hoogste watervallen van Marokko, daarna door naar Beni Mellal.",
         pts=[(31.6258, -7.9891, "Marrakech"),
              (31.7322, -7.0027, "Demnate"),
              (32.0152, -6.7193, "Ouzoud-watervallen"),
              (32.2176, -6.4956, "Afourer"),
              (32.3373, -6.3498, "Beni Mellal")]),
    dict(n="09", file="Dag-09-BeniMellal-Khenifra-Midelt",
         name="Dag 9 (20 okt) Beni Mellal - Khenifra - Midelt",
         desc_tail="Beboste Midden-Atlaswegen terug naar Moonrise Villa VIP in Midelt.",
         pts=[(32.3373, -6.3498, "Beni Mellal"),
              (32.5980, -6.2680, "Kasba Tadla"),
              (32.9350, -5.6680, "Khenifra - lunch"),
              (32.6800, -4.7450, "Midelt - Moonrise Villa VIP")]),
    dict(n="10", file="Dag-10-Midelt-Guercif-Nador-ferry",
         name="Dag 10 (21 okt) Midelt - Missour - Guercif - Nador + ferry",
         desc_tail="N15/N2. Vroeg weg 07:30. Tanken in Guercif. Min. 3u voor vertrek bij de terminal.",
         pts=[(32.6800, -4.7450, "Midelt"),
              (33.0470, -3.9890, "Missour - koffie"),
              (34.2270, -3.3530, "Guercif - lunch + tank"),
              (34.4127, -2.8942, "Taourirt"),
              (35.0645, -2.9286, "Selouane"),
              (35.2680, -2.9330, "Haven Nador (Beni Ansar) - FERRY")]),
    dict(n="99", file="Dag-99-Almeria-Moraira",
         name="Dag 11 (22 okt) Almeria - Moraira",
         desc_tail="Ontspannen laatste etappe langs de kust naar huis.",
         pts=[(36.8315, -2.4766, "Haven Almeria"),
              (37.1773, -1.8210, "Aguilas"),
              (37.9922, -1.1307, "Murcia"),
              (38.3452, -0.4810, "Alicante"),
              (38.6873, 0.1440, "Moraira")]),
]

HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" creator="Marokko Motorreis 2026"\n'
        '     xmlns="http://www.topografix.com/GPX/1/1"\n'
        '     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        '     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 '
        'http://www.topografix.com/GPX/1/1/gpx.xsd">\n')


def main():
    report = []
    for d in DAYS:
        snapped, moves = [], []
        for lat, lon, name in d["pts"]:
            dist, sla, slo = nearest(lat, lon)
            if dist <= SNAP_MAX:
                snapped.append((round(sla, 6), round(slo, 6), name))
            else:
                snapped.append((lat, lon, name))
            moves.append((name, dist))
            time.sleep(0.35)

        geom, km, uur = route(snapped)
        time.sleep(0.5)
        trk = simplify(geom, TOL)
        while len(trk) > MAX_TRKPT:
            trk = simplify(trk, TOL * 2)
        d["km"], d["uur"], d["moves"], d["npts"] = km, uur, moves, len(trk)
        u_h = int(uur); u_m = int(round((uur - u_h) * 60))
        d["desc"] = f'{km:.0f} km, ca. {u_h}u{u_m:02d} rijden. ' + d["desc_tail"]

        # ---- route-variant (<rte>)
        o = [HEAD, f'  <metadata><name>{esc(d["name"])}</name>'
                   f'<desc>{esc(d["desc"])}</desc></metadata>\n',
             '  <rte>\n', f'    <name>{esc(d["name"])}</name>\n',
             f'    <desc>{esc(d["desc"])}</desc>\n']
        for la, lo, nm in snapped:
            o.append(f'    <rtept lat="{la:.6f}" lon="{lo:.6f}"><name>{esc(nm)}</name>'
                     f'<sym>Waypoint</sym></rtept>\n')
        o += ['  </rte>\n', '</gpx>\n']
        (OUT_R / f'{d["file"]}.gpx').write_text("".join(o), encoding="utf-8")

        # ---- track-variant (<trk> + <wpt>)
        o = [HEAD, f'  <metadata><name>{esc(d["name"])}</name>'
                   f'<desc>{esc(d["desc"])}</desc></metadata>\n']
        for la, lo, nm in snapped:
            o.append(f'  <wpt lat="{la:.6f}" lon="{lo:.6f}"><name>{esc(nm)}</name>'
                     f'<sym>Flag, Blue</sym></wpt>\n')
        o += ['  <trk>\n', f'    <name>{esc(d["name"])}</name>\n',
              f'    <desc>{esc(d["desc"])}</desc>\n', '    <trkseg>\n']
        o += [f'      <trkpt lat="{a:.5f}" lon="{b:.5f}"></trkpt>\n' for a, b in trk]
        o += ['    </trkseg>\n', '  </trk>\n', '</gpx>\n']
        (OUT_T / f'{d["file"]}.gpx').write_text("".join(o), encoding="utf-8")

        worst = max(m[1] for m in moves)
        print(f'  dag {d["n"]}: {km:6.1f} km / {uur:4.1f} u  '
              f'{len(snapped)} via-punten, {len(trk):4d} trackpunten, '
              f'grootste snap {worst:6.1f} m   {d["file"]}')
        report.append(d)

    print("\n--- correcties per punt (>150 m verplaatst) ---")
    for d in report:
        for nm, dist in d["moves"]:
            if dist > 150:
                print(f'  dag {d["n"]:>2}  {nm:<38} {dist:8.1f} m -> op de weg gezet')


main()
