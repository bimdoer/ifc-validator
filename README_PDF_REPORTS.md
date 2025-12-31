# PDF-Bericht-Generierung mit Quarto

Dieses System generiert professionelle PDF-Berichte aus IFC-Validierungsergebnissen mit Quarto und Typst.

## Voraussetzungen

1. **Quarto installieren**: https://quarto.org/docs/get-started/
   - Quarto bringt Typst automatisch mit
   - Keine separate Typst-Installation nötig

2. **Python-Abhängigkeiten**: Alle Standard-Abhängigkeiten des Projekts

## Schnellstart

1. **Konfiguration erstellen**:
   ```bash
   cd config
   cp report_config.example.json report_config.json
   # Bearbeite report_config.json
   ```

2. **Beispiel ausführen**:
   ```bash
   python examples/example_pdf_report.py
   ```

3. **PDF finden**: 
   - Im Download-Ordner: `Downloads/reports/{report_id}/report.pdf`

## Architektur

### Datenfluss

```
ValidationReport → ReportDataGenerator → report_data.json
                                              ↓
                                    QMD-Template (lädt JSON)
                                              ↓
                                    Quarto → Typst → PDF
```

### Dateistruktur

```
config/
  ├── brand_company.json              # Ihr Firmen-Branding
  ├── brand_customer_project.json     # Kunde + Projekt
  ├── rule_descriptions.json          # Regel-Beschreibungen (mehrsprachig)
  └── report_config.json              # Hauptkonfiguration

templates/
  └── report_template.qmd             # Quarto-Template

reports/{report_id}/
  ├── report_data.json                # Generierte Daten
  ├── report.qmd                      # Kopiertes Template
  ├── report.pdf                      # Finales PDF
  └── assets/logos/                    # Logos
```

## Konfiguration

### Report-ID Format

`{projekt_id}_{YYYYMMDD-HHMM}_quality-report`

Beispiel: `PRJ-2024-001_20250115-1430_quality-report`

### Sprachen

Unterstützt: Deutsch (de), Englisch (en), Französisch (fr)

Setze `language` in `report_config.json`.

## Erweiterte Nutzung

### Manuelle PDF-Generierung

Wenn Quarto nicht automatisch gefunden wird:

```bash
cd Downloads/reports/{report_id}
quarto render report.qmd --to typst-pdf
```

### QMD nachbearbeiten

Das generierte `report.qmd` kann nachträglich bearbeitet werden:
- Text hinzufügen/ändern
- Layout anpassen
- Kommentare einfügen

Beim nächsten Lauf wird es überschrieben, daher:
- Änderungen in `templates/report_template.qmd` machen, oder
- `report.qmd` nach dem Generieren kopieren

### Entity-Info in Regeln

Regeln können jetzt erweiterte Entity-Informationen mitgeben:

```python
self.create_result(
    entity=ifc_wall,
    message="Ungültige Geometrie",
    global_id="2JPIbogtaSJ80doWX10qDb",
    ifc_type="IfcWall",
    storey="EG",
    building="Building A"
)
```

Diese Informationen erscheinen dann in den Findings-Tabellen des PDFs.

## Troubleshooting

### "Quarto nicht gefunden"
- Stelle sicher, dass Quarto installiert ist: `quarto --version`
- Füge Quarto zum PATH hinzu

### "Template nicht gefunden"
- Prüfe, ob `templates/report_template.qmd` existiert
- Prüfe relative Pfade in der Konfiguration

### "Logos werden nicht angezeigt"
- Prüfe, ob Logo-Dateien existieren
- Prüfe Pfade in `brand_company.json` und `brand_customer_project.json`
- Logos werden automatisch nach `assets/logos/` kopiert

### PDF-Rendering-Fehler
- Prüfe Quarto-Logs
- Stelle sicher, dass Typst funktioniert: `quarto check`
- Prüfe QMD-Syntax

## Anpassungen

### Branding ändern

Bearbeite `config/brand_company.json`:
- Farben: Hex-Codes (z.B. `#0066CC`)
- Schriften: CSS-Font-Namen

### Template anpassen

Bearbeite `templates/report_template.qmd`:
- Layout ändern
- Zusätzliche Abschnitte hinzufügen
- Styling anpassen

### Neue Regeln hinzufügen

1. Füge Regel-Beschreibung zu `config/rule_descriptions.json` hinzu
2. Füge Regel zu `report_config.json` → `rules` hinzu
3. Stelle sicher, dass Regel-Klasse in `example_pdf_report.py` gemappt ist
