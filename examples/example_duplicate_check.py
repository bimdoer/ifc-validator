"""Beispiel für die Verwendung der DuplicateRule zur Prüfung auf Duplikate."""

import sys
import webbrowser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import IFCValidator
from src.utils.ifc_loader import load_ifc_file
from src.utils.path_helpers import get_download_folder
from src.validator.rules import DuplicateRule


def print_progress(percentage: int, message: str = ""):
    """Gibt Fortschritt in Prozent aus."""
    import sys
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
    
    # =========================
    
    print("IFC Duplikatsprüfung gestartet...")
    print_progress(0, "Initialisierung...")
    
    project_root = Path(__file__).parent.parent
    
    # IFC-Datei laden - Pfad relativ zum Projekt-Root
    print_progress(25, "IFC-Datei wird geladen...")
    ifc_file = load_ifc_file(str(project_root / "tests" / "fixtures" / "sample.ifc"))
    
    # Validator OHNE Standard-Regeln erstellen (leere Liste)
    print_progress(50, "Validator wird konfiguriert...")
    validator = IFCValidator(rules=[])
    
    # Duplikatsprüfungen hinzufügen
    # Prüfe auf doppelte GlobalIds
    duplicate_globalid = DuplicateRule(field_name="GlobalId")
    validator.add_rule(duplicate_globalid)
    
    # Prüfe auf doppelte Names (falls vorhanden)
    duplicate_name = DuplicateRule(field_name="Name")
    validator.add_rule(duplicate_name)
    
    # Validierung durchführen
    print_progress(75, "Validierung läuft...")
    report = validator.validate(ifc_file)
    
    # Text-Report ausgeben (falls gewünscht)
    if PRINT_TEXT_REPORT:
        print("\n" + "=" * 60)
        print("TEXT-REPORT")
        print("=" * 60)
        print(report.get_report())
        print()
    
    # PDF-Report generieren (falls gewünscht) - VOR HTML, damit Button angezeigt wird
    download_folder = get_download_folder()
    pdf_file = download_folder / "validation_report.pdf"
    pdf_generated = False
    if GENERATE_PDF:
        print_progress(90, "PDF-Report wird generiert...")
        try:
            report.save_pdf_report(str(pdf_file))
            print(f"[OK] PDF-Report gespeichert: {pdf_file}")
            pdf_generated = pdf_file.exists()
        except ImportError as e:
            print(f"[WARNUNG] PDF-Export nicht verfuegbar: {e}")
            print(f"  Installiere playwright mit: pip install playwright")
            print(f"  Danach führe aus: playwright install chromium")
        except Exception as e:
            print(f"[WARNUNG] Fehler beim PDF-Export: {e}")
    
    # HTML-Report generieren und speichern
    if GENERATE_HTML:
        print_progress(95, "HTML-Report wird generiert...")
        html_file = download_folder / "validation_report.html"
        
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
        print("[OK] Validierung erfolgreich! Keine Duplikate gefunden.")
    else:
        print(f"[FEHLER] {len(report.get_errors())} Duplikate gefunden")


if __name__ == "__main__":
    main()
