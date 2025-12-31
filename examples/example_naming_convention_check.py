"""Beispiel für die Prüfung von Dateinamen-Konventionen."""

import sys
import webbrowser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import IFCValidator
from src.utils.ifc_loader import load_ifc_file, load_multiple_ifc_files
from src.utils.path_helpers import get_download_folder
from src.validator.rules import FileNameStructureRule, FileNameValueRule
from src.utils.naming_convention_loader import load_naming_convention_config


def print_progress(percentage: int, message: str = ""):
    """Gibt Fortschritt in Prozent aus."""
    bar_length = 20
    filled = int(bar_length * percentage / 100)
    bar = "#" * filled + "-" * (bar_length - filled)
    output = f"\r[{bar}] {percentage}% {message}"
    try:
        print(output, end="", flush=True)
    except UnicodeEncodeError:
        output_ascii = output.encode('ascii', 'replace').decode('ascii')
        print(output_ascii, end="", flush=True)
    if percentage == 100:
        print()


def main():
    # ===== KONFIGURATION =====
    GENERATE_HTML = True
    GENERATE_PDF = True
    PRINT_TEXT_REPORT = True
    
    # Template-Auswahl:
    # - "full" oder "naming_convention_template.json" für vollständiges Template mit allowed_values
    # - "simple" oder "naming_convention_template_simple.json" für einfaches Template nur mit Strukturprüfung
    # - Oder direkter Pfad zu einer JSON-Datei
    TEMPLATE = "full"  # Optionen: "full", "simple", oder Dateiname wie "naming_convention_template.json"
    
    # Ordner mit IFC-Dateien zum Prüfen (oder einzelne Dateien)
    IFC_DIRECTORY = "tests/fixtures"  # Oder: ["tests/fixtures/sample.ifc", "tests/fixtures/sample2.ifc"]
    # =========================
    
    print("IFC Namenskonventions-Prüfung gestartet...")
    print_progress(0, "Initialisierung...")
    
    project_root = Path(__file__).parent.parent
    
    # Bestimme Template-Datei basierend auf TEMPLATE-Einstellung
    if TEMPLATE.lower() == "full":
        config_file = "naming_convention_template.json"
    elif TEMPLATE.lower() == "simple":
        config_file = "naming_convention_template_simple.json"
    else:
        # Direkter Dateiname oder Pfad
        config_file = TEMPLATE
    
    # Lade Konfiguration
    config_path = project_root / config_file
    if not config_path.exists():
        print(f"[FEHLER] Konfigurationsdatei nicht gefunden: {config_path}")
        print(f"  Verfügbare Templates:")
        print(f"    - naming_convention_template.json (vollständig mit allowed_values)")
        print(f"    - naming_convention_template_simple.json (einfach, nur Strukturprüfung)")
        print(f"  Setze TEMPLATE auf 'full', 'simple' oder einen Dateinamen")
        return
    
    print_progress(10, f"Konfiguration wird geladen ({config_file})...")
    try:
        config = load_naming_convention_config(config_path)
        print(f"[INFO] Template geladen: {config_file}")
        if config.get('allowed_values'):
            print(f"[INFO] Template enthält {len(config['allowed_values'])} erlaubte Wert-Definitionen")
        else:
            print(f"[INFO] Template enthält nur Strukturprüfung (keine allowed_values)")
    except Exception as e:
        print(f"[FEHLER] Fehler beim Laden der Konfiguration: {e}")
        return
    
    # Sammle Dateinamen
    print_progress(20, "Dateinamen werden gesammelt...")
    if isinstance(IFC_DIRECTORY, str):
        directory = project_root / IFC_DIRECTORY
        if directory.is_dir():
            ifc_files = list(directory.glob("*.ifc"))
            file_names = [f.name for f in ifc_files]
        else:
            # Einzelne Datei
            ifc_files = [directory]
            file_names = [directory.name]
    else:
        # Liste von Dateien
        ifc_files = [project_root / f for f in IFC_DIRECTORY]
        file_names = [Path(f).name for f in IFC_DIRECTORY]
    
    if not file_names:
        print("[FEHLER] Keine IFC-Dateien gefunden!")
        return
    
    print(f"Gefundene Dateien: {len(file_names)}")
    for name in file_names:
        print(f"  - {name}")
    
    # Erstelle Validator
    print_progress(40, "Validator wird konfiguriert...")
    validator = IFCValidator(rules=[])
    
    # Strukturprüfungsregel
    structure_rule = FileNameStructureRule(
        file_names=file_names,
        pattern=config['pattern'],
        segment_lengths=config['segment_lengths']
    )
    validator.add_rule(structure_rule)
    
    # Werteprüfungsregel (nur wenn allowed_values vorhanden und nicht leer)
    allowed_values = config.get('allowed_values', {})
    if allowed_values:
        print(f"[INFO] Werteprüfung wird aktiviert ({len(allowed_values)} Segmente mit erlaubten Werten)")
        value_rule = FileNameValueRule(
            file_names=file_names,
            pattern=config['pattern'],
            segment_lengths=config['segment_lengths'],
            allowed_values=allowed_values
        )
        validator.add_rule(value_rule)
    else:
        print(f"[INFO] Nur Strukturprüfung aktiviert (keine Werteprüfung)")
    
    # Validierung durchführen
    # Die Regeln prüfen nur Dateinamen, nicht IFC-Inhalt
    # Wir können ein Dummy-IFC-Objekt verwenden (wird ignoriert)
    print_progress(60, "Validierung läuft...")
    
    # Erstelle ein minimales Dummy-IFC-Objekt (wird von den Regeln ignoriert)
    # Oder rufe die Regeln direkt auf
    all_results = []
    
    # Rufe validate() auf den Regeln auf (mit Dummy-Objekt)
    # Die Regeln ignorieren das ifc_file und prüfen nur die konfigurierten Dateinamen
    try:
        # Versuche eine IFC-Datei zu laden als Dummy (falls vorhanden)
        dummy_ifc = None
        if ifc_files and ifc_files[0].exists():
            dummy_ifc = load_ifc_file(str(ifc_files[0]))
        else:
            # Erstelle ein minimales Dummy-Objekt
            import ifcopenshell
            dummy_ifc = ifcopenshell.file()
    except Exception:
        # Falls das nicht funktioniert, erstelle ein leeres Dummy
        import ifcopenshell
        dummy_ifc = ifcopenshell.file()
    
    # Validiere (Regeln ignorieren ifc_file, prüfen nur Dateinamen)
    report = validator.validate(dummy_ifc)
    all_results = report.results
    
    # Erstelle kombiniertes Report
    from src.validator.report import ValidationReport
    combined_report = ValidationReport(all_results, rule_names=[rule.name for rule in validator.rules])
    
    # Text-Report ausgeben
    if PRINT_TEXT_REPORT:
        print("\n" + "=" * 60)
        print("TEXT-REPORT")
        print("=" * 60)
        print(combined_report.get_report())
        print()
    
    # PDF-Report generieren
    download_folder = get_download_folder()
    pdf_file = download_folder / "naming_convention_report.pdf"
    pdf_generated = False
    if GENERATE_PDF:
        print_progress(90, "PDF-Report wird generiert...")
        try:
            combined_report.save_pdf_report(str(pdf_file))
            print(f"[OK] PDF-Report gespeichert: {pdf_file}")
            pdf_generated = pdf_file.exists()
        except ImportError as e:
            print(f"[WARNUNG] PDF-Export nicht verfügbar: {e}")
        except Exception as e:
            print(f"[WARNUNG] Fehler beim PDF-Export: {e}")
    
    # HTML-Report generieren
    if GENERATE_HTML:
        print_progress(95, "HTML-Report wird generiert...")
        html_file = download_folder / "naming_convention_report.html"
        
        pdf_path_for_html = str(pdf_file) if pdf_generated and pdf_file.exists() else None
        combined_report.save_html_report(str(html_file), pdf_file_path=pdf_path_for_html)
        
        print(f"\n[OK] HTML-Report gespeichert: {html_file}")
        
        try:
            webbrowser.open(f'file://{html_file.absolute()}')
            print(f"[OK] HTML-Report im Browser geöffnet")
        except Exception as e:
            print(f"[WARNUNG] Browser konnte nicht automatisch geöffnet werden: {e}")
    
    print_progress(100, "Abgeschlossen!")
    
    # Status prüfen
    print()
    if combined_report.is_valid():
        print("[OK] Validierung erfolgreich! Alle Dateinamen entsprechen der Konvention.")
    else:
        errors = combined_report.get_errors()
        warnings = combined_report.get_warnings()
        print(f"[FEHLER] {len(errors)} Fehler und {len(warnings)} Warnungen gefunden")


if __name__ == "__main__":
    main()

