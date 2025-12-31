# Konfiguration für PDF-Berichte

Dieses Verzeichnis enthält die Konfigurationsdateien für die PDF-Bericht-Generierung.

## Dateien

### `brand_company.json`
Enthält das Branding Ihrer Firma:
- `company_name`: Name Ihres Unternehmens
- `logo_path`: Pfad zum Firmenlogo
- `brand`: Farben und Schriften (primary_color, secondary_color, accent_color, font_family, font_heading)

### `brand_customer_project.json`
Enthält Kunden- und Projektinformationen:
- `customer`: Name und Logo des Kunden
- `project`: Projektname, Logo und Projekt-ID

### `rule_descriptions.json`
Enthält Beschreibungen aller Regeln in mehreren Sprachen (de, en, fr):
- `title`: Titel der Regel
- `description`: Beschreibung der Regel

### `report_config.example.json`
Beispiel-Konfiguration für einen Bericht:
- `brand_company`: Pfad zur Company-Branding-Datei
- `brand_customer_project`: Pfad zur Customer/Project-Branding-Datei
- `models`: Liste der zu prüfenden IFC-Modelle
- `rules`: Liste der Regel-Namen, die ausgeführt werden sollen
- `language`: Sprache des Berichts (de/en/fr)
- `output`: Output-Konfiguration (report_id, output_dir - optional)

## Verwendung

1. Kopiere `report_config.example.json` zu `report_config.json`
2. Passe die Pfade zu den Branding-Dateien an
3. Füge die zu prüfenden Modelle hinzu
4. Wähle die gewünschten Regeln aus
5. Setze die Sprache (de/en/fr)

## Logos

Logos sollten im `assets/logos/` Verzeichnis gespeichert werden:
- `assets/logos/company_logo.png` - Ihr Firmenlogo
- `assets/logos/customer_logo.png` - Kundenlogo
- `assets/logos/project_logo.png` - Projektlogo

Die Pfade in den JSON-Dateien sollten relativ zum Projekt-Root sein.
