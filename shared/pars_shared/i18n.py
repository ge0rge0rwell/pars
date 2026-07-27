import gettext
import os

_DOMAIN = "pars"
_LOCALE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "locale",
)

SUPPORTED_LANGUAGES = ("tr", "en")
DEFAULT_LANGUAGE = "tr"


def install(language: str = DEFAULT_LANGUAGE):
    translation = gettext.translation(
        _DOMAIN, localedir=_LOCALE_DIR, languages=[language], fallback=True
    )
    return translation.gettext
