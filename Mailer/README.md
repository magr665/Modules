# LK_emailer

En simpel Python-mailer til at sende e-mails via SMTP med understøttelse af:

- almindelig tekst
- HTML-indhold
- BCC-modtagere
- vedhæftede filer

## Fil
- `LK_emailer.py`

## Krav
- Python 3.x
- En fungerende SMTP-server
- En `emailer_args.json`-fil i samme mappe som modulet

## Konfiguration
Modulet læser SMTP-indstillinger fra en JSON-fil med navnet `emailer_args.json`.

Eksempel:

```json
{
  "smtp_server": "smtp.example.com",
  "sender": "noreply@example.com",
  "user": "smtp_user",
  "pass": "smtp_password"
}
```

## Brug
Importer klassen:

```python
from LK_emailer import Mailer
```

Opret en instans:

```python
mailer = Mailer()
```

Send en e-mail:

```python
mailer.sendmail(
    subject="Testmail",
    tos=["modtager@example.com"],
    text="Dette er en tekstmail.",
    html="<p>Dette er en <b>HTML</b> mail.</p>",
    filename=r"C:\sti\til\fil.pdf",
    bcc=["bcc@example.com"]
)
```

## Parametre for `sendmail`
```python
sendmail(subject, tos=None, text=None, html=None, filename=None, bcc=None)
```

- `subject`: E-mailens emne
- `tos`: Liste over modtagere
- `text`: Tekstversion af mailen
- `html`: HTML-version af mailen
- `filename`: Sti til vedhæftet fil
- `bcc`: Liste over BCC-modtagere

## Bemærkninger
- Hvis `tos` ikke angives, bruges afsenderen som modtager.
- `filename` kan være `None`, hvis der ikke skal vedhæftes nogen fil.
- SMTP-porten er hardkodet til `587` i modulet.
- Det er ikke nødvendigt at udfylde både `text` og `html`, bare en af dem

## Eksempel
```python
from LK_emailer import Mailer

mailer = Mailer()

mailer.sendmail(
    subject="Velkomstmail",
    tos=["bruger@example.com"],
    text="Hej!\n\nVelkommen til vores system.",
    html="<h3>Hej!</h3><p>Velkommen til vores system.</p>",
    bcc=["admin@example.com"]
)
```

## Licens
Denne fil er brugt som en lokal Python-hjælper og kan tilpasses efter behov.
