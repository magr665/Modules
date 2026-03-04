import arcpy
import geopandas as gpd


def add_geometry_to_gdf(gdf: gpd.GeoDataFrame, epsg: int = 25832, drop_original_geometry: bool = True) -> gpd.GeoDataFrame:
    """
    Denne funktion, `addGeometry`, konverterer geometri fra en GeoDataFrame til et format, som kan bruges i ArcPy. 
    Funktionen tilføjer en ny kolonne `SHAPE@` til GeoDataFrame'en, som indeholder geometrien i ArcPy-format. 
    Der er også mulighed for at fjerne den oprindelige geometri-kolonne, hvis dette ønskes.

    Parametre:
    ----------
    - df: GeoDataFrame, der indeholder geospatiale data og en geometri-kolonne.
    - epsg: EPSG-koden for det ønskede koordinatsystem. Standard er 25832 (UTM Zone 32N, ETRS89).
    - drop_original_geometry: Boolsk værdi, der angiver, om den oprindelige geometri-kolonne skal fjernes. Standard er `True`.

    Returnerer:
    -----------
    - En kopi af den oprindelige GeoDataFrame med en tilføjet `SHAPE@`-kolonne indeholdende geometrien i ArcPy-format.

    Bemærkninger:
    -------------
    - Funktionen bruger `arcpy.FromWKT` til at konvertere geometri fra Well-Known Text (WKT) til ArcPy-format.
    - SpatialReference EPSG:25832 bruges som standard, hvilket svarer til UTM Zone 32N (ETRS89).
    """
    # Create a copy of the original GeoDataFrame
    new_gdf = gdf.copy(deep=True)

    geometry_field_name = new_gdf.geometry.name
    new_gdf['temp_wkt_field'] = new_gdf[geometry_field_name].apply(lambda geom: geom.wkt if geom is not None else None)
    new_gdf['SHAPE@'] = new_gdf['temp_wkt_field'].apply(lambda wkt: arcpy.FromWKT(wkt, arcpy.SpatialReference(epsg)) if wkt is not None else None)
    new_gdf.drop(columns=['temp_wkt_field'], inplace=True)
    if drop_original_geometry:
        new_gdf.drop(columns=[geometry_field_name], inplace=True)

    return new_gdf