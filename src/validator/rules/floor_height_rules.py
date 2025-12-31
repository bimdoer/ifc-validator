from typing import Dict, List, Any, Optional
import ifcopenshell
from .base_rule import BaseRule


class FloorHeightRule(BaseRule):
    """Prüft Geschosshöhen, Gesamthöhe und Anzahl der Geschosse."""
    
    def __init__(self, tolerance: float = 0.01, min_floor_height: Optional[float] = None):
        """
        Args:
            tolerance: Toleranz für Höhenvergleiche in Metern
            min_floor_height: Minimale erlaubte Geschosshöhe in Metern (optional)
        """
        super().__init__(
            name="FloorHeightValidation",
            description="Validiert Geschosshöhen, Gesamthöhe und Anzahl Geschosse",
            severity="warning"
        )
        self.tolerance = tolerance
        self.min_floor_height = min_floor_height
        self._metadata = None
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        results = []
        
        # Hole alle Building Storeys
        storeys = ifc_file.by_type("IfcBuildingStorey")
        
        if not storeys:
            results.append(self.create_result(
                None,
                "Keine IfcBuildingStorey gefunden"
            ))
            return results
        
        # Sortiere Storeys nach Elevation
        storeys_with_elevation = []
        for storey in storeys:
            elevation = getattr(storey, 'Elevation', None)
            if elevation is not None:
                try:
                    elevation_float = float(elevation)
                    storeys_with_elevation.append((storey, elevation_float))
                except (ValueError, TypeError):
                    # Elevation ist nicht konvertierbar
                    results.append(self.create_result(
                        storey,
                        f"Ungültige Elevation: {elevation}"
                    ))
        
        if not storeys_with_elevation:
            results.append(self.create_result(
                None,
                "Keine Storeys mit gültiger Elevation gefunden"
            ))
            return results
        
        # Sortiere nach Elevation (aufsteigend)
        storeys_with_elevation.sort(key=lambda x: x[1])
        
        # Berechne Geschosshöhen
        floor_heights = []
        for i in range(len(storeys_with_elevation) - 1):
            current_storey, current_elevation = storeys_with_elevation[i]
            next_storey, next_elevation = storeys_with_elevation[i + 1]
            height = next_elevation - current_elevation
            floor_heights.append({
                'storey': current_storey,
                'height': height,
                'elevation': current_elevation
            })
            
            # Prüfe minimale Geschosshöhe
            if self.min_floor_height and height < self.min_floor_height:
                storey_name = getattr(current_storey, 'Name', f'Geschoss {i+1}')
                results.append(self.create_result(
                    current_storey,
                    f"Geschosshöhe zu gering bei '{storey_name}': {height:.2f}m (min: {self.min_floor_height:.2f}m)"
                ))
        
        # Berechne Gesamthöhe
        if len(storeys_with_elevation) >= 2:
            lowest_elevation = storeys_with_elevation[0][1]
            highest_elevation = storeys_with_elevation[-1][1]
            total_height = highest_elevation - lowest_elevation
            
            # Speichere Metadaten für Vergleich
            self._metadata = {
                'storey_count': len(storeys_with_elevation),
                'total_height': total_height,
                'floor_heights': floor_heights,
                'lowest_elevation': lowest_elevation,
                'highest_elevation': highest_elevation,
                'storeys': storeys_with_elevation
            }
            
            # Info-Meldung mit Zusammenfassung
            results.append({
                'rule': self.name,
                'entity': None,
                'message': f"Gebäude: {len(storeys_with_elevation)} Geschosse, Gesamthöhe: {total_height:.2f}m",
                'severity': 'info',
                'metadata': {
                    'storey_count': len(storeys_with_elevation),
                    'total_height': total_height,
                    'floor_heights': [fh['height'] for fh in floor_heights]
                }
            })
        elif len(storeys_with_elevation) == 1:
            # Nur ein Geschoss gefunden
            self._metadata = {
                'storey_count': 1,
                'total_height': 0.0,
                'floor_heights': [],
                'lowest_elevation': storeys_with_elevation[0][1],
                'highest_elevation': storeys_with_elevation[0][1],
                'storeys': storeys_with_elevation
            }
            results.append({
                'rule': self.name,
                'entity': None,
                'message': f"Gebäude: 1 Geschoss gefunden (keine Höhenberechnung möglich)",
                'severity': 'info',
                'metadata': {
                    'storey_count': 1,
                    'total_height': 0.0,
                    'floor_heights': []
                }
            })
        
        return results
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Gibt Metadaten über Geschosse zurück (für Vergleich)."""
        return self._metadata


class MultiFileFloorComparisonRule(BaseRule):
    """Vergleicht Geschosshöhen zwischen mehreren IFC-Dateien."""
    
    def __init__(self, reference_file_metadata: Dict[str, Any], tolerance: float = 0.01):
        """
        Args:
            reference_file_metadata: Metadaten der Referenzdatei (von FloorHeightRule)
            tolerance: Toleranz für Vergleiche in Metern
        """
        super().__init__(
            name="MultiFileFloorComparison",
            description="Vergleicht Geschosshöhen zwischen mehreren Dateien",
            severity="warning"
        )
        self.reference_metadata = reference_file_metadata
        self.tolerance = tolerance
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        results = []
        
        # Hole Metadaten der aktuellen Datei
        floor_rule = FloorHeightRule(tolerance=self.tolerance)
        current_results = floor_rule.validate(ifc_file)
        current_metadata = floor_rule.get_metadata()
        
        if not current_metadata:
            results.append(self.create_result(
                None,
                "Konnte Metadaten der aktuellen Datei nicht extrahieren"
            ))
            return results
        
        # Vergleiche Anzahl Geschosse
        ref_count = self.reference_metadata.get('storey_count', 0)
        curr_count = current_metadata.get('storey_count', 0)
        
        if ref_count != curr_count:
            results.append(self.create_result(
                None,
                f"Unterschiedliche Anzahl Geschosse: Referenz={ref_count}, Aktuell={curr_count}"
            ))
        
        # Vergleiche Gesamthöhe
        ref_height = self.reference_metadata.get('total_height', 0)
        curr_height = current_metadata.get('total_height', 0)
        
        if abs(ref_height - curr_height) > self.tolerance:
            diff = curr_height - ref_height
            results.append(self.create_result(
                None,
                f"Unterschiedliche Gesamthöhe: Referenz={ref_height:.2f}m, Aktuell={curr_height:.2f}m (Diff: {diff:+.2f}m)"
            ))
        
        # Vergleiche einzelne Geschosshöhen
        ref_heights = self.reference_metadata.get('floor_heights', [])
        curr_heights = current_metadata.get('floor_heights', [])
        
        min_count = min(len(ref_heights), len(curr_heights))
        for i in range(min_count):
            ref_h = ref_heights[i]['height']
            curr_h = curr_heights[i]['height']
            
            if abs(ref_h - curr_h) > self.tolerance:
                diff = curr_h - ref_h
                storey_name = getattr(curr_heights[i]['storey'], 'Name', f'Geschoss {i+1}')
                results.append(self.create_result(
                    curr_heights[i]['storey'],
                    f"Unterschiedliche Geschosshöhe bei '{storey_name}': Referenz={ref_h:.2f}m, Aktuell={curr_h:.2f}m (Diff: {diff:+.2f}m)"
                ))
        
        # Wenn unterschiedliche Anzahl Geschosse, markiere fehlende/überschüssige
        if len(ref_heights) != len(curr_heights):
            if len(curr_heights) < len(ref_heights):
                results.append(self.create_result(
                    None,
                    f"{len(ref_heights) - len(curr_heights)} Geschosse fehlen im Vergleich zur Referenz"
                ))
            else:
                results.append(self.create_result(
                    None,
                    f"{len(curr_heights) - len(ref_heights)} zusätzliche Geschosse vorhanden"
                ))
        
        return results

