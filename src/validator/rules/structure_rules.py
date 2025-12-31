from typing import Dict, List, Any
import ifcopenshell
from .base_rule import BaseRule


class HierarchyRule(BaseRule):
    """Prüft die Hierarchie-Struktur des IFC-Modells."""
    
    def __init__(self):
        super().__init__(
            name="HierarchyValidation",
            description="Validiert die Struktur-Hierarchie",
            severity="warning"
        )
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        results = []
        
        # Beispiel: Prüfe auf Root-Elemente
        projects = ifc_file.by_type("IfcProject")
        if not projects:
            results.append(self.create_result(
                None,
                "Kein IfcProject gefunden"
            ))
        
        return results

