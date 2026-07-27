from pars_shared import i18n


def test_turkish_translation():
    _ = i18n.install("tr")
    assert _("test") == "deneme"


def test_english_translation():
    _ = i18n.install("en")
    assert _("test") == "test"


def test_missing_translation_falls_back_to_source_string():
    _ = i18n.install("de")
    assert _("Session active") == "Session active"
