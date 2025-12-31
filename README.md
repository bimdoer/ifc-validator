# IFC Validator

Ein Python-basiertes Tool zur Validierung von IFC-Dateien mit konfigurierbaren Prüfregeln.

## Features

- Lokale Prüfregeln für IFC-Dateien
- Erweiterbare Regel-Engine
- Detaillierte Validierungsberichte
- Vorbereitet für WebAssembly-Export

## Installation

```bash
pip install -r requirements.txt
```

## Verwendung

```python
from src.validator import IFCValidator
from src.utils.ifc_loader import load_ifc_file

# IFC-Datei laden
ifc_file = load_ifc_file("path/to/file.ifc")

# Validator erstellen
validator = IFCValidator()

# Validierung durchführen
results = validator.validate(ifc_file)

# Ergebnisse anzeigen
print(results.get_report())
```

## Entwicklung

```bash
# Tests ausführen
pytest tests/

# Beispiel ausführen
python examples/example_usage.py
```

## Roadmap

- [ ] WebAssembly-Unterstützung
- [ ] TypeScript-Integration
- [ ] Vercel-Hosting
- [ ] Web-UI

