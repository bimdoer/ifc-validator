"""Beispiel für die Verwendung des IFC-Validators."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import IFCValidator
from src.utils.ifc_loader import load_ifc_file
from src.validator.rules import RequiredPropertiesRule


def main():
    # IFC-Datei laden - Pfad relativ zum Projekt-Root
    project_root = Path(__file__).parent.parent
    ifc_file = load_ifc_file(str(project_root / "tests" / "fixtures" / "sample.ifc"))
    
    # Validator mit Standard-Regeln erstellen
    validator = IFCValidator()
    
    # Optional: Eigene Regel hinzufügen
    custom_rule = RequiredPropertiesRule(
        required_properties=["Name", "Description"]
    )
    validator.add_rule(custom_rule)
    
    # Validierung durchführen
    report = validator.validate(ifc_file)
    
    # Ergebnisse anzeigen
    print(report.get_report())
    
    # Status prüfen
    if report.is_valid():
        print("\n✓ Validierung erfolgreich!")
    else:
        print(f"\n✗ {len(report.get_errors())} Fehler gefunden")


if __name__ == "__main__":
    main()

