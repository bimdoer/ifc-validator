from typing import List, Dict, Any, Optional
import ifcopenshell
from .rules import BaseRule
from .report import ValidationReport


class IFCValidator:
    """Hauptklasse für die IFC-Validierung."""
    
    def __init__(self, rules: List[BaseRule] = None):
        """
        Args:
            rules: Liste von Validierungsregeln. Wenn None, werden Standard-Regeln verwendet.
        """
        if rules is None:
            from .rules import (
                GeometryValidationRule,
                BoundingBoxRule,
                HierarchyRule
            )
            self.rules = [
                GeometryValidationRule(),
                BoundingBoxRule(),
                HierarchyRule(),
            ]
        else:
            self.rules = rules
    
    def add_rule(self, rule: BaseRule):
        """Fügt eine neue Regel hinzu."""
        self.rules.append(rule)
    
    def validate(self, ifc_file: ifcopenshell.file) -> ValidationReport:
        """
        Validiert eine IFC-Datei gegen alle konfigurierten Regeln.
        
        Args:
            ifc_file: Die zu validierende IFC-Datei
            
        Returns:
            ValidationReport mit allen Ergebnissen
        """
        all_results = []
        
        for rule in self.rules:
            try:
                results = rule.validate(ifc_file)
                all_results.extend(results)
            except Exception as e:
                all_results.append({
                    'rule': rule.name,
                    'entity': None,
                    'message': f"Fehler bei Regelausführung: {str(e)}",
                    'severity': 'error'
                })
        
        # Übergib auch die Liste der verwendeten Regeln an den Report
        rule_names = [rule.name for rule in self.rules]
        return ValidationReport(all_results, rule_names=rule_names)
    
    def validate_multiple(
        self, 
        ifc_files: List[ifcopenshell.file],
        file_names: Optional[List[str]] = None,
        comparison_rules: Optional[List[BaseRule]] = None
    ) -> ValidationReport:
        """
        Validiert mehrere IFC-Dateien und vergleicht sie miteinander.
        
        Args:
            ifc_files: Liste von IFC-Dateien, die validiert werden sollen
            file_names: Optionale Liste von Dateinamen für bessere Fehlermeldungen
            comparison_rules: Optionale Liste von Regeln, die speziell für 
                             Mehrdateien-Vergleiche verwendet werden sollen.
                             Diese werden zusätzlich zu den normalen Regeln ausgeführt.
        
        Returns:
            ValidationReport mit allen Ergebnissen von allen Dateien
        
        Example:
            >>> files = [load_ifc_file("file1.ifc"), load_ifc_file("file2.ifc")]
            >>> validator = IFCValidator(rules=[FloorHeightRule()])
            >>> report = validator.validate_multiple(files, file_names=["file1.ifc", "file2.ifc"])
        """
        if not ifc_files:
            return ValidationReport([], rule_names=[rule.name for rule in self.rules])
        
        all_results = []
        
        # Dateinamen normalisieren
        if file_names is None:
            file_names = [f"Datei {i+1}" for i in range(len(ifc_files))]
        elif len(file_names) != len(ifc_files):
            # Fallback wenn Anzahl nicht übereinstimmt
            file_names = file_names[:len(ifc_files)]
            file_names.extend([f"Datei {i+1}" for i in range(len(file_names), len(ifc_files))])
        
        # 1. Schritt: Einzelvalidierung jeder Datei
        file_metadata = []
        for idx, ifc_file in enumerate(ifc_files):
            file_name = file_names[idx]
            
            # Normale Regeln auf jede Datei anwenden
            for rule in self.rules:
                try:
                    results = rule.validate(ifc_file)
                    # Füge Dateinamen zu Ergebnissen hinzu
                    for result in results:
                        result['file'] = file_name
                        if 'message' in result:
                            result['message'] = f"[{file_name}] {result['message']}"
                    all_results.extend(results)
                    
                    # Prüfe ob Regel Metadaten für Vergleich bereitstellt
                    if hasattr(rule, 'get_metadata'):
                        metadata = rule.get_metadata()
                        if metadata:
                            metadata['file_name'] = file_name
                            metadata['file_index'] = idx
                            file_metadata.append(metadata)
                            
                except Exception as e:
                    all_results.append({
                        'rule': rule.name,
                        'entity': None,
                        'file': file_name,
                        'message': f"[{file_name}] Fehler bei Regelausführung: {str(e)}",
                        'severity': 'error'
                    })
        
        # 2. Schritt: Vergleichsregeln (wenn vorhanden)
        if comparison_rules and len(ifc_files) > 1:
            # Erste Datei als Referenz verwenden (oder alle paarweise vergleichen)
            reference_metadata = file_metadata[0] if file_metadata else None
            
            for comparison_rule in comparison_rules:
                # Wenn Vergleichsregel Referenz-Metadaten benötigt
                if hasattr(comparison_rule, 'set_reference_metadata') and reference_metadata:
                    comparison_rule.set_reference_metadata(reference_metadata)
                
                # Wende Vergleichsregel auf alle Dateien an (außer Referenz)
                for idx, ifc_file in enumerate(ifc_files[1:], start=1):
                    file_name = file_names[idx]
                    try:
                        results = comparison_rule.validate(ifc_file)
                        for result in results:
                            result['file'] = file_name
                            result['message'] = f"[{file_name}] {result['message']}"
                        all_results.extend(results)
                    except Exception as e:
                        all_results.append({
                            'rule': comparison_rule.name,
                            'entity': None,
                            'file': file_name,
                            'message': f"[{file_name}] Fehler bei Vergleichsregel: {str(e)}",
                            'severity': 'error'
                        })
        
        # Sammle alle Regelnamen
        rule_names = [rule.name for rule in self.rules]
        if comparison_rules:
            rule_names.extend([rule.name for rule in comparison_rules])
        
        return ValidationReport(all_results, rule_names=rule_names)

