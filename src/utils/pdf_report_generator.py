"""Direkte PDF-Generierung aus ReportData ohne Quarto."""

import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def generate_pdf_from_report_data(
    report_data_path: Path,
    output_pdf_path: Path,
    logo_paths: Optional[Dict[str, Optional[Path]]] = None
) -> None:
    """
    Generiert direkt ein PDF aus report_data.json mit Playwright.
    
    Args:
        report_data_path: Pfad zur report_data.json
        output_pdf_path: Pfad für das Output-PDF
        logo_paths: Optional - Dict mit 'customer', 'project', 'company' Logo-Pfaden
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "playwright ist nicht installiert. Installiere es mit: pip install playwright\n"
            "Danach führe aus: playwright install chromium"
        )
    
    # Lade ReportData
    with open(report_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Generiere HTML
    html_content = generate_html_from_data(data, logo_paths or {})
    
    # Rendere PDF mit Playwright
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp_file:
        tmp_file.write(html_content)
        tmp_html_path = tmp_file.name
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            file_url = f"file://{Path(tmp_html_path).absolute()}"
            page.goto(file_url)
            
            # Warte auf vollständiges Laden
            page.wait_for_load_state('networkidle')
            
            # PDF generieren
            page.pdf(
                path=str(output_pdf_path),
                format='A4',
                margin={
                    'top': '0.5cm',
                    'right': '2cm',
                    'bottom': '0.5cm',
                    'left': '2cm'
                },
                print_background=True
            )
            
            browser.close()
    finally:
        try:
            os.unlink(tmp_html_path)
        except:
            pass


def generate_html_from_data(data: Dict[str, Any], logo_paths: Dict[str, Optional[Path]]) -> str:
    """Generiert HTML aus ReportData."""
    
    metadata = data.get('metadata', {})
    customer = data.get('customer', {})
    project = data.get('project', {})
    author = data.get('author', {})
    models = data.get('models', [])
    checks = data.get('checks', [])
    language = data.get('language', 'de')
    
    # Übersetzungen
    translations = {
        'de': {
            'dashboard': 'Übersicht',
            'details': 'Detailprüfungen',
            'customer': 'Kunde',
            'project': 'Projekt',
            'generated_at': 'Erstellt am',
            'report_id': 'Bericht-ID',
            'models_checked': 'Geprüfte Modelle',
            'check': 'Prüfung',
            'status': 'Status',
            'findings': 'Befunde',
            'pass': 'OK',
            'warn': 'Warnung',
            'fail': 'Fehler',
            'total': 'Gesamt',
            'severity': 'Schweregrad',
            'message': 'Meldung',
            'ifc_type': 'IFC-Typ',
            'storey': 'Geschoss',
            'building': 'Gebäude',
            'no_findings': 'Keine Befunde',
            'summary': 'Zusammenfassung',
            'info': 'Information'
        },
        'en': {
            'dashboard': 'Overview',
            'details': 'Detailed Checks',
            'customer': 'Customer',
            'project': 'Project',
            'generated_at': 'Generated at',
            'report_id': 'Report ID',
            'models_checked': 'Models Checked',
            'check': 'Check',
            'status': 'Status',
            'findings': 'Findings',
            'pass': 'OK',
            'warn': 'Warning',
            'fail': 'Error',
            'total': 'Total',
            'severity': 'Severity',
            'message': 'Message',
            'ifc_type': 'IFC Type',
            'storey': 'Storey',
            'building': 'Building',
            'no_findings': 'No findings',
            'summary': 'Summary'
        },
        'fr': {
            'dashboard': 'Vue d\'ensemble',
            'details': 'Vérifications détaillées',
            'customer': 'Client',
            'project': 'Projet',
            'generated_at': 'Généré le',
            'report_id': 'ID du rapport',
            'models_checked': 'Modèles vérifiés',
            'check': 'Vérification',
            'status': 'Statut',
            'findings': 'Résultats',
            'pass': 'OK',
            'warn': 'Avertissement',
            'fail': 'Erreur',
            'total': 'Total',
            'severity': 'Gravité',
            'message': 'Message',
            'ifc_type': 'Type IFC',
            'storey': 'Niveau',
            'building': 'Bâtiment',
            'no_findings': 'Aucun résultat',
            'summary': 'Résumé',
            'info': 'Information'
        }
    }
    
    t = translations.get(language, translations['de'])
    
    # Funktion zum Extrahieren der Farbe aus SVG
    def extract_color_from_svg(svg_content: str) -> Optional[str]:
        """Extrahiert die erste gefundene Farbe (fill oder stroke) aus SVG."""
        import re
        # Suche nach fill="#..." oder fill='...' oder stroke="#..." oder stroke='...'
        patterns = [
            r'fill=["\']([^"\']+)["\']',
            r'stroke=["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, svg_content)
            for match in matches:
                # Ignoriere 'none', 'transparent', etc.
                if match and match.lower() not in ['none', 'transparent', 'currentcolor']:
                    # Wenn es ein Hex-Code ist, gib ihn zurück
                    if match.startswith('#'):
                        return match
                    # Wenn es ein RGB/RGBA ist, konvertiere zu Hex (vereinfacht)
                    # Für jetzt nehmen wir nur Hex-Codes
        return None
    
    # Logo-Helper - alle Logos als Base64 data URI (auch SVG)
    def get_logo_base64(logo_path: Optional[Path]) -> tuple[str, Optional[str]]:
        """
        Konvertiert Logo zu Base64 data URI (unterstützt PNG, JPEG, SVG).
        Returns: (base64_data_uri, extracted_color)
        """
        if not logo_path:
            return "", None
        
        if not logo_path.exists():
            print(f"⚠ Logo nicht gefunden: {logo_path}")
            return "", None
        
        try:
            ext = logo_path.suffix.lower()
            extracted_color = None
            
            # SVG als Base64 data URI (einfacher für Skalierung)
            if ext == '.svg':
                with open(logo_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                # Extrahiere Farbe aus SVG
                extracted_color = extract_color_from_svg(svg_content)
                if extracted_color:
                    print(f"✓ Farbe aus SVG extrahiert: {extracted_color}")
                # SVG als Base64 kodieren
                svg_bytes = svg_content.encode('utf-8')
                base64_str = base64.b64encode(svg_bytes).decode('utf-8')
                print(f"✓ SVG-Logo geladen: {logo_path.name} (als Base64)")
                return f"data:image/svg+xml;base64,{base64_str}", extracted_color
            
            # Raster-Formate (PNG, JPEG) als Base64
            with open(logo_path, 'rb') as f:
                img_data = f.read()
            base64_str = base64.b64encode(img_data).decode('utf-8')
            
            if ext == '.png':
                mime_type = 'image/png'
            elif ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            else:
                mime_type = 'image/png'
            
            print(f"✓ Logo geladen: {logo_path.name} ({len(base64_str)} Zeichen Base64)")
            return f"data:{mime_type};base64,{base64_str}", None
        except Exception as e:
            print(f"✗ Fehler beim Laden des Logos {logo_path}: {e}")
            import traceback
            traceback.print_exc()
            return "", None
    
    # Alle Logos als img-Tags (einheitliche Skalierung)
    customer_logo_data, _ = get_logo_base64(logo_paths.get('customer'))
    project_logo_data, _ = get_logo_base64(logo_paths.get('project'))
    company_logo_data, company_logo_color = get_logo_base64(logo_paths.get('company'))
    
    def format_logo_html(logo_data: str, alt: str, css_class: str = "logo") -> str:
        """Formatiert Logo als img-Tag."""
        if not logo_data:
            return ""
        return f'<img src="{logo_data}" class="{css_class}" alt="{alt}">'
    
    customer_logo = format_logo_html(customer_logo_data, "Kunde", "logo-header")
    project_logo = format_logo_html(project_logo_data, "Projekt", "project-logo-corner")
    company_logo = format_logo_html(company_logo_data, "Firma", "logo-footer")
    
    # Branding-Farben
    brand = author.get('brand', {})
    # Verwende Farbe aus Company-Logo, falls vorhanden, sonst aus Branding, sonst Standard
    primary_color = company_logo_color or brand.get('primary_color', '#0066CC')
    secondary_color = brand.get('secondary_color', '#333333')
    
    if company_logo_color:
        print(f"✓ Primärfarbe aus Company-Logo übernommen: {primary_color}")
    
    def format_datetime(dt_str: str) -> str:
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return dt_str
    
    def get_status_symbol(status: str) -> str:
        if status == 'pass':
            return '✓'
        elif status == 'warn':
            return '⚠'
        elif status == 'fail':
            return '✗'
        return '?'
    
    def get_status_color(status: str) -> str:
        if status == 'pass':
            return '#28a745'
        elif status == 'warn':
            return '#ffc107'
        elif status == 'fail':
            return '#dc3545'
        return '#6c757d'
    
    # HTML generieren
    html = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IFC Validierungsbericht</title>
    <style>
        @page {{
            size: A4;
            margin: 0.5cm 2cm;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: white;
            padding-bottom: 3cm;
            counter-reset: page-counter 0;
        }}
        .page-break {{
            page-break-before: always;
            counter-increment: page-counter;
        }}
        .header {{
            display: flex;
            justify-content: flex-start;
            align-items: center;
            margin: -0.5cm -2cm 1.5cm -2cm;
            padding: 0.5cm 2cm 1cm 2cm;
            position: relative;
        }}
        .page-header {{
            position: fixed;
            top: -0.5cm;
            left: -2cm;
            right: -2cm;
            padding: 0.3cm 2cm;
            background: white;
            display: none;
            justify-content: space-between;
            align-items: center;
            font-size: 9pt;
            color: {secondary_color};
            z-index: 1000;
        }}
        /* Zeige Header nach dem ersten page-break */
        .page-break ~ .page-header {{
            display: flex;
        }}
        .page-header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }}
        .page-header-project-id {{
            font-weight: bold;
        }}
        .page-header-page-number {{
            font-weight: normal;
        }}
        .page-header-page-number::after {{
            content: counter(page-counter);
        }}
        .logo {{
            width: 150px;
            height: 60px;
            object-fit: contain;
            display: block;
        }}
        .logo-header {{
            width: 150px;
            height: 60px;
            object-fit: contain;
            display: block;
        }}
        .logo-footer {{
            width: 120px;
            height: 40px;
            object-fit: contain;
            display: block;
        }}
        .project-logo-corner {{
            position: absolute;
            top: 0.5cm;
            right: 2cm;
            width: 120px;
            height: 50px;
            object-fit: contain;
        }}
        .footer {{
            position: fixed;
            bottom: -0.5cm;
            left: -2cm;
            right: -2cm;
            padding: 0.5cm 2cm;
            background: white;
            display: flex;
            justify-content: flex-end;
            align-items: center;
        }}
        .title-section {{
            text-align: center;
            margin-bottom: 1.5cm;
        }}
        .title-section h1 {{
            font-size: 24pt;
            color: {primary_color};
            margin-bottom: 0.5cm;
        }}
        .metadata {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1cm;
            margin-bottom: 1.5cm;
            font-size: 10pt;
        }}
        .metadata-item {{
            display: flex;
            justify-content: flex-start;
            align-items: baseline;
        }}
        .metadata-label {{
            font-weight: bold;
            color: {secondary_color};
            margin-right: 0.5cm;
        }}
        .dashboard-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5cm;
            font-size: 10pt;
        }}
        .dashboard-table th,
        .dashboard-table td {{
            padding: 10px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        .dashboard-table th {{
            background-color: {primary_color};
            color: white;
            font-weight: bold;
        }}
        .dashboard-table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 9pt;
        }}
        .status-pass {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-warn {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .status-fail {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .check-section {{
            margin-bottom: 2cm;
        }}
        .check-header {{
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid {primary_color};
            margin-bottom: 1cm;
        }}
        .check-header h2 {{
            color: {primary_color};
            font-size: 18pt;
            margin-bottom: 5px;
        }}
        .check-summary {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 1cm;
            font-size: 10pt;
        }}
        .check-summary-item {{
            display: inline-block;
            margin-right: 20px;
        }}
        .findings-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1cm;
            font-size: 9pt;
        }}
        .findings-table th,
        .findings-table td {{
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        .findings-table th {{
            background-color: {secondary_color};
            color: white;
            font-weight: bold;
        }}
        .findings-table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .severity-error {{
            color: #dc3545;
            font-weight: bold;
        }}
        .severity-warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        .severity-info {{
            color: #17a2b8;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <!-- Header mit Customer Logo links, Project Logo rechts oben (nur erste Seite) -->
    <div class="header">
        {customer_logo}
        {project_logo}
    </div>
    
    <!-- Header für ab Seite 2 (Projekt-ID und Seitenzahl) - wird nach dem ersten page-break sichtbar -->
    <div class="page-header">
        <div class="page-header-content">
            <span class="page-header-project-id">{project.get('project_id', 'N/A')}</span>
            <span class="page-header-page-number"></span>
        </div>
    </div>
    
    <!-- Titel -->
    <div class="title-section">
        <h1>IFC Validierungsbericht</h1>
    </div>
    
    <!-- Metadaten -->
    <div class="metadata">
        <div class="metadata-item">
            <span class="metadata-label">{t['customer']}:</span>
            <span>{customer.get('name', 'N/A')}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">{t['project']}:</span>
            <span>{project.get('name', 'N/A')}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">{t['generated_at']}:</span>
            <span>{format_datetime(metadata.get('generated_at', ''))}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">{t['report_id']}:</span>
            <span>{metadata.get('report_id', 'N/A')}</span>
        </div>
    </div>
    
    <!-- Dashboard-Tabelle -->
    <h2>{t['dashboard']}</h2>
    <table class="dashboard-table">
        <thead>
            <tr>
                <th>{t['check']}</th>
                <th>{t['status']}</th>
                <th>{t['warn']}</th>
                <th>{t['fail']}</th>
                <th>{t['info']}</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for check in checks:
        status = check.get('status', 'unknown')
        status_class = f'status-{status}'
        status_symbol = get_status_symbol(status)
        summary = check.get('summary', {})
        warn_count = summary.get('warn', 0)
        fail_count = summary.get('fail', 0)
        info_count = summary.get('info', 0)
        
        html += f"""
            <tr>
                <td>{check.get('title', '')}</td>
                <td><span class="status-badge {status_class}">{status_symbol} {status.upper()}</span></td>
                <td>{warn_count}</td>
                <td>{fail_count}</td>
                <td>{info_count}</td>
            </tr>
