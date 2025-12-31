from abc import ABC, abstractmethod
from typing import Dict, List, Any
import ifcopenshell


class BaseRule(ABC):
    """Basisklasse für alle Validierungsregeln."""
    
    def __init__(self, name: str, description: str, severity: str = "error"):
        """
        Args:
            name: Name der Regel
            description: Beschreibung der Regel
            severity: Schweregrad ('error', 'warning', 'info')
        """
        self.name = name
        self.description = description
        self.severity = severity
    
    @abstractmethod
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        """
        Validiert die IFC-Datei gegen diese Regel.
        
        Args:
            ifc_file: Die zu validierende IFC-Datei
            
        Returns:
            Liste von Validierungsergebnissen, jedes mit:
            - 'entity': Die betroffene IFC-Entität
            - 'message': Fehlermeldung
            - 'severity': Schweregrad
        """
        pass
    
    def create_result(self, entity, message: str) -> Dict[str, Any]:
        """Hilfsmethode zum Erstellen eines Validierungsergebnisses."""
        return {
            'rule': self.name,
            'entity': str(entity),
            'message': message,
            'severity': self.severity
        }

