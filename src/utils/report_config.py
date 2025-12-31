"""Konfigurations-Loader für Report-Generierung."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class ReportConfig:
    """Lädt und verwaltet Report-Konfigurationen."""
    
    def __init__(self, config_path: str, base_path: Optional[Path] = None):
        """
        Args:
            config_path: Pfad zur report_config.json
            base_path: Basis-Pfad für relative Pfade (default: config_path parent)
        """
        self.config_path = Path(config_path)
        if base_path is None:
            self.base_path = self.config_path.parent
        else:
            self.base_path = Path(base_path)
        
        # Lade Konfiguration
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Lade Branding-Dateien
        self._load_branding()
        
        # Lade Regel-Beschreibungen
        self._load_rule_descriptions()
    
    def _load_branding(self):
        """Lädt Branding-Dateien."""
        # Company Branding
        company_path = self._resolve_path(self.config.get('brand_company', ''))
        if company_path and company_path.exists():
            with open(company_path, 'r', encoding='utf-8') as f:
                self.company_brand = json.load(f)
        else:
            self.company_brand = {}
        
        # Customer/Project Branding
        customer_project_path = self._resolve_path(
            self.config.get('brand_customer_project', '')
        )
        if customer_project_path and customer_project_path.exists():
            with open(customer_project_path, 'r', encoding='utf-8') as f:
                self.customer_project = json.load(f)
        else:
            self.customer_project = {}
    
    def _load_rule_descriptions(self):
        """Lädt Regel-Beschreibungen."""
        # Versuche rule_descriptions.json im config-Verzeichnis
        rule_desc_path = self.config_path.parent / 'rule_descriptions.json'
        if rule_desc_path.exists():
            with open(rule_desc_path, 'r', encoding='utf-8') as f:
                self.rule_descriptions = json.load(f)
        else:
            self.rule_descriptions = {}
    
    def _resolve_path(self, path_str: str) -> Optional[Path]:
        """Löst relativen oder absoluten Pfad auf."""
        if not path_str:
            return None
        
        path = Path(path_str)
        if path.is_absolute():
            return path
        
        # Relativ zum base_path
        return self.base_path / path
    
    def get_company_brand(self) -> Dict[str, Any]:
        """Gibt Company-Branding zurück."""
        return self.company_brand
    
    def get_customer_project(self) -> Dict[str, Any]:
        """Gibt Customer/Project-Branding zurück."""
        return self.customer_project
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Gibt Liste der zu prüfenden Modelle zurück."""
        return self.config.get('models', [])
    
    def get_rules(self) -> List[str]:
        """Gibt Liste der Regel-Namen zurück."""
        return self.config.get('rules', [])
    
    def get_language(self) -> str:
        """Gibt die gewählte Sprache zurück (de/en/fr)."""
        return self.config.get('language', 'de')
    
    def get_rule_description(self, rule_name: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Gibt Beschreibung für eine Regel zurück.
        
        Args:
            rule_name: Name der Regel
            language: Sprache (de/en/fr), default: aus Config
            
        Returns:
            Dict mit 'title' und 'description' in gewählter Sprache
        """
        if language is None:
            language = self.get_language()
        
        rule_info = self.rule_descriptions.get(rule_name, {})
        
        title = rule_info.get('title', {}).get(language, rule_name)
        description = rule_info.get('description', {}).get(language, '')
        
        return {
            'title': title,
            'description': description
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """Gibt Output-Konfiguration zurück."""
        return self.config.get('output', {})
    
    def get_project_id(self) -> Optional[str]:
        """Gibt Projekt-ID zurück."""
        project = self.customer_project.get('project', {})
        return project.get('project_id')