"""
    
    html += """
        </tbody>
    </table>
    
    <div class="page-break"></div>
"""
    
    # Detailprüfungen
    html += f"<h2>{t['details']}</h2>\n"
    
    for check in checks:
        status = check.get('status', 'unknown')
        status_color = get_status_color(status)
        summary = check.get('summary', {})
        findings = check.get('findings', [])
        scoped_models = check.get('scoped_models', [])
        
        html += f"""
    <div class="check-section">
        <div class="check-header">
            <h2>{check.get('title', '')}</h2>
            <p>{check.get('description', '')}</p>
        </div>
        
        <div class="check-summary">
            <div class="check-summary-item">
                <strong>{t['status']}:</strong> 
                <span style="color: {status_color};">{get_status_symbol(status)} {status.upper()}</span>
            </div>
            <div class="check-summary-item">
                <strong>{t['summary']}:</strong> 
                {t['pass']}: {summary.get('pass', 0)}, 
                {t['warn']}: {summary.get('warn', 0)}, 
                {t['fail']}: {summary.get('fail', 0)}, 
                {t['info']}: {summary.get('info', 0)}
            </div>
        </div>
        
        <p><strong>{t['models_checked']}:</strong> {', '.join(scoped_models) if scoped_models else 'N/A'}</p>
