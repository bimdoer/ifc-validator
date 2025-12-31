"""Helper-Funktionen für Pfad-Operationen."""

import os
from pathlib import Path
from typing import Optional


def get_download_folder() -> Path:
    """
    Gibt den Pfad zum Download-Ordner des aktuellen Benutzers zurück.
    
    Returns:
        Path-Objekt zum Download-Ordner
        
    Raises:
        OSError: Wenn der Download-Ordner nicht gefunden werden kann
    """
    # Windows
    if os.name == 'nt':
        download_folder = Path.home() / "Downloads"
        if download_folder.exists():
            return download_folder
        
        # Fallback: Versuche über Umgebungsvariable
        user_profile = os.environ.get('USERPROFILE')
        if user_profile:
            download_folder = Path(user_profile) / "Downloads"
            if download_folder.exists():
                return download_folder
    
    # macOS
    elif os.name == 'posix':
        try:
            import platform
            if platform.system() == 'Darwin':
                download_folder = Path.home() / "Downloads"
                if download_folder.exists():
                    return download_folder
        except Exception:
            pass
    
    # Linux
    elif os.name == 'posix':
        # XDG User Directories
        xdg_download_dir = os.environ.get('XDG_DOWNLOAD_DIR')
        if xdg_download_dir:
            download_folder = Path(xdg_download_dir)
            if download_folder.exists():
                return download_folder
        
        # Fallback: Standard Downloads
        download_folder = Path.home() / "Downloads"
        if download_folder.exists():
            return download_folder
    
    # Fallback: Home-Verzeichnis
    return Path.home()
