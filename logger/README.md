
# Logger-modul

Et Python-loggingsværktøj til administrering af logfiler med flere logningsniveauer, automatisk filrotation og understøttelse af fejlfindingstilstand.

## Funktioner

- **Flere logningsniveauer**: Info-, advarsel-, fejl- og kritiske meddelelser
- **Automatisk filrotation**: Vedligeholder et konfigurerbart antal logfiler
- **Fejlfindingstilstand**: Forbedret logging med yderligere fejlfindingsoplysninger
- **Konsoloutput**: Valgfri udskrift af meddelelser til konsol
- **Sporing af forløbet tid**: Automatisk timing af scriptudførelse
- **Samlet statistik**: Rapporter advarsler, kritiske fejl og fejl ved logafslutning

## Installation

Placer `logger.py`-filen i dit Python-projektmapppen.  
eller i den mappe hvor du har andre python moduler og har opsat  
Path-variablen i system settings til at pege på denne mappe

## Anvendelse

```python
from logger import Logger

# Opret logger-instans
log = Logger(path="./logs", filename="app", debug=False, print_msg=True)

# Start logging
log.start()

# Log meddelelser
log.info("Applikation startet")
log.warning("Dette er en advarsel")
log.error("En fejl opstod")
log.critical("Kritisk problem opdaget")

# Afslut logging med samlet statistik
log.end()

# Kontroller for problemer
if log.checklog('all'):
    print("Ingen problemer fundet")
```

## Parametre

| Parameter | Type | Standard | Beskrivelse |
|-----------|------|---------|-------------|
| `path` | str | Modulmappe | Logfilmappe |
| `filename` | str | "log" | Logfilnavn (uden filtypenavn) |
| `date_at_end` | bool | True | Tilføj tidsstempel til filnavn |
| `num_of_logs` | int | 10 | Antal logfiler, der skal bevares |
| `debug` | bool | False | Aktivér fejlfindingstilstand |
| `print_msg` | bool | False | Udskriv meddelelser til konsol |

## Metoder

- `start()` - Initialiser loggingsession
- `info(msg)` - Log informationsmeddelelse
- `warning(msg)` - Log advarselmeddelelse
- `error(msg)` - Log fejlmeddelelse
- `critical(msg)` - Log kritisk meddelelse
- `stars(msg, num=10)` - Log meddelelse med dekorative stjerner
- `end()` - Afslut logging og vis samlet statistik
- `checklog(type='all')` - Bekræft logstatus (returnerer True, hvis ingen problemer)