"""
        
        if findings:
            html += f"""
        <table class="findings-table">
            <thead>
                <tr>
                    <th>{t['severity']}</th>
                    <th>{t['message']}</th>
                    <th>{t['ifc_type']}</th>
                    <th>{t['storey']}</th>
                    <th>{t['building']}</th>
                </tr>
            </thead>
            <tbody>
"""
            for finding in findings:
                severity = finding.get('severity', '').lower()
                severity_class = f'severity-{severity}'
                html += f"""
                <tr>
                    <td class="{severity_class}">{finding.get('severity', '').upper()}</td>
                    <td>{finding.get('message', '')}</td>
                    <td>{finding.get('ifc_type', '-')}</td>
                    <td>{finding.get('storey', '-')}</td>
                    <td>{finding.get('building', '-')}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""
        else:
            html += f"<p style='font-style: italic;'>{t['no_findings']}</p>\n"
        
        html += """
    </div>
    <div class="page-break"></div>
"""
    
    company_name = author.get('name', '')
    
    html += f"""
    <!-- Footer mit Company Logo und Name -->
    <div class="footer">
        {company_logo if company_logo else ''}
        {f'<span class="footer-company-name">{company_name}</span>' if company_name else ''}
    </div>
</body>
</html>
"""
    
    return html
