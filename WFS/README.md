# LK_WFS_v3

`LK_WFS_v3.py` indeholder klassen `WFSClient`, som bruges til at hente geografiske data fra WFS-tjenester som en GeoPandas `GeoDataFrame`.

Klassen håndterer blandt andet:

- Hentning og parsing af `GetCapabilities`
- Kontrol af tilgængelige feature layers
- Hentning af features med `GetFeature`
- Paging af store resultater
- Bounding boxes og automatisk clipping
- Basic authentication
- Konvertering af kolonnenavne, så punktum og bindestreg erstattes med `_`
- Automatisk tilføjelse af kolonnen `xTid`

## Forudsætninger

WFS-tjenesten skal være version **2.0.0 eller nyere**. Version 1.0.0 og 1.1.0 understøttes ikke.

Installer de nødvendige Python-pakker:

```bash
pip install pandas geopandas fiona requests lxml shapely
```

Modulet forventer som udgangspunkt, at data kan behandles i koordinatsystemet `EPSG:25832`. Det gælder især ved clipping til en bounding box.

## Import

```python
from LK_WFS_v3 import WFSClient
```

## Hurtig start

```python
from LK_WFS_v3 import WFSClient

wfs = WFSClient(
    url="https://example.com/wfs",
    bbox=[570000, 6200000, 580000, 6210000],
)

gdf = wfs.get_features("kommuner")

print(gdf.head())
print(gdf.crs)
```

Hvis der ikke angives en `bbox` ved oprettelsen, bruges feature-lagets bounding box fra `GetCapabilities`.

## Authentication

Brug `username` og `password` sammen, hvis WFS-tjenesten kræver login:

```python
wfs = WFSClient(
    url="https://example.com/wfs",
    username="brugernavn",
    password="kodeord",
    bbox=[570000, 6200000, 580000, 6210000],
)
```

Begge værdier skal angives. Hvis kun den ene angives, kastes en `ValueError`.

## Constructor-parametre

`WFSClient` oprettes med en URL samt valgfrie keyword-parametre:

| Parameter | Type | Beskrivelse |
| --- | --- | --- |
| `url` | `str` | URL til WFS-tjenesten. Påkrævet. |
| `username` | `str` | Brugernavn til authentication. |
| `password` | `str` | Kodeord til authentication. |
| `bbox` | `list` | Bounding box som `[minx, miny, maxx, maxy]`. |
| `debug` | `bool` | Udskriver ekstra information under forespørgsler. Standard er `False`. |
| `maxfeatures` | `int` | Maksimalt antal features pr. forespørgsel. Hentes automatisk fra capabilities, hvis den ikke angives. |
| `outputformat` | `str` | Outputformat til WFS-forespørgsler, hvis tjenesten kræver det. |
| `params` | `dict` | Ekstra parametre, som tilføjes til WFS-forespørgsler. |
| `paging` | `bool` | Aktiverer eller deaktiverer paging. Standard er `True`. |
| `logger` | `logging.Logger` | Valgfri logger til status- og fejlbeskeder. Her kan man f.eks. sende den logger med som jeg også har et modul til |

Eksempel med ekstra parametre:

```python
wfs = WFSClient(
    url="https://example.com/wfs",
    params={"whoami": "Lemvig Kommune"},
    debug=True,
)
```

## Hentning af features

```python
gdf = wfs.get_features("lag_navn")
```

Metoden returnerer en GeoPandas `GeoDataFrame`. Den:

1. Henter data for den valgte bounding box.
2. Følger paging-links fra WFS-responsen.
3. Samler siderne i én `GeoDataFrame`.
4. Fjerner dubletter.
5. Omdøber kolonner med `.` eller `-`.
6. Tilføjer `xTid` med tidspunktet for hentningen.
7. Clipper resultatet til den valgte bounding box som standard.

### Valgfrie parametre til `get_features`

```python
gdf = wfs.get_features(
    "lag_navn",
    clip_gdf=False,
    raw_dates=True,
)
```

| Parameter | Type | Beskrivelse |
| --- | --- | --- |
| `clip_gdf` | `bool` | Clipper resultatet til objektets bounding box. Standard er `True`. |
| `raw_dates` | `bool` | Bevarer datoer som tekst i stedet for datetime-værdier. Standard er `False`. |
| `filter` | `str` | Filter til WFS-forespørgslen. Understøttelse afhænger af WFS-tjenesten. |

## Flere bounding boxes

Der kan angives flere bounding boxes efter oprettelsen af klienten:

```python
wfs = WFSClient(url="https://example.com/wfs")
wfs.bboxes = [
    ["570000", "6200000", "580000", "6210000"],
    ["580000", "6200000", "590000", "6210000"],
]

gdf = wfs.get_features("lag_navn")
```

Bounding boxes angives som `[minx, miny, maxx, maxy]`. Ved brug af clipping skal koordinaterne passe til modulets forventede CRS, `EPSG:25832`.

## Fejlhåndtering

Typiske fejl er:

- `ValueError`, hvis WFS-versionen er lavere end 2.0.0.
- `ValueError`, hvis kun `username` eller `password` angives.
- `ValueError`, hvis der ikke findes features i responsen.
- Fejl ved parsing, hvis WFS-tjenesten returnerer et format, som GeoPandas/Fiona ikke kan læse.
- Forbindelsesfejl efter fem forsøg på samme forespørgsel.

## Bemærkninger

- `GetCapabilities` kaldes allerede i `WFSClient`-konstruktøren. Oprettelsen kræver derfor forbindelse til WFS-tjenesten.
- Paging er som standard aktiveret og kræver normalt en WFS 2.0.0-tjeneste.
- `feature_name` skal være navnet på et lag, som findes i WFS-tjenestens capabilities.
- Adgangskoder bør ikke skrives direkte i kildekode, hvis scriptet deles eller versionsstyres.
