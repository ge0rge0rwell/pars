from pars_admin.accounts import AccountStore


def test_create_then_verify_correct_password_succeeds(tmp_path):
    store = AccountStore(str(tmp_path / "accounts.sqlite3"))
    store.create_account("teacher.ayse", "correct horse battery staple")

    assert store.verify_login("teacher.ayse", "correct horse battery staple") is True


def test_verify_wrong_password_fails(tmp_path):
    store = AccountStore(str(tmp_path / "accounts.sqlite3"))
    store.create_account("teacher.ayse", "correct horse battery staple")

    assert store.verify_login("teacher.ayse", "wrong password") is False


def test_verify_unknown_username_fails(tmp_path):
    store = AccountStore(str(tmp_path / "accounts.sqlite3"))

    assert store.verify_login("ghost", "anything") is False


def test_password_never_stored_in_plaintext(tmp_path):
    db_path = tmp_path / "accounts.sqlite3"
    store = AccountStore(str(db_path))
    password = "correct horse battery staple"

    store.create_account("teacher.ayse", password)

    raw = db_path.read_bytes()
    assert password.encode("utf-8") not in raw


def test_create_duplicate_username_raises(tmp_path):
    import pytest

    store = AccountStore(str(tmp_path / "accounts.sqlite3"))
    store.create_account("teacher.ayse", "first-password")

    with pytest.raises(ValueError):
        store.create_account("teacher.ayse", "second-password")
