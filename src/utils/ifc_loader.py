import ifcopenshell
from pathlib import Path
from typing import Optional, List


def load_ifc_file(file_path: str) -> ifcopenshell.file:
    """
    Lädt eine IFC-Datei.
    
    Args:
        file_path: Pfad zur IFC-Datei
        
    Returns:
        ifcopenshell.file Objekt
        
    Raises:
        FileNotFoundError: Wenn die Datei nicht gefunden wird
        Exception: Bei Fehlern beim Laden
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"IFC-Datei nicht gefunden: {file_path}")
    
    try:
        return ifcopenshell.open(str(path))
    except Exception as e:
        raise Exception(f"Fehler beim Laden der IFC-Datei: {str(e)}")


def load_multiple_ifc_files(file_paths: List[str]) -> List[ifcopenshell.file]:
    """
    Lädt mehrere IFC-Dateien.
    
    Args:
        file_paths: Liste von Pfaden zu IFC-Dateien
        
    Returns:
        Liste von ifcopenshell.file Objekten
        
    Raises:
        FileNotFoundError: Wenn eine Datei nicht gefunden wird
        Exception: Bei Fehlern beim Laden
    """
    files = []
    for file_path in file_paths:
        files.append(load_ifc_file(file_path))
    return files

