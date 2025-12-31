from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
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
    
    def create_result(self, entity, message: str,
                     global_id: Optional[str] = None,
                     ifc_type: Optional[str] = None,
                     storey: Optional[str] = None,
                     building: Optional[str] = None) -> Dict[str, Any]:
        """
        Hilfsmethode zum Erstellen eines Validierungsergebnisses.
        
        Args:
            entity: Die betroffene IFC-Entität
            message: Fehlermeldung
            global_id: Optional - GlobalId der Entity
            ifc_type: Optional - IFC-Typ (z.B. "IfcWall")
            storey: Optional - Geschoss (z.B. "EG")
            building: Optional - Gebäude (z.B. "Building A")
            
        Returns:
            Dictionary mit Validierungsergebnis
        """
        result = {
            'rule': self.name,
            'entity': str(entity),
            'message': message,
            'severity': self.severity
        }
        
        # Füge optionale Entity-Info-Felder hinzu, wenn vorhanden
        if global_id is not None:
            result['global_id'] = global_id
        if ifc_type is not None:
            result['ifc_type'] = ifc_type
        if storey is not None:
            result['storey'] = storey
        if building is not None:
            result['building'] = building
            
        return result

