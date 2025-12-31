from typing import List, Dict, Any, Optional
from collections import defaultdict
import re


class ValidationReport:
    """Klasse zur Verwaltung und Darstellung von Validierungsergebnissen."""
    
    def __init__(self, results: List[Dict[str, Any]], rule_names: List[str] = None):
        self.results = results
        self.rule_names = rule_names or []
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Gibt alle Fehler zurück."""
        return [r for r in self.results if r['severity'] == 'error']
    
    def get_warnings(self) -> List[Dict[str, Any]]:
        """Gibt alle Warnungen zurück."""
        return [r for r in self.results if r['severity'] == 'warning']
    
    def get_info(self) -> List[Dict[str, Any]]:
        """Gibt alle Info-Meldungen zurück."""
        return [r for r in self.results if r['severity'] == 'info']
    
    def is_valid(self) -> bool:
        """Gibt True zurück, wenn keine Fehler gefunden wurden."""
        return len(self.get_errors()) == 0
    
    def get_summary(self) -> Dict[str, int]:
        """Gibt eine Zusammenfassung zurück."""
        summary = defaultdict(int)
        for result in self.results:
            summary[result['severity']] += 1
        return dict(summary)
    
    def get_report(self, detailed: bool = True) -> str:
        """Gibt einen formatierten Bericht zurück."""
        lines = []
        lines.append("=" * 60)
        lines.append("IFC Validierungsbericht")
        lines.append("=" * 60)
        lines.append("")
        
        summary = self.get_summary()
        lines.append(f"Zusammenfassung:")
        lines.append(f"  Fehler: {summary.get('error', 0)}")
        lines.append(f"  Warnungen: {summary.get('warning', 0)}")
        lines.append(f"  Info: {summary.get('info', 0)}")
        lines.append(f"  Gesamt: {len(self.results)}")
        lines.append("")
        
        if detailed:
            lines.append("Details:")
            lines.append("-" * 60)
            for result in self.results:
                lines.append(f"[{result['severity'].upper()}] {result['rule']}")
                entity_str = str(result['entity']) if result['entity'] is not None else "N/A"
                lines.append(f"  Entity: {entity_str}")
                lines.append(f"  Message: {result['message']}")
                lines.append("")
        
        # Regel-Statistik am Ende
        if self.rule_names:
            lines.append("")
            lines.append("Regel-Statistik:")
            lines.append("-" * 60)
            
            # Zähle Fehler pro Regel
            rule_counts = defaultdict(lambda: {'error': 0, 'warning': 0, 'info': 0})
            for result in self.results:
                rule_name = result['rule']
                severity = result['severity']
                rule_counts[rule_name][severity] += 1
            
            # Zeige alle Regeln (auch die mit 0 Fehlern)
            for rule_name in self.rule_names:
                counts = rule_counts[rule_name]
                total = counts['error'] + counts['warning'] + counts['info']
                lines.append(f"  {rule_name}:")
                lines.append(f"    Fehler: {counts['error']}")
                lines.append(f"    Warnungen: {counts['warning']}")
                lines.append(f"    Info: {counts['info']}")
                lines.append(f"    Gesamt: {total}")
                lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def _extract_global_id(self, entity_str: Optional[str]) -> Optional[str]:
        """Extrahiert GlobalId aus Entity-String für Viewer-Integration."""
        if entity_str is None:
            return None
        # Suche nach GlobalId im Format: '2JPIbogtaSJ80doWX10qDb'
        match = re.search(r"'([A-Za-z0-9_$]+)'", str(entity_str))
        if match:
            return match.group(1)
        return None
    
    def get_html_report(self, pdf_file_path: Optional[str] = None) -> str:
        """
        Gibt HTML-Report als String zurück.
        
        Args:
            pdf_file_path: Optionaler Pfad zur PDF-Datei. Wenn angegeben, wird ein PDF-Button angezeigt.
        """
        summary = self.get_summary()
        
        # HTML-Header
        html = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IFC Validierungsbericht</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .summary {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .summary h2 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .summary-item {
            background: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .summary-item.error {
            border-left-color: #e74c3c;
        }
        .summary-item.warning {
            border-left-color: #f39c12;
        }
        .summary-item.info {
            border-left-color: #3498db;
        }
        .summary-item strong {
            display: block;
            font-size: 24px;
            color: #2c3e50;
        }
        .summary-item span {
            color: #7f8c8d;
            font-size: 14px;
        }
        .results {
            margin-top: 30px;
        }
        .result-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid;
            background: #fff;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .result-item:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .result-item.error {
            border-left-color: #e74c3c;
            background: #fee;
        }
        .result-item.warning {
            border-left-color: #f39c12;
            background: #fff8e1;
        }
        .result-item.info {
            border-left-color: #3498db;
            background: #e3f2fd;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .result-severity {
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            text-transform: uppercase;
        }
        .result-severity.error {
            background: #e74c3c;
            color: white;
        }
        .result-severity.warning {
            background: #f39c12;
            color: white;
        }
        .result-severity.info {
            background: #3498db;
            color: white;
        }
        .result-rule {
            font-weight: bold;
            color: #2c3e50;
        }
        .result-entity {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #7f8c8d;
            margin: 5px 0;
            word-break: break-all;
        }
        .result-message {
            color: #555;
            margin-top: 5px;
        }
        .rule-statistics {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
        }
        .rule-statistics h2 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .rule-item {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .rule-item h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .rule-counts {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .rule-count {
            padding: 5px 10px;
            background: white;
            border-radius: 3px;
            font-size: 14px;
        }
        .rule-count strong {
            color: #2c3e50;
        }
        .status {
            text-align: center;
            padding: 20px;
            margin-top: 30px;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
        }
        .status.valid {
            background: #d4edda;
            color: #155724;
            border: 2px solid #c3e6cb;
        }
        .status.invalid {
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #f5c6cb;
        }
        .filters {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }
        .filter-group {
            display: flex;
            gap: 5px;
        }
        .filter-btn {
            padding: 8px 15px;
            border: 2px solid #3498db;
            background: white;
            color: #3498db;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .filter-btn:hover {
            background: #3498db;
            color: white;
        }
        .filter-btn.active {
            background: #3498db;
            color: white;
        }
        .filter-btn.error.active {
            background: #e74c3c;
            border-color: #e74c3c;
        }
        .filter-btn.warning.active {
            background: #f39c12;
            border-color: #f39c12;
        }
        .filter-btn.info.active {
            background: #3498db;
            border-color: #3498db;
        }
        .search-box {
            flex: 1;
            min-width: 200px;
            padding: 8px 15px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .rule-group {
            margin-bottom: 20px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            overflow: hidden;
        }
        .rule-group-header {
            background: #f8f9fa;
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }
        .rule-group-header:hover {
            background: #e9ecef;
        }
        .rule-group-header h3 {
            margin: 0;
            color: #2c3e50;
            font-size: 18px;
        }
        .rule-group-counts {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .rule-group-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .rule-group-badge.error {
            background: #e74c3c;
            color: white;
        }
        .rule-group-badge.warning {
            background: #f39c12;
            color: white;
        }
        .rule-group-badge.info {
            background: #3498db;
            color: white;
        }
        .rule-group-toggle {
            font-size: 20px;
            color: #7f8c8d;
            transition: transform 0.3s;
        }
        .rule-group-content {
            display: none;
            padding: 0;
        }
        .rule-group-content.expanded {
            display: block;
        }
        .rule-group-results {
            padding: 10px 20px 20px 20px;
        }
        .rule-group.hidden {
            display: none;
        }
    </style>
    <script>
        function toggleRuleGroup(ruleName) {
            const content = document.getElementById('rule-content-' + ruleName.replace(/[^a-zA-Z0-9]/g, '-'));
            const toggle = document.getElementById('rule-toggle-' + ruleName.replace(/[^a-zA-Z0-9]/g, '-'));
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                toggle.textContent = '▶';
            } else {
                content.classList.add('expanded');
                toggle.textContent = '▼';
            }
        }
        
        function filterBySeverity(severity) {
            const btn = event.target;
            btn.classList.toggle('active');
            
            const allItems = document.querySelectorAll('.result-item');
            const activeFilters = Array.from(document.querySelectorAll('.filter-btn.active')).map(b => b.dataset.severity);
            
            allItems.forEach(item => {
                if (activeFilters.length === 0 || activeFilters.includes(item.classList[1])) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Update rule groups visibility
            updateRuleGroupsVisibility();
        }
        
        function searchRules() {
            const searchTerm = document.getElementById('rule-search').value.toLowerCase();
            const ruleGroups = document.querySelectorAll('.rule-group');
            
            ruleGroups.forEach(group => {
                const ruleName = group.querySelector('h3').textContent.toLowerCase();
                if (ruleName.includes(searchTerm)) {
                    group.classList.remove('hidden');
                } else {
                    group.classList.add('hidden');
                }
            });
        }
        
        function updateRuleGroupsVisibility() {
            const ruleGroups = document.querySelectorAll('.rule-group');
            ruleGroups.forEach(group => {
                const visibleItems = group.querySelectorAll('.result-item[style="display: block;"], .result-item:not([style*="display: none"])');
                if (visibleItems.length === 0 && group.querySelectorAll('.result-item').length > 0) {
                    group.style.display = 'none';
                } else {
                    group.style.display = 'block';
                }
            });
        }
        
        // Expand all rule groups on load
        window.addEventListener('load', function() {
            document.querySelectorAll('.rule-group-content').forEach(content => {
                content.classList.add('expanded');
                const ruleName = content.id.replace('rule-content-', '').replace(/-/g, ' ');
                const toggle = document.getElementById('rule-toggle-' + content.id.replace('rule-content-', ''));
                if (toggle) toggle.textContent = '▼';
            });
        });
    </script>
</head>
<body>
    <div class="container">
"""
        
        # PDF-Button nur anzeigen, wenn PDF generiert wurde
        if pdf_file_path:
            from pathlib import Path
            pdf_path = Path(pdf_file_path)
            pdf_url = f'file://{pdf_path.absolute()}'
            html += f"""        <div style="text-align: right; margin-bottom: 15px;">
            <a href="{pdf_url}" target="_blank" style="display: inline-block; padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold; text-decoration: none;">
                📄 PDF öffnen
            </a>
        </div>
"""
        
        html += """        <h1>IFC Validierungsbericht</h1>
        
        <div class="summary">
            <h2>Zusammenfassung</h2>
            <div class="summary-grid">
                <div class="summary-item error">
                    <strong>""" + str(summary.get('error', 0)) + """</strong>
                    <span>Fehler</span>
                </div>
                <div class="summary-item warning">
                    <strong>""" + str(summary.get('warning', 0)) + """</strong>
                    <span>Warnungen</span>
                </div>
                <div class="summary-item info">
                    <strong>""" + str(summary.get('info', 0)) + """</strong>
                    <span>Info</span>
                </div>
                <div class="summary-item">
                    <strong>""" + str(len(self.results)) + """</strong>
                    <span>Gesamt</span>
                </div>
            </div>
        </div>
"""
        
        # Ergebnisse nach Regeln gruppieren
        if self.results:
            html += """        <div class="results">
            <h2>Details nach Prüfungen</h2>
            
            <div class="filters">
                <div class="filter-group">
                    <button class="filter-btn error active" data-severity="error" onclick="filterBySeverity('error')">Fehler</button>
                    <button class="filter-btn warning active" data-severity="warning" onclick="filterBySeverity('warning')">Warnungen</button>
                    <button class="filter-btn info active" data-severity="info" onclick="filterBySeverity('info')">Info</button>
                </div>
                <input type="text" id="rule-search" class="search-box" placeholder="Suche nach Prüfung..." onkeyup="searchRules()">
            </div>
"""
            
            # Gruppiere Ergebnisse nach Regeln
            from collections import defaultdict
            rule_results = defaultdict(list)
            for result in self.results:
                rule_results[result['rule']].append(result)
            
            # Erstelle Sektion für jede Regel
            for rule_name in sorted(rule_results.keys()):
                results_for_rule = rule_results[rule_name]
                
                # Zähle Severities für diese Regel
                rule_severity_counts = defaultdict(int)
                for result in results_for_rule:
                    rule_severity_counts[result['severity']] += 1
                
                rule_id = rule_name.replace(' ', '-').replace('/', '-').replace('\\', '-')
                rule_id_safe = ''.join(c if c.isalnum() or c == '-' else '-' for c in rule_id)
                
                html += f"""            <div class="rule-group" id="rule-{rule_id_safe}">
                <div class="rule-group-header" onclick="toggleRuleGroup('{rule_id_safe}')">
                    <h3>{self._escape_html(rule_name)}</h3>
                    <div class="rule-group-counts">
"""
                
                # Badges für Severities
                if rule_severity_counts['error'] > 0:
                    html += f"""                        <span class="rule-group-badge error">{rule_severity_counts['error']} Fehler</span>
"""
                if rule_severity_counts['warning'] > 0:
                    html += f"""                        <span class="rule-group-badge warning">{rule_severity_counts['warning']} Warnungen</span>
"""
                if rule_severity_counts['info'] > 0:
                    html += f"""                        <span class="rule-group-badge info">{rule_severity_counts['info']} Info</span>
"""
                
                total = len(results_for_rule)
                html += f"""                        <span style="color: #7f8c8d; font-size: 14px;">({total} gesamt)</span>
                        <span class="rule-group-toggle" id="rule-toggle-{rule_id_safe}">▼</span>
                    </div>
                </div>
                <div class="rule-group-content expanded" id="rule-content-{rule_id_safe}">
                    <div class="rule-group-results">
"""
                
                # Zeige alle Ergebnisse dieser Regel
                for result in results_for_rule:
                    global_id = self._extract_global_id(result['entity'])
                    global_id_attr = f' data-global-id="{global_id}"' if global_id else ''
                    
                    html += f"""                        <div class="result-item {result['severity']}"{global_id_attr}>
                            <div class="result-header">
                                <span class="result-severity {result['severity']}">{result['severity'].upper()}</span>
                            </div>
                            <div class="result-entity">{self._escape_html(result['entity'])}</div>
                            <div class="result-message">{self._escape_html(result['message'])}</div>
                        </div>
"""
                
                html += """                    </div>
                </div>
            </div>
"""
            
            html += "        </div>\n"
        
        # Regel-Statistik
        if self.rule_names:
            html += """        <div class="rule-statistics">
            <h2>Regel-Statistik</h2>
"""
            rule_counts = defaultdict(lambda: {'error': 0, 'warning': 0, 'info': 0})
            for result in self.results:
                rule_name = result['rule']
                severity = result['severity']
                rule_counts[rule_name][severity] += 1
            
            for rule_name in self.rule_names:
                counts = rule_counts[rule_name]
                total = counts['error'] + counts['warning'] + counts['info']
                html += f"""            <div class="rule-item">
                <h3>{self._escape_html(rule_name)}</h3>
                <div class="rule-counts">
                    <div class="rule-count"><strong>Fehler:</strong> {counts['error']}</div>
                    <div class="rule-count"><strong>Warnungen:</strong> {counts['warning']}</div>
                    <div class="rule-count"><strong>Info:</strong> {counts['info']}</div>
                    <div class="rule-count"><strong>Gesamt:</strong> {total}</div>
                </div>
            </div>
"""
            html += "        </div>\n"
        
        # Status
        status_class = "valid" if self.is_valid() else "invalid"
        status_text = "✓ Validierung erfolgreich!" if self.is_valid() else f"✗ {len(self.get_errors())} Fehler gefunden"
        html += f"""        <div class="status {status_class}">
            {status_text}
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _escape_html(self, text: Optional[str]) -> str:
        """Escaped HTML-Sonderzeichen."""
        if text is None:
            return "N/A"
        if not isinstance(text, str):
            text = str(text)
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
    
    def save_html_report(self, file_path: str, pdf_file_path: Optional[str] = None) -> None:
        """
        Speichert HTML-Report in Datei.
        
        Args:
            file_path: Pfad zur HTML-Datei
            pdf_file_path: Optionaler Pfad zur PDF-Datei. Wenn angegeben, wird ein PDF-Button im HTML angezeigt.
        """
        html = self.get_html_report(pdf_file_path=pdf_file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def get_html_for_pdf(self) -> str:
        """Gibt HTML-Report für PDF-Export zurück (verwendet HTML-Report direkt)."""
        # HTML-Report verwenden (ohne PDF-Button)
        # Playwright unterstützt alle modernen CSS-Features, daher können wir
        # das HTML 1:1 übernehmen
        html = self.get_html_report(pdf_file_path=None)
        
        # PDF-spezifische CSS-Anpassungen hinzufügen (@page rules)
        import re
        html = re.sub(
            r'(</style>)',
            r'''        @page {
            size: A4;
            margin: 2cm;
        }
        @media print {
            .filters {
                display: none;
            }
            .rule-group-content {
                display: block !important;
            }
        }
    \1''',
            html,
            count=1
        )
        
        return html
    
    def save_pdf_report(self, file_path: str) -> None:
        """Speichert PDF-Report in Datei mit Playwright."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "playwright ist nicht installiert. Installiere es mit: pip install playwright\n"
                "Danach führe aus: playwright install chromium"
            )
        
        html_content = self.get_html_for_pdf()
        
        # Temporäre HTML-Datei erstellen (Playwright benötigt eine Datei oder URL)
        import tempfile
        import os
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(html_content)
            tmp_html_path = tmp_file.name
        
        try:
            with sync_playwright() as p:
                # Chromium-Browser starten
                browser = p.chromium.launch()
                page = browser.new_page()
                
                # HTML-Datei laden
                file_url = f"file://{Path(tmp_html_path).absolute()}"
                page.goto(file_url)
                
                # PDF generieren
                page.pdf(
                    path=file_path,
                    format='A4',
                    margin={
                        'top': '2cm',
                        'right': '2cm',
                        'bottom': '2cm',
                        'left': '2cm'
                    },
                    print_background=True
                )
                
                browser.close()
        finally:
            # Temporäre Datei löschen
            try:
                os.unlink(tmp_html_path)
            except:
                pass

