"""Beispiel für die Prüfung von Geschosshöhen mit Mehrdateien-Vergleich."""

import sys
import webbrowser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import IFCValidator
from src.utils.ifc_loader import load_ifc_file, load_multiple_ifc_files
from src.utils.path_helpers import get_download_folder
from src.validator.rules import FloorHeightRule, MultiFileFloorComparisonRule


def print_progress(percentage: int, message: str = ""):
    """Gibt Fortschritt in Prozent aus."""
    bar_length = 20
    filled = int(bar_length * percentage / 100)
    # Verwende ASCII-Zeichen für bessere Kompatibilität
    bar = "#" * filled + "-" * (bar_length - filled)
    output = f"\r[{bar}] {percentage}% {message}"
    try:
        print(output, end="", flush=True)
    except UnicodeEncodeError:
        # Fallback für Systeme ohne UTF-8 Support
        output_ascii = output.encode('ascii', 'replace').decode('ascii')
        print(output_ascii, end="", flush=True)
    if percentage == 100:
        print()  # Neue Zeile bei 100%


def main():
    # ===== KONFIGURATION =====
    # Setze diese Variablen, um das Verhalten zu steuern:
    GENERATE_HTML = True      # True: HTML generieren, False: nur Text-Report
    GENERATE_PDF = True       # True: PDF generieren, False: nur HTML
    PRINT_TEXT_REPORT = True  # True: Text-Report auch ausgeben, False: nur HTML
    
    # Liste der IFC-Dateien zum Vergleichen
    # Erste Datei ist die Referenz für den Vergleich
    IFC_FILES = [
        "tests/fixtures/sample.ifc",  # Referenzdatei
        "tests/fixtures/sample2.ifc",# Füge hier weitere Dateien hinzu:
        "tests/fixtures/sample3.ifc"# "path/to/file2.ifc",
        # "path/to/file3.ifc",
    ]
    
    # Toleranz für Höhenvergleiche (in Metern)
    TOLERANCE = 0.01
    
    # Minimale Geschosshöhe (optional, None = keine Prüfung)
    MIN_FLOOR_HEIGHT = None  # z.B. 2.5 für 2.5m Minimum
    # =========================
    
    print("IFC Geschosshöhen-Prüfung gestartet...")
    print_progress(0, "Initialisierung...")
    
    project_root = Path(__file__).parent.parent
    
    if not IFC_FILES:
        print("[FEHLER] Keine IFC-Dateien angegeben!")
        return
    
    # Prüfe ob Dateien existieren
    file_paths = [project_root / f for f in IFC_FILES]
    missing_files = [f for f in file_paths if not f.exists()]
    if missing_files:
        print(f"[FEHLER] Folgende Dateien wurden nicht gefunden:")
        for f in missing_files:
            print(f"  - {f}")
        return
    
    if len(IFC_FILES) == 1:
        # Einzeldatei-Modus
        print_progress(25, "IFC-Datei wird geladen...")
        ifc_file = load_ifc_file(str(file_paths[0]))
        
        print_progress(50, "Validator wird konfiguriert...")
        validator = IFCValidator(rules=[])
        validator.add_rule(FloorHeightRule(tolerance=TOLERANCE, min_floor_height=MIN_FLOOR_HEIGHT))
        
        print_progress(75, "Validierung läuft...")
        report = validator.validate(ifc_file)
        
        print(f"\nDatei: {IFC_FILES[0]}")
        
    else:
        # Mehrdateien-Modus
        print_progress(25, "IFC-Dateien werden geladen...")
        ifc_files = load_multiple_ifc_files([str(f) for f in file_paths])
        file_names = [Path(f).name for f in IFC_FILES]
        
        print_progress(50, "Validator wird konfiguriert...")
        validator = IFCValidator(rules=[])
        
        # Einzelprüfungsregel
        floor_rule = FloorHeightRule(tolerance=TOLERANCE, min_floor_height=MIN_FLOOR_HEIGHT)
        validator.add_rule(floor_rule)
        
        # Lade Referenzdatei separat für Metadaten
        print_progress(60, "Referenzdatei wird analysiert...")
        reference_file = ifc_files[0]
        reference_report = validator.validate(reference_file)
        reference_metadata = floor_rule.get_metadata()
        
        if not reference_metadata:
            print("[FEHLER] Konnte Metadaten der Referenzdatei nicht extrahieren!")
            return
        
        print(f"\nReferenzdatei: {IFC_FILES[0]}")
        print(f"  Anzahl Geschosse: {reference_metadata['storey_count']}")
        print(f"  Gesamthöhe: {reference_metadata['total_height']:.2f}m")
        
        # Vergleichsregel erstellen
        comparison_rule = MultiFileFloorComparisonRule(
            reference_file_metadata=reference_metadata,
            tolerance=TOLERANCE
        )
        
        print_progress(75, "Validierung läuft...")
        report = validator.validate_multiple(
            ifc_files, 
            file_names=file_names,
            comparison_rules=[comparison_rule]
        )
        
        # Zeige Zusammenfassung für weitere Dateien
        for idx, file_name in enumerate(file_names[1:], start=1):
            # Extrahiere Metadaten für diese Datei
            temp_validator = IFCValidator(rules=[FloorHeightRule(tolerance=TOLERANCE)])
            temp_report = temp_validator.validate(ifc_files[idx])
            temp_metadata = temp_validator.rules[0].get_metadata()
            
            if temp_metadata:
                print(f"\nDatei {idx+1}: {file_name}")
                print(f"  Anzahl Geschosse: {temp_metadata['storey_count']}")
                print(f"  Gesamthöhe: {temp_metadata['total_height']:.2f}m")
    
    # Text-Report ausgeben (falls gewünscht)
    if PRINT_TEXT_REPORT:
        print("\n" + "=" * 60)
        print("TEXT-REPORT")
        print("=" * 60)
        print(report.get_report())
        print()
    
    # PDF-Report generieren (falls gewünscht) - VOR HTML, damit Button angezeigt wird
    download_folder = get_download_folder()
    pdf_file = download_folder / "floor_height_validation_report.pdf"
    pdf_generated = False
    if GENERATE_PDF:
        print_progress(90, "PDF-Report wird generiert...")
        try:
            report.save_pdf_report(str(pdf_file))
            print(f"[OK] PDF-Report gespeichert: {pdf_file}")
            pdf_generated = pdf_file.exists()
        except ImportError as e:
            print(f"[WARNUNG] PDF-Export nicht verfuegbar: {e}")
            print(f"  Installiere weasyprint mit: pip install weasyprint")
        except Exception as e:
            print(f"[WARNUNG] Fehler beim PDF-Export: {e}")
    
    # HTML-Report generieren und speichern
    if GENERATE_HTML:
        print_progress(95, "HTML-Report wird generiert...")
        html_file = download_folder / "floor_height_validation_report.html"
        
        # PDF-Pfad übergeben, wenn PDF erfolgreich generiert wurde
        pdf_path_for_html = str(pdf_file) if pdf_generated and pdf_file.exists() else None
        report.save_html_report(str(html_file), pdf_file_path=pdf_path_for_html)
        
        print(f"\n[OK] HTML-Report gespeichert: {html_file}")
        
        # HTML im Browser öffnen
        try:
            webbrowser.open(f'file://{html_file.absolute()}')
            print(f"[OK] HTML-Report im Browser geoeffnet")
        except Exception as e:
            print(f"[WARNUNG] Browser konnte nicht automatisch geoeffnet werden: {e}")
            print(f"  Oeffne manuell: {html_file}")
    
    print_progress(100, "Abgeschlossen!")
    
    # Status prüfen
    print()
    if report.is_valid():
        print("[OK] Validierung erfolgreich! Keine Probleme gefunden.")
    else:
        errors = report.get_errors()
        warnings = report.get_warnings()
        print(f"[FEHLER] {len(errors)} Fehler und {len(warnings)} Warnungen gefunden")


if __name__ == "__main__":
    main()

