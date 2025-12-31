"""Helper-Funktionen zum Laden von Namenskonventions-Konfigurationen aus JSON."""

import json
from pathlib import Path
from typing import Dict, Any, List, Union


def load_naming_convention_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Lädt eine Namenskonventions-Konfiguration aus einer JSON-Datei.
    
    Args:
        config_path: Pfad zur JSON-Konfigurationsdatei
        
    Returns:
        Dict mit 'pattern', 'segment_lengths' und 'allowed_values'
        
    Raises:
        FileNotFoundError: Wenn die Datei nicht gefunden wird
        json.JSONDecodeError: Wenn die JSON-Datei ungültig ist
        ValueError: Wenn die Konfiguration ungültig ist
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Validiere erforderliche Felder
    required_fields = ['pattern', 'segment_lengths']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Konfiguration fehlt erforderliches Feld: {field}")
    
    # 'allowed_values' ist optional
    if 'allowed_values' not in config:
        config['allowed_values'] = {}
    
    # Löse Referenzen auf (z.B. "6": "=2" bedeutet: verwende die Werte von Index 2)
    config['allowed_values'] = _resolve_references(config['allowed_values'])
    
    return config


def _resolve_references(allowed_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Löst Referenzen in allowed_values auf.
    
    Eine Referenz hat das Format "=N", wobei N der Index ist, auf den verwiesen wird.
    Beispiel: "6": "=2" bedeutet, dass Index 6 die gleichen Werte wie Index 2 verwendet.
    
    Args:
        allowed_values: Dict mit möglichen Referenzen
        
    Returns:
        Dict mit aufgelösten Referenzen
    """
    resolved = {}
    
    # Erste Runde: Kopiere alle nicht-Referenz-Werte
    for key, value in allowed_values.items():
        if isinstance(value, str) and value.startswith('='):
            # Das ist eine Referenz, wird später aufgelöst
            continue
        resolved[key] = value
    
    # Zweite Runde: Löse Referenzen auf
    for key, value in allowed_values.items():
        if isinstance(value, str) and value.startswith('='):
            # Extrahiere Referenz-Index
            ref_index = value[1:].strip()
            if ref_index in resolved:
                resolved[key] = resolved[ref_index]
            else:
                raise ValueError(
                    f"Referenz in allowed_values['{key}'] = '{value}' verweist auf "
                    f"nicht existierenden Index '{ref_index}'"
                )
    
    return resolved

