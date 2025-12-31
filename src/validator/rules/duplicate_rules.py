from typing import Dict, List, Any, Callable, Optional
import ifcopenshell
from collections import defaultdict
from .base_rule import BaseRule


class DuplicateRule(BaseRule):
    """Prüft auf Duplikate basierend auf einem Feld."""
    
    def __init__(self, field_name: str, entity_types: List[str] = None, 
                 get_value_func: Optional[Callable] = None, severity: str = "error"):
        """
        Args:
            field_name: Name des Feldes, nach dem auf Duplikate geprüft wird
            entity_types: Liste von IFC-Entitätstypen, die geprüft werden sollen.
                         Standard: ["IfcProduct"]
            get_value_func: Optionale Funktion zum Extrahieren des Wertes.
                           Wenn None, wird getattr(entity, field_name) verwendet
            severity: Schweregrad ('error', 'warning', 'info')
        """
        super().__init__(
            name=f"Duplicate{field_name}",
            description=f"Prüft auf doppelte {field_name} Werte",
            severity=severity
        )
        self.field_name = field_name
        self.entity_types = entity_types or ["IfcProduct"]
        self.get_value_func = get_value_func
    
    def _get_value(self, entity) -> Any:
        """Extrahiert den Wert des Feldes von der Entität."""
        if self.get_value_func:
            return self.get_value_func(entity)
        
        # Standard: Versuche das Attribut direkt zu lesen
        if hasattr(entity, self.field_name):
            return getattr(entity, self.field_name)
        
        return None
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        results = []
        
        # Sammle alle Entitäten der angegebenen Typen
        all_entities = []
        for entity_type in self.entity_types:
            entities = ifc_file.by_type(entity_type)
            all_entities.extend(entities)
        
        # Gruppiere nach Feldwert
        value_to_entities = defaultdict(list)
        for entity in all_entities:
            value = self._get_value(entity)
            if value is not None:
                value_to_entities[value].append(entity)
        
        # Finde Duplikate (Werte mit mehr als einer Entität)
        for value, entities in value_to_entities.items():
            if len(entities) > 1:
                # Erstelle Fehlermeldung für alle betroffenen Entitäten
                entity_ids = [str(e) for e in entities]
                results.append(self.create_result(
                    entities[0],  # Erste Entität als Referenz
                    f"Duplikat gefunden: {self.field_name}='{value}' wird {len(entities)}x verwendet. "
                    f"Betroffene Entitäten: {', '.join(entity_ids[:5])}"
                    + (f" (und {len(entities) - 5} weitere)" if len(entities) > 5 else "")
                ))
        
        return results

