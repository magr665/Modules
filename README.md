# Mine Python-moduler

Velkommen til mit Python-moduler-repository. Dette projekt indeholder en samling af genbrugelige Python-moduler designet til at strømline almindelige programmeringsopgaver.

## Moduler

### Logger
En simpel logging-modul til logging af applikationshændelser og fejl.

### SHAPE@ Converter
Tilføjer SHAPE@ felt til en geopandas geodataframe, som kan bruges med arcpy InsertCursor til at overføre data til en SDE FeatureClass.

**Afhængigheder**: geopandas, arcpy

### Mailer (LK_emailer)
En Python-mailer til at sende e-mails via SMTP med understøttelse af:
- Almindelig tekst
- HTML-indhold
- BCC-modtagere
- Vedhæftede filer

Se [Mailer/README.md](Mailer/README.md) for mere information.

### WFS Client (LK_WFS_v3)
En WFS-klient til at hente geografiske data fra WFS-tjenester (version 2.0.0+) som GeoPandas GeoDataFrame. Supporterer bounding boxes, authentication, paging og flere andre features.

Se [WFS/README.md](WFS/README.md) for mere information.

## Installation

```bash
pip install -r requirements.txt
```

## Brug

Importer moduler efter behov i dit projekt:

```python
from Modules.logger import Logger
from Modules.shape_converter import add_shape_field
from Mailer.LK_emailer import Mailer
from WFS.LK_WFS_v3 import WFSClient
```

### Logger eksempel
```python
from Modules.logger import Logger

logger = Logger('my_app')
logger.info('Dette er en log-besked')
```

### SHAPE@ Converter eksempel
```python
from Modules.shape_converter import add_shape_field
import geopandas as gpd

gdf = gpd.read_file('data.shp')
gdf = add_shape_field(gdf)
```

### Mailer eksempel
```python
from Mailer.LK_emailer import Mailer

mailer = Mailer()
mailer.sendmail(
    subject="Velkomstmail",
    tos=["bruger@example.com"],
    text="Hej!\n\nVelkommen til vores system.",
    html="<h3>Hej!</h3><p>Velkommen til vores system.</p>",
    bcc=["admin@example.com"]
)
```

Se [Mailer/README.md](Mailer/README.md) for flere eksempler og konfigurationsinstruktioner.

### WFS Client eksempel
```python
from WFS.LK_WFS_v3 import WFSClient

wfs = WFSClient(
    url="https://example.com/wfs",
    bbox=[570000, 6200000, 580000, 6210000],
)

gdf = wfs.get_features("kommuner")
print(gdf.head())
```

Se [WFS/README.md](WFS/README.md) for mere information og parametre.

## Krav

- Python 3.8+
- geopandas
- arcpy (til SHAPE@ modul)
- pandas
- fiona
- requests
- lxml
- shapely

Se individuelle modul-README'er for specifikke afhængigheder.

## Bidrag

Bidrag er velkomne! Indsend venligst pull requests eller åbn issues for fejl og funktionsanmodninger.

## Licens

[Tilføj licens information]
