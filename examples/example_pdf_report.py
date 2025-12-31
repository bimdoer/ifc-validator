"""Beispiel für die Generierung von PDF-Berichten mit Quarto."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import IFCValidator
from src.utils.ifc_loader import load_ifc_file, load_multiple_ifc_files
from src.utils.report_config import ReportConfig
from src.utils.report_data_generator import ReportDataGenerator
from src.utils.pdf_report_generator import generate_pdf_from_report_data
import shutil


def main():
    """Hauptfunktion zur Generierung eines PDF-Berichts."""
    
    # 1. Lade Konfiguration
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / "report_config.example.json"
    
    if not config_path.exists():
        print(f"Fehler: Konfigurationsdatei nicht gefunden: {config_path}")
        print("Bitte erstelle eine report_config.json basierend auf report_config.example.json")
        return
    
    config = ReportConfig(str(config_path), base_path=project_root)
    
    # 2. Lade Modelle
    models_config = config.get_models()
    ifc_files = []
    file_names = []
    
    for model_config in models_config:
        file_path = model_config.get('file_path')
        if file_path:
            full_path = project_root / file_path
            if full_path.exists():
                try:
                    ifc_file = load_ifc_file(str(full_path))
                    ifc_files.append(ifc_file)
                    file_names.append(model_config.get('name', Path(file_path).name))
                    print(f"✓ Modell geladen: {model_config.get('name', file_path)}")
                except Exception as e:
                    print(f"✗ Fehler beim Laden von {file_path}: {e}")
            else:
                print(f"⚠ Datei nicht gefunden: {full_path}")
    
    if not ifc_files:
        print("Fehler: Keine IFC-Dateien gefunden!")
        return
    
    # 3. Erstelle Validator mit ausgewählten Regeln
    from src.validator.rules import (
        GeometryValidationRule,
        BoundingBoxRule,
        HierarchyRule
    )
    
    # Mapping von Regel-Namen zu Klassen
    rule_classes = {
        'GeometryValidationRule': GeometryValidationRule,
        'BoundingBoxRule': BoundingBoxRule,
        'HierarchyRule': HierarchyRule,
    }
    
    rules = []
    rule_names = config.get_rules()
    for rule_name in rule_names:
        if rule_name in rule_classes:
            rules.append(rule_classes[rule_name]())
        else:
            print(f"⚠ Unbekannte Regel: {rule_name}")
    
    if not rules:
        print("⚠ Keine Regeln gefunden, verwende Standard-Regeln")
        validator = IFCValidator()
    else:
        validator = IFCValidator(rules=rules)
    
    # 4. Führe Validierung durch
    print("\nStarte Validierung...")
    if len(ifc_files) == 1:
        report = validator.validate(ifc_files[0])
    else:
        report = validator.validate_multiple(ifc_files, file_names=file_names)
    
    print(f"✓ Validierung abgeschlossen: {len(report.results)} Ergebnisse")
    
    # 5. Generiere ReportData (nur im Speicher, nicht speichern)
    print("\nGeneriere ReportData...")
    generator = ReportDataGenerator(report, config)
    report_data = generator.generate()
    report_id = report_data['metadata']['report_id']
    print(f"✓ ReportData generiert: {report_id}")
    
    # 6. Sammle Logo-Pfade
    company_brand = config.get_company_brand()
    customer_project = config.get_customer_project()
    
    logo_paths = {
        'customer': None,
        'project': None,
        'company': None
    }
    
    # Resolve Logo-Pfade
    print("\nLade Logos...")
    customer_logo_path = customer_project.get('customer', {}).get('logo_path')
    if customer_logo_path:
        customer_full_path = project_root / customer_logo_path
        print(f"  Kundenlogo: {customer_full_path} (existiert: {customer_full_path.exists()})")
        if customer_full_path.exists():
            logo_paths['customer'] = customer_full_path
            print(f"  ✓ Kundenlogo geladen")
    
    project_logo_path = customer_project.get('project', {}).get('logo_path')
    if project_logo_path:
        project_full_path = project_root / project_logo_path
        print(f"  Projektlogo: {project_full_path} (existiert: {project_full_path.exists()})")
        if project_full_path.exists():
            logo_paths['project'] = project_full_path
            print(f"  ✓ Projektlogo geladen")
    
    company_logo_path = company_brand.get('logo_path')
    if company_logo_path:
        company_full_path = project_root / company_logo_path
        print(f"  Firmenlogo: {company_full_path} (existiert: {company_full_path.exists()})")
        if company_full_path.exists():
            logo_paths['company'] = company_full_path
            print(f"  ✓ Firmenlogo geladen")
    
    # 7. Generiere PDF direkt (ohne Ordner, direkt im Download-Ordner)
    print("\nGeneriere PDF...")
    from src.utils.path_helpers import get_download_folder
    download_folder = get_download_folder()
    pdf_path = download_folder / f"{report_id}.pdf"
    
    try:
        # Temporäres JSON-File für PDF-Generierung (wird danach gelöscht)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
            import json
            json.dump(report_data, tmp_file, indent=2, ensure_ascii=False)
            tmp_json_path = Path(tmp_file.name)
        
        generate_pdf_from_report_data(
            report_data_path=tmp_json_path,
            output_pdf_path=pdf_path,
            logo_paths=logo_paths
        )
        
        # Lösche temporäres JSON-File
        tmp_json_path.unlink()
        
        print("✓ PDF erfolgreich generiert!")
        print(f"✓ PDF gespeichert: {pdf_path}")
    except ImportError as e:
        print(f"✗ {e}")
        print("\nBitte installiere Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
    except Exception as e:
        print(f"✗ Fehler beim Generieren des PDFs: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✓ PDF-Datei: {pdf_path}")


if __name__ == "__main__":
    main()
