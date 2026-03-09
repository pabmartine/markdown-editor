import gettext
import locale
import os
from pathlib import Path

from .constants import APP_DOMAIN

_current_gettext = lambda text: text


def get_locale_dir():
    """Obtener directorio de locale apropiado"""
    project_locale = Path(__file__).resolve().parents[3] / "locale"
    possible_dirs = [
        Path("/app/share/locale"),
        project_locale,
        Path("/usr/share/locale"),
    ]
    
    for locale_dir in possible_dirs:
        if locale_dir.exists():
            return str(locale_dir)
    
    return str(project_locale)

LOCALE_DIR = get_locale_dir()
DOMAIN = APP_DOMAIN

def setup_locale(language=None):
    """Configurar el idioma de la aplicación - Compatible con Flatpak"""
    global _current_gettext

    if language and language != "auto":
        try:
            os.environ["LANGUAGE"] = language
            os.environ["LC_MESSAGES"] = language
        except:
            pass
    else:
        os.environ.pop("LANGUAGE", None)
        os.environ.pop("LC_MESSAGES", None)
    
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        try:
            # Fallback para entornos restringidos como Flatpak
            locale.setlocale(locale.LC_ALL, "C.UTF-8")
        except locale.Error:
            pass
    
    try:
        # Detectar si estamos en Flatpak
        is_flatpak = os.path.exists("/app") or os.environ.get("FLATPAK_ID")
        
        if is_flatpak:
            # En Flatpak, usar directamente /app/share/locale
            locale_dir = "/app/share/locale"
        else:
            locale_dir = LOCALE_DIR
        
        if os.path.exists(locale_dir):
            lang_translations = gettext.translation(DOMAIN, locale_dir, fallback=True)
            lang_translations.install()
            _current_gettext = lang_translations.gettext
            return _current_gettext
        else:
            _current_gettext = lambda text: text
            return _current_gettext
            
    except Exception as e:
        print(f"Warning: Error configurando locale: {e}")
        _current_gettext = lambda text: text
        return _current_gettext

def translate(text):
    return _current_gettext(text)

_ = translate

setup_locale()

# Función simple para obtener idiomas disponibles
def get_available_languages():
    """Obtener lista de idiomas disponibles"""
    return [
        ("auto", _("Auto-detect")),
        ("en", _("English")),  
        ("es", _("Spanish"))
    ]

# Función para cambiar idioma dinámicamente
def change_language_global(language_code):
    """Cambiar idioma dinámicamente"""
    return setup_locale(language_code if language_code != "auto" else None)
