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
    
    return config

