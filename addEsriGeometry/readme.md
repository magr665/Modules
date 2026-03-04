# AddGeometry

Modul til konvertering af geometri fra GeoPandas til ArcPy-format.

## Funktion: `add_geometry_to_gdf`

Konverterer geometri fra en GeoDataFrame til ArcPy-kompatibelt format ved at tilføje en `SHAPE@`-kolonne.

### Parametre

- `gdf` (GeoDataFrame): GeoDataFrame med geospatiale data
- `epsg` (int): EPSG-kode for koordinatsystem. Default: `25832` (UTM Zone 32N, ETRS89)
- `drop_original_geometry` (bool): Fjerner original geometri-kolonne. Default: `True`

### Returværdi

GeoDataFrame med tilføjet `SHAPE@`-kolonne i ArcPy-format.  
Som så kan bruges sammen med arcpy InsertCursor til en SDE featureclass.

### Eksempel

```python
import geopandas as gpd
from AddGeometry import add_geometry_to_gdf

gdf = gpd.read_file('data.shp')
gdf_arcpy = add_geometry_to_gdf(gdf, epsg=25832, drop_original_geometry=True)

dest = 'PATH TO FEATURECLASS'
arcpy.TruncateTable_management(dest) ## Hvis FeatureClassen skal tømmes først, ellers skal denne linje fjernes
with arcpy.da.InsertCursor(dest, gdf_arcpy.columns.to_list()) as cursor:
  for row in gdf_arcpy.itertuples(name=None, index=False):
      cursor.insertRow(row)
```

### Note

Funktionen bruger `arcpy.FromWKT` til at konvertere Well-Known Text (WKT) geometri til ArcPy-format.
