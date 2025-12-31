from typing import Dict, List, Any
import ifcopenshell
from .base_rule import BaseRule


class GeometryValidationRule(BaseRule):
    """Prüft geometrische Eigenschaften von IFC-Elementen."""
    
    def __init__(self):
        super().__init__(
            name="GeometryValidation",
            description="Validiert grundlegende geometrische Eigenschaften",
            severity="error"
        )
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        results = []
        
        # Beispiel: Prüfe auf Elemente ohne Representation
        products = ifc_file.by_type("IfcProduct")
        for product in products:
            if not product.Representation:
                results.append(self.create_result(
                    product,
                    f"Element {product.GlobalId} hat keine Representation"
                ))
        
        return results


class BoundingBoxRule(BaseRule):
    """Prüft, ob Elemente gültige Bounding Boxes haben."""
    
    def __init__(self):
        super().__init__(
            name="BoundingBoxValidation",
            description="Validiert Bounding Boxes von Elementen",
            severity="warning"
        )
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        results = []
        
        # Beispiel-Implementierung
        products = ifc_file.by_type("IfcProduct")
        for product in products:
            if hasattr(product, 'ObjectPlacement'):
                # Hier können spezifische Bounding Box Checks implementiert werden
                pass
        
        return results

