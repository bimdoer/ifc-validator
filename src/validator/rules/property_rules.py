from typing import Dict, List, Any
import ifcopenshell
from .base_rule import BaseRule


class RequiredPropertiesRule(BaseRule):
    """Prüft, ob erforderliche Properties vorhanden sind."""
    
    def __init__(self, required_properties: List[str] = None):
        super().__init__(
            name="RequiredProperties",
            description="Validiert das Vorhandensein erforderlicher Properties",
            severity="error"
        )
        self.required_properties = required_properties or []
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        results = []
        
        if not self.required_properties:
            return results
        
        products = ifc_file.by_type("IfcProduct")
        for product in products:
            # Prüfe Properties
            if hasattr(product, 'IsDefinedBy'):
                for prop_def in product.IsDefinedBy:
                    if prop_def.is_a('IfcRelDefinesByProperties'):
                        prop_set = prop_def.RelatingPropertyDefinition
                        if hasattr(prop_set, 'HasProperties'):
                            existing_props = [p.Name for p in prop_set.HasProperties]
                            missing = [p for p in self.required_properties if p not in existing_props]
                            if missing:
                                results.append(self.create_result(
                                    product,
                                    f"Fehlende Properties: {', '.join(missing)}"
                                ))
        
        return results

