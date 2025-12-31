import re
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import ifcopenshell
from .base_rule import BaseRule


class FileNameStructureRule(BaseRule):
    """
    Prüft die Struktur/Pattern von Dateinamen.
    
    Diese Regel prüft nur die Dateinamen-Struktur, nicht den IFC-Inhalt.
    Das ifc_file Parameter wird ignoriert.
    """
    
    def __init__(
        self,
        file_names: Union[str, List[str]],
        pattern: str,
        segment_lengths: List[Union[int, str]],
        severity: str = "error"
    ):
        """
        Args:
            file_names: Einzelner Dateiname oder Liste von Dateinamen
            pattern: Pattern mit Platzhaltern, z.B. "{projekt}_{gebaeude}_{autor}"
            segment_lengths: Liste der erwarteten Segment-Längen, z.B. [5, 1, 2]
            severity: Schweregrad ('error', 'warning', 'info')
        """
        super().__init__(
            name="FileNameStructure",
            description="Prüft Dateinamen-Struktur gegen definiertes Pattern",
            severity=severity
        )
        
        # Normalisiere file_names zu Liste
        if isinstance(file_names, str):
            self.file_names = [file_names]
        else:
            self.file_names = file_names
        
        self.pattern = pattern
        self.segment_lengths = segment_lengths
        
        # Konvertiere Pattern zu Regex
        self.regex_pattern = self._pattern_to_regex(pattern, segment_lengths)
    
    def _pattern_to_regex(self, pattern: str, segment_lengths: List[Union[int, str]]) -> re.Pattern:
        """
        Konvertiert das Pattern mit Platzhaltern zu einem Regex-Pattern.
        
        Beispiel:
            Pattern: "{projekt}_{gebaeude}_{autor}"
            Segment-Längen: [5, 1, 2]
            -> Regex: "^.{5}_.{1}_.{2}\\.ifc$"
        """
        # Finde alle Platzhalter im Pattern
        placeholders = re.findall(r'\{([^}]+)\}', pattern)
        
        if len(placeholders) != len(segment_lengths):
            raise ValueError(
                f"Anzahl der Platzhalter ({len(placeholders)}) stimmt nicht mit "
                f"Anzahl der Segment-Längen ({len(segment_lengths)}) überein"
            )
        
        # Erstelle Regex-Pattern
        regex_str = pattern
        
        # Ersetze jeden Platzhalter durch entsprechende Längen-Prüfung
        for i, (placeholder, length) in enumerate(zip(placeholders, segment_lengths)):
            if isinstance(length, int):
                # Feste Länge: genau N Zeichen
                regex_str = regex_str.replace(f"{{{placeholder}}}", f".{{{length}}}", 1)
            elif isinstance(length, str) and '-' in length:
                # Zusammengesetztes Segment (z.B. "2-4-4")
                # Ersetze durch entsprechende Regex
                parts = length.split('-')
                regex_parts = [f".{{{int(p)}}}" for p in parts]
                regex_str = regex_str.replace(f"{{{placeholder}}}", "-".join(regex_parts), 1)
            else:
                raise ValueError(f"Ungültige Segment-Länge: {length}")
        
        # Escape Sonderzeichen (außer den bereits ersetzten)
        # Aber wir müssen vorsichtig sein - die Bindestriche in zusammengesetzten Segmenten
        # sollten nicht escaped werden
        # Einfacher Ansatz: Escape alles außer den bereits generierten Regex-Teilen
        
        # Füge Dateiendung hinzu (falls nicht vorhanden)
        if not regex_str.endswith(r'\.ifc'):
            regex_str += r'\.ifc'
        
        # Füge Start/End-Anker hinzu
        regex_str = "^" + regex_str + "$"
        
        return re.compile(regex_str)
    
    def _extract_segments(self, filename: str) -> List[str]:
        """
        Extrahiert Segmente aus dem Dateinamen basierend auf dem Pattern und Segment-Längen.
        """
        # Entferne Dateiendung
        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        segments = []
        remaining = name_without_ext
        
        # Parse Pattern um Trennzeichen zu finden
        pattern_parts = re.split(r'\{[^}]+\}', self.pattern)
        delimiters = [part for part in pattern_parts if part]  # Leere Strings entfernen
        
        # Extrahiere Segmente basierend auf Längen
        for i, length in enumerate(self.segment_lengths):
            if isinstance(length, int):
                # Einfaches Segment mit fester Länge
                segment = remaining[:length]
                segments.append(segment)
                remaining = remaining[length:]
                
                # Überspringe Trennzeichen (außer beim letzten Segment)
                if i < len(self.segment_lengths) - 1 and remaining:
                    # Finde nächstes Trennzeichen
                    if remaining[0] in ['_', '-']:
                        remaining = remaining[1:]
            elif isinstance(length, str) and '-' in length:
                # Zusammengesetztes Segment (z.B. "2-4-4")
                parts = [int(p) for p in length.split('-')]
                total_length = sum(parts) + len(parts) - 1  # Summe + Bindestriche
                segment = remaining[:total_length]
                segments.append(segment)
                remaining = remaining[total_length:]
                
                # Überspringe Trennzeichen (außer beim letzten Segment)
                if i < len(self.segment_lengths) - 1 and remaining:
                    if remaining[0] == '_':
                        remaining = remaining[1:]
            else:
                # Fallback: Nimm alles was übrig ist
                segments.append(remaining)
                break
        
        return segments
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        """
        Validiert die Dateinamen-Struktur.
        
        Args:
            ifc_file: Wird ignoriert (nur für Kompatibilität mit BaseRule)
        
        Returns:
            Liste von Validierungsergebnissen
        """
        results = []
        
        for file_name in self.file_names:
            # Entferne Dateiendung für Regex-Prüfung
            name_for_check = file_name if file_name.endswith('.ifc') else file_name + '.ifc'
            
            # Prüfe gegen Regex-Pattern
            if not self.regex_pattern.match(name_for_check):
                results.append(self.create_result(
                    None,
                    f"Dateiname '{file_name}' entspricht nicht dem erwarteten Pattern '{self.pattern}'"
                ))
                continue
            
            # Prüfe Segment-Längen
            segments = self._extract_segments(file_name)
            
            if len(segments) != len(self.segment_lengths):
                results.append(self.create_result(
                    None,
                    f"Dateiname '{file_name}': Falsche Anzahl Segmente. "
                    f"Erwartet: {len(self.segment_lengths)}, Gefunden: {len(segments)}"
                ))
                continue
            
            # Prüfe jede Segment-Länge
            for i, (segment, expected_length) in enumerate(zip(segments, self.segment_lengths)):
                if isinstance(expected_length, int):
                    if len(segment) != expected_length:
                        results.append(self.create_result(
                            None,
                            f"Dateiname '{file_name}': Segment {i} hat falsche Länge. "
                            f"Erwartet: {expected_length} Zeichen, Gefunden: {len(segment)} Zeichen ('{segment}')"
                        ))
                elif isinstance(expected_length, str) and '-' in expected_length:
                    # Zusammengesetztes Segment (z.B. "2-4-4")
                    parts = segment.split('-')
                    expected_parts = [int(p) for p in expected_length.split('-')]
                    if len(parts) != len(expected_parts):
                        results.append(self.create_result(
                            None,
                            f"Dateiname '{file_name}': Segment {i} hat falsche Struktur. "
                            f"Erwartet: {len(expected_parts)} Teile, Gefunden: {len(parts)}"
                        ))
                    else:
                        for j, (part, expected_len) in enumerate(zip(parts, expected_parts)):
                            if len(part) != expected_len:
                                results.append(self.create_result(
                                    None,
                                    f"Dateiname '{file_name}': Segment {i}, Teil {j} hat falsche Länge. "
                                    f"Erwartet: {expected_len} Zeichen, Gefunden: {len(part)} Zeichen ('{part}')"
                                ))
        
        return results


