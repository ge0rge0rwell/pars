import os

import pytest

from pars_agent import config

_FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_loads_valid_answer_file():
    cfg = config.load_config(os.path.join(_FIXTURES, "sample-answer-file.conf"))
    assert cfg.admin_console_host == "10.0.1.1"
    assert cfg.admin_console_port == 8743
    assert cfg.hostname_override is None


def test_rejects_missing_required_key():
    with pytest.raises(ValueError, match="admin_console_host"):
        config.load_config(os.path.join(_FIXTURES, "missing-required-key.conf"))


def test_rejects_nonexistent_file():
    with pytest.raises(ValueError):
        config.load_config(os.path.join(_FIXTURES, "does-not-exist.conf"))
