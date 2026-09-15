# LK_gis_helpers

`LK_gis_helpers.py` indeholder hjælpefunktioner til arbejde mellem GeoPandas, Shapely og ArcPy. Modulet kan blandt andet konvertere geometrier til ArcGIS-format, clippe data til en bounding box, beskrive feature classes i en SDE-database og konvertere Esri-geometrier til Shapely.

## Forudsætninger

Modulet kræver ArcPy og de geospatiale Python-pakker:

- ArcGIS Pro med en gyldig ArcPy-installation
- `geopandas`
- `pandas`
- `shapely`

ArcPy installeres normalt sammen med ArcGIS Pro. Modulet bør køres med den Python-interpreter eller conda-environment, hvor ArcPy er tilgængelig.

Øvrige pakker kan installeres med:

```bash
pip install geopandas pandas shapely
```

## Import

```python
from LK_gis_helpers import addESRIGeom, ESRIclip, describeFC, esri_to_shapely
```

## Koordinatsystem

Funktionerne `addESRIGeom` og `ESRIclip` bruger `EPSG:25832` som standard. Inputdata og bounding boxes skal derfor normalt være i ETRS89 / UTM zone 32N, medmindre data transformeres før kaldet.

## `addESRIGeom`

Konverterer geometrien i en GeoPandas `GeoDataFrame` fra WKT til ArcPy-geometri og tilføjer resultatet i kolonnen `SHAPE@`.

```python
from LK_gis_helpers import addESRIGeom

esri_df = addESRIGeom(gdf)
```

### Parametre

| Parameter | Type | Beskrivelse |
| --- | --- | --- |
| `df` | `geopandas.GeoDataFrame` | GeoDataFrame med en aktiv geometri-kolonne. |
| `drop_geom` | `bool` | Fjerner den oprindelige geometri-kolonne, hvis `True`. Standard er `True`. |
| `debug` | `bool` | Udskriver statusbeskeder under konverteringen. Standard er `False`. |

Funktionen returnerer en kopi af inputdata med kolonnen `SHAPE@`. `GEOMETRYCOLLECTION`-geometrier fjernes, fordi de ikke behandles af den aktuelle konvertering.

Bevar den oprindelige Shapely-geometri sådan:

```python
esri_df = addESRIGeom(
    gdf,
    drop_geom=False,
    debug=True,
)
```

Kolonnen `SHAPE@` kan blandt andet bruges som input ved ArcPy-operationer, hvor ArcGIS-geometri forventes.

## `ESRIclip`

Clipper en GeoDataFrame til en rektangulær bounding box.

```python
from LK_gis_helpers import ESRIclip

bbox = [570000, 6200000, 580000, 6210000]
clipped_gdf = ESRIclip(gdf, bbox)
```

### Parametre

| Parameter | Type | Beskrivelse |
| --- | --- | --- |
| `gdf` | `geopandas.GeoDataFrame` | GeoDataFrame med geometrier, der skal klippes. |
| `bbox` | `list` | Fire koordinater i rækkefølgen `[min_x, min_y, max_x, max_y]`. |

Funktionen returnerer en ny GeoDataFrame med geometrien klippet til bounding boxen. Bounding boxens CRS sættes til `EPSG:25832`.

## `describeFC`

Finder og beskriver feature classes i en SDE-database ved hjælp af ArcPy.

```python
from LK_gis_helpers import describeFC

result = describeFC(
    sde=r"C:\data\database.sde",
    schema="GIS",
    feature_class="roads",
)

print(result[["Feature class", "Feature type", "Coordinate system"]])
```

### Parametre

| Parameter | Type | Standard | Beskrivelse |
| --- | --- | --- | --- |
| `sde` | `str` | Påkrævet | Sti til SDE-databasen. |
| `schema` | `str` | `"*"` | Skema, der skal medtages. `"*"` medtager alle skemaer. |
| `feature_class` | `str` | `"*"` | Feature class, der skal beskrives. `"*"` medtager alle feature classes. |

Funktionen returnerer en pandas `DataFrame` med blandt andet:

- Feature class-navn og feature type
- Om feature class har M- eller Z-værdier
- EPSG/factory code og koordinatsystemets navn
- En liste over felter i kolonnen `Fields`
- En ordbog med feltmetadata i kolonnen `Fields dict`
- ArcPy spatial reference i kolonnen `Spatial Reference`

ArcPy workspace ændres til den angivne SDE-sti under kaldet.

## `esri_to_shapely`

Konverterer en ArcGIS-geometri eller en Esri JSON-lignende dictionary til en Shapely-geometri.

```python
from LK_gis_helpers import esri_to_shapely

shapely_geom = esri_to_shapely(arcpy_geom)
```

Funktionen understøtter:

- Punktgeometrier med `x` og `y`
- Linjer med `paths`, som returneres som `MultiLineString`
- Polygoner med `rings`, som returneres som `Polygon`
- `None`, som returneres som `None`

Eksempel med en Esri JSON dictionary:

```python
point = esri_to_shapely({
    "x": 570000,
    "y": 6200000,
})
```

Hvis geometrien ikke genkendes, returnerer funktionen `None`.

## Typisk arbejdsgang

```python
import geopandas as gpd
from LK_gis_helpers import ESRIclip, addESRIGeom

bbox = [570000, 6200000, 580000, 6210000]
gdf = gpd.read_file("input.gpkg")
gdf = ESRIclip(gdf, bbox)
esri_df = addESRIGeom(gdf, drop_geom=False)
```

Sørg for, at inputdata er i `EPSG:25832` før clipping og ArcPy-konvertering:

```python
if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:25832")
else:
    gdf = gdf.to_crs("EPSG:25832")
```