class FileNameValueRule(BaseRule):
    """
    Prüft erlaubte Werte in Dateinamen-Segmenten.
    
    Diese Regel prüft nur die Dateinamen-Werte, nicht den IFC-Inhalt.
    Das ifc_file Parameter wird ignoriert.
    """
    
    def __init__(
        self,
        file_names: Union[str, List[str]],
        pattern: str,
        segment_lengths: List[Union[int, str]],
        allowed_values: Dict[str, Union[List[str], str]],
        severity: str = "error"
    ):
        """
        Args:
            file_names: Einzelner Dateiname oder Liste von Dateinamen
            pattern: Pattern mit Platzhaltern (muss mit FileNameStructureRule übereinstimmen)
            segment_lengths: Liste der Segment-Längen (muss mit FileNameStructureRule übereinstimmen)
            allowed_values: Dict mit {segment_index: [erlaubte_werte]} oder {segment_index: "numeric"}
            severity: Schweregrad ('error', 'warning', 'info')
        """
        super().__init__(
            name="FileNameValue",
            description="Prüft erlaubte Werte in Dateinamen-Segmenten",
            severity=severity
        )
        
        # Normalisiere file_names zu Liste
        if isinstance(file_names, str):
            self.file_names = [file_names]
        else:
            self.file_names = file_names
        
        self.pattern = pattern
        self.segment_lengths = segment_lengths
        self.allowed_values = allowed_values
    
    def _extract_segments(self, filename: str) -> List[str]:
        """
        Extrahiert Segmente aus dem Dateinamen.
        (Gleiche Logik wie in FileNameStructureRule)
        """
        # Entferne Dateiendung
        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        segments = []
        remaining = name_without_ext
        
        # Parse Pattern um Trennzeichen zu finden
        pattern_parts = re.split(r'\{[^}]+\}', self.pattern)
        delimiters = [part for part in pattern_parts if part]  # Leere Strings entfernen
        
        # Extrahiere Segmente basierend auf Längen
        for i, length in enumerate(self.segment_lengths):
            if isinstance(length, int):
                # Einfaches Segment mit fester Länge
                segment = remaining[:length]
                segments.append(segment)
                remaining = remaining[length:]
                
                # Überspringe Trennzeichen (außer beim letzten Segment)
                if i < len(self.segment_lengths) - 1 and remaining:
                    # Finde nächstes Trennzeichen
                    if remaining[0] in ['_', '-']:
                        remaining = remaining[1:]
            elif isinstance(length, str) and '-' in length:
                # Zusammengesetztes Segment (z.B. "2-4-4")
                parts = [int(p) for p in length.split('-')]
                total_length = sum(parts) + len(parts) - 1  # Summe + Bindestriche
                segment = remaining[:total_length]
                segments.append(segment)
                remaining = remaining[total_length:]
                
                # Überspringe Trennzeichen (außer beim letzten Segment)
                if i < len(self.segment_lengths) - 1 and remaining:
                    if remaining[0] == '_':
                        remaining = remaining[1:]
            else:
                # Fallback: Nimm alles was übrig ist
                segments.append(remaining)
                break
        
        return segments
    
    def _split_composite_segment(self, segment: str, length_spec: str) -> List[str]:
        """
        Teilt ein zusammengesetztes Segment (z.B. "2-4-4") in Teile auf.
        """
        if '-' not in length_spec:
            return [segment]
        
        parts = [int(p) for p in length_spec.split('-')]
        result = []
        remaining = segment
        
        for part_len in parts:
            if '-' in remaining:
                # Nimm bis zum Bindestrich
                part, remaining = remaining.split('-', 1)
                result.append(part)
            else:
                # Letzter Teil
                result.append(remaining)
                break
        
        return result
    
    def _validate_segment_value(
        self,
        file_name: str,
        segment_index: int,
        segment_value: str,
        allowed: Union[List[str], str]
    ) -> Optional[str]:
        """
        Validiert einen Segment-Wert gegen erlaubte Werte.
        
        Returns:
            Fehlermeldung oder None wenn OK
        """
        if isinstance(allowed, str):
            if allowed == "numeric":
                if not segment_value.isdigit():
                    return (
                        f"Dateiname '{file_name}': Segment {segment_index} muss numerisch sein, "
                        f"gefunden: '{segment_value}'"
                    )
            elif allowed.startswith("pattern:"):
                # Regex-Pattern
                pattern = allowed[8:]  # Entferne "pattern:" Präfix
                if not re.match(pattern, segment_value):
                    return (
                        f"Dateiname '{file_name}': Segment {segment_index} entspricht nicht dem Pattern '{pattern}', "
                        f"gefunden: '{segment_value}'"
                    )
        elif isinstance(allowed, list):
            if segment_value not in allowed:
                return (
                    f"Dateiname '{file_name}': Segment {segment_index} hat unerlaubten Wert '{segment_value}'. "
                    f"Erlaubte Werte: {', '.join(allowed)}"
                )
        
        return None
    
    def validate(self, ifc_file: ifcopenshell.file) -> List[Dict[str, Any]]:
        """
        Validiert die erlaubten Werte in Dateinamen-Segmenten.
        
        Args:
            ifc_file: Wird ignoriert (nur für Kompatibilität mit BaseRule)
        
        Returns:
            Liste von Validierungsergebnissen
        """
        results = []
        
        for file_name in self.file_names:
            segments = self._extract_segments(file_name)
            
            # Prüfe jedes Segment gegen allowed_values
            for segment_index_str, allowed in self.allowed_values.items():
                try:
                    segment_index = int(segment_index_str)
                except ValueError:
                    continue  # Überspringe ungültige Indizes
                
                if segment_index >= len(segments):
                    results.append(self.create_result(
                        None,
                        f"Dateiname '{file_name}': Segment {segment_index} existiert nicht "
                        f"(nur {len(segments)} Segmente vorhanden)"
                    ))
                    continue
                
                segment_value = segments[segment_index]
                segment_length = self.segment_lengths[segment_index]
                
                # Prüfe ob es ein zusammengesetztes Segment ist
                if isinstance(segment_length, str) and '-' in segment_length:
                    # Zusammengesetztes Segment (z.B. "2-4-4")
                    if isinstance(allowed, dict):
                        # Erlaubte Werte für Sub-Segmente
                        sub_segments = self._split_composite_segment(segment_value, segment_length)
                        expected_parts = segment_length.split('-')
                        
                        if len(sub_segments) != len(expected_parts):
                            results.append(self.create_result(
                                None,
                                f"Dateiname '{file_name}': Segment {segment_index} hat falsche Anzahl Teile. "
                                f"Erwartet: {len(expected_parts)}, Gefunden: {len(sub_segments)}"
                            ))
                            continue
                        
                        # Prüfe jedes Sub-Segment
                        for sub_index, (sub_segment, sub_allowed) in enumerate(zip(sub_segments, expected_parts)):
                            sub_key = str(sub_index)
                            if sub_key in allowed:
                                error = self._validate_segment_value(
                                    file_name,
                                    f"{segment_index}.{sub_index}",
                                    sub_segment,
                                    allowed[sub_key]
                                )
                                if error:
                                    results.append(self.create_result(None, error))
                    else:
                        # Einfache Prüfung für das gesamte zusammengesetzte Segment
                        error = self._validate_segment_value(
                            file_name,
                            segment_index,
                            segment_value,
                            allowed
                        )
                        if error:
                            results.append(self.create_result(None, error))
                else:
                    # Einfaches Segment
                    error = self._validate_segment_value(
                        file_name,
                        segment_index,
                        segment_value,
                        allowed
                    )
                    if error:
                        results.append(self.create_result(None, error))
        
        return results

