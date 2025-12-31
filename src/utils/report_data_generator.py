"""Generator für ReportData-JSON aus ValidationReport."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

from ..validator.report import ValidationReport
from .report_config import ReportConfig
from .path_helpers import get_download_folder


class ReportDataGenerator:
    """Generiert ReportData-JSON aus ValidationReport und ReportConfig."""
    
    def __init__(self, report: ValidationReport, config: ReportConfig):
        """
        Args:
            report: ValidationReport mit Prüfergebnissen
            config: ReportConfig mit Metadaten und Branding
        """
        self.report = report
        self.config = config
    
    def generate_report_id(self) -> str:
        """
        Generiert Report-ID im Format: {projekt_id}_{YYYYMMDD-HHMM}_quality-report
        
        Returns:
            Report-ID String
        """
        project_id = self.config.get_project_id() or "UNKNOWN"
        now = datetime.now()
        date_time_str = now.strftime("%Y%m%d-%H%M")
        return f"{project_id}_{date_time_str}_quality-report"
    
    def generate(self) -> Dict[str, Any]:
        """
        Generiert ReportData-Dictionary.
        
        Returns:
            Dictionary im ReportData-Schema
        """
        # Metadaten
        report_id = self.config.get_output_config().get('report_id')
        if not report_id:
            report_id = self.generate_report_id()
        
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'validator_version': '0.1.0',  # TODO: Aus __version__ lesen
            'report_id': report_id
        }
        
        # Branding
        company_brand = self.config.get_company_brand()
        customer_project = self.config.get_customer_project()
        
        # Modelle
        models = self._extract_models()
        
        # Checks/Regeln
        checks = self._generate_checks()
        
        return {
            'metadata': metadata,
            'customer': customer_project.get('customer', {}),
            'project': customer_project.get('project', {}),
            'author': {
                'name': company_brand.get('company_name', ''),
                'logo_path': company_brand.get('logo_path', ''),
                'brand': company_brand.get('brand', {})
            },
            'models': models,
            'checks': checks,
            'language': self.config.get_language()
        }
    
    def _extract_models(self) -> List[Dict[str, Any]]:
        """Extrahiert Modelle aus Config und Results."""
        models_config = self.config.get_models()
        models = []
        
        # Sammle alle Dateinamen aus Results
        files_in_results = set()
        for result in self.report.results:
            if 'file' in result:
                files_in_results.add(result['file'])
        
        # Erstelle Modelle-Liste
        for model_config in models_config:
            file_path = model_config.get('file_path', '')
            file_name = Path(file_path).name if file_path else model_config.get('name', 'Unknown')
            
            # Prüfe ob dieses Modell in Results vorkommt
            if file_name in files_in_results or not files_in_results:
                models.append({
                    'name': model_config.get('name', file_name),
                    'file_path': file_path,
                    'file_name': file_name,
                    'discipline': model_config.get('discipline', ''),
                    'checked_at': datetime.now().isoformat()
                })
        
        return models
    
    def _generate_checks(self) -> List[Dict[str, Any]]:
        """Generiert Checks-Liste aus ValidationReport."""
        checks = []
        language = self.config.get_language()
        
        # Gruppiere Results nach Regel
        rule_results = defaultdict(list)
        for result in self.report.results:
            rule_results[result['rule']].append(result)
        
        # Erstelle Check für jede Regel (auch wenn keine Results)
        for rule_name in self.report.rule_names:
            results_for_rule = rule_results[rule_name]
            
            # Zähle Severities
            counts = defaultdict(int)
            for result in results_for_rule:
                counts[result['severity']] += 1
            
            # Bestimme Status
            status = 'pass'
            if counts['error'] > 0:
                status = 'fail'
            elif counts['warning'] > 0:
                status = 'warn'
            
            # Regel-Beschreibung
            rule_desc = self.config.get_rule_description(rule_name, language)
            
            # Scoped Models (welche Modelle wurden für diese Regel geprüft)
            scoped_models = set()
            for result in results_for_rule:
                if 'file' in result:
                    scoped_models.add(result['file'])
            if not scoped_models:
                # Fallback: Extrahiere Dateinamen aus Config
                for m in self.config.get_models():
                    file_path = m.get('file_path', '')
                    if file_path:
                        file_name = Path(file_path).name
                        scoped_models.add(file_name)
                    else:
                        # Verwende 'name' als Fallback
                        scoped_models.add(m.get('name', 'Unknown'))
            scoped_models = list(scoped_models)
            
            # Findings (nur wenn Status != pass)
            findings = []
            if status != 'pass':
                for result in results_for_rule:
                    finding = {
                        'severity': result['severity'],
                        'message': result['message'],
                        'entity': str(result.get('entity', 'N/A'))
                    }
                    
                    # Füge optionale Entity-Info-Felder hinzu
                    if 'global_id' in result:
                        finding['global_id'] = result['global_id']
                    if 'ifc_type' in result:
                        finding['ifc_type'] = result['ifc_type']
                    if 'storey' in result:
                        finding['storey'] = result['storey']
                    if 'building' in result:
                        finding['building'] = result['building']
                    if 'file' in result:
                        finding['file'] = result['file']
                    
                    findings.append(finding)
            
            check = {
                'id': rule_name.lower().replace(' ', '_'),
                'title': rule_desc['title'],
                'description': rule_desc['description'],
                'status': status,
                'summary': {
                    'pass': 0,  # TODO: Pass-Count wenn implementiert
                    'warn': counts['warning'],
                    'fail': counts['error'],
                    'info': counts['info'],
                    'total': len(results_for_rule)
                },
                'scoped_models': scoped_models,
                'findings': findings
            }
            
            checks.append(check)
        
        return checks
    
    def save_report_data(self, output_path: Optional[Path] = None) -> Path:
        """
        Speichert ReportData als JSON.
        
        Args:
            output_path: Optional - Pfad zur JSON-Datei
            
        Returns:
            Path zur gespeicherten JSON-Datei
        """
        report_data = self.generate()
        
        if output_path is None:
            # Verwende Download-Ordner
            download_folder = get_download_folder()
            report_id = report_data['metadata']['report_id']
            output_dir = download_folder / 'reports' / report_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / 'report_data.json'
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def get_output_directory(self) -> Path:
        """
        Gibt das Output-Verzeichnis zurück (Download-Ordner/reports/{report_id}).
        
        Returns:
            Path zum Output-Verzeichnis
        """
        download_folder = get_download_folder()
        report_data = self.generate()
        report_id = report_data['metadata']['report_id']
        return download_folder / 'reports' / report_id
