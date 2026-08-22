# GPX voor Garmin Zumo XT — Marokko 2026

Twee sets van dezelfde 12 dagen:

| Map | Inhoud | Gebruik |
|-----|--------|---------|
| `gpx-zumo/` | `<rte>` route met 4–6 via-punten | Komt binnen als **Trip** → turn-by-turn navigatie |
| `gpx-zumo-track/` | `<trk>` spoor over de echte weg (340–950 punten) + `<wpt>` | Komt binnen als **Track** → hoeft niets te berekenen |

## Wat er mis was met de oude bestanden

Het enige bestand dat wél importeerde (`Dag-00-transit-11-okt…`) ligt volledig in
Spanje en had geen via-punt verder dan 240 m van een weg. Alle andere dagen
bevatten via-punten die honderden meters tot **22 km** van de dichtstbijzijnde
begaanbare weg lagen, zoals:

| Punt | Oude coördinaat | Afstand tot weg | Gecorrigeerd naar |
|------|-----------------|-----------------|-------------------|
| Skoura (dag 6) | 31.2160, -6.4180 | 9,7 km (dorp lag 22 km verkeerd) | 31.0604, -6.5576 |
| Taddert (dag 7) | 31.4670, -7.6580 | 375 m (verkeerd dorp) | 31.3553, -7.3912 |
| Dades-haarspelden (dag 6) | 31.5560, -5.9700 | 5,0 km | 31.5219, -5.9290 (RR704) |
| Ziz-vallei (dag 4) | 31.6870, -4.2570 | 4,8 km | 31.6884, -4.1794 (Aoufous) |
| Selouane (dag 1 + 10) | 34.9130, -2.9420 | 2,0 km (17 km te ver zuid) | 35.0645, -2.9286 |
| Tunnel du Legionnaire (dag 4) | 32.2200, -4.4300 | 2,7 km | 32.2578, -4.5060 (Rich) |
| Demnate (dag 8) | 31.9010, -7.2200 | 841 m | 31.7322, -7.0027 |
| Afourer (dag 8) | 32.2340, -6.4900 | 503 m | 32.2176, -6.4956 |
| Tizi n Tichka (dag 7) | 31.2960, -7.3810 | 310 m | 31.2861, -7.3811 |

Elk via-punt in de nieuwe set is met OSRM op de weg gezet en ligt op **0,0 m**.
Elke dag is getest: OSRM berekent alle 12 routes zonder fout.

## Belangrijk: Marokko-kaart op de Zumo

De Zumo XT wordt geleverd met een **Europa**-kaart; Marokko zit daar niet in.
Zonder Marokko-kaart kan het toestel geen route berekenen in Marokko, hoe correct
het GPX-bestand ook is. Installeer een gratis OpenStreetMap-kaart:

1. Download een Marokko-kaart voor Garmin (bv. `garmin.openstreetmap.nl` of
   Freizeitkarte) — je krijgt een `gmapsupp.img`.
2. Zet die op een microSD in de Zumo, in de map `Garmin/` (hernoem naar
   `gmapsupp2.img` als er al een bestand staat).
3. Zet de kaart aan via Instellingen → Kaart → Kaarten.

Zonder die kaart werken alleen de bestanden uit `gpx-zumo-track/`: een track
wordt getekend zoals hij is en heeft geen routeberekening nodig.

## Overzetten

Zumo via USB aansluiten → bestanden in `Garmin/GPX/` zetten → losmaken en
opnieuw opstarten. Route = Ritplanner, track = Tracks.

## Opnieuw genereren

`python3 tools/build_zumo_gpx.py` (heeft internet nodig voor OSRM).
