import json

import pytest

from pars_agent.grant_verify import GrantVerifier
from pars_agent.main import AgentLoop, run_forever
from pars_shared import crypto, grant


class _FakeIndicator:
    def __init__(self):
        self.states = []

    def update(self, active_subject):
        self.states.append(active_subject)


class _FakeRecorder:
    def __init__(self):
        self.labels = []

    def capture(self, label):
        self.labels.append(label)


def _drop_grant(inbox_dir, priv, pub, grant_id, grant_kind="open"):
    g = grant.build_and_sign(
        grant_id=grant_id,
        issued_at="2026-07-23T00:00:00Z",
        admin_instance_id="school-42",
        admin_private_key=priv,
        admin_public_key=pub,
        subject="teacher.ayse",
        subject_kind="teacher",
        target_hostname="itlab-03",
        target_cert_fingerprint="ab:cd",
        session_mode="control",
        grant_kind=grant_kind,
    )
    (inbox_dir / f"{grant_id}.json").write_text(json.dumps(grant.to_wire_dict(g)))


def test_tick_with_no_grant_is_idle():
    verifier = GrantVerifier(pinned_admin_pubkey=b"\x01" * 32, own_hostname="itlab-03")
    indicator, recorder = _FakeIndicator(), _FakeRecorder()
    loop = AgentLoop(verifier, indicator, recorder, inbox_dir=None)

    loop.tick()

    assert indicator.states == [None]
    assert recorder.labels == []


def test_open_grant_shows_indicator_and_captures_start(tmp_path):
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    indicator, recorder = _FakeIndicator(), _FakeRecorder()
    loop = AgentLoop(verifier, indicator, recorder, inbox_dir=tmp_path)
    _drop_grant(tmp_path, priv, pub, "g-1")

    loop.tick()

    assert indicator.states == ["teacher.ayse"]
    assert recorder.labels == ["start"]


def test_second_tick_during_session_captures_interval(tmp_path):
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    indicator, recorder = _FakeIndicator(), _FakeRecorder()
    loop = AgentLoop(verifier, indicator, recorder, inbox_dir=tmp_path)
    _drop_grant(tmp_path, priv, pub, "g-1")
    loop.tick()

    loop.tick()

    assert recorder.labels == ["start", "interval"]


def test_revoke_grant_hides_indicator_and_captures_end(tmp_path):
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    indicator, recorder = _FakeIndicator(), _FakeRecorder()
    loop = AgentLoop(verifier, indicator, recorder, inbox_dir=tmp_path)
    _drop_grant(tmp_path, priv, pub, "g-1")
    loop.tick()

    _drop_grant(tmp_path, priv, pub, "g-2", grant_kind="revoke")
    loop.tick()

    assert indicator.states == ["teacher.ayse", None]
    assert recorder.labels == ["start", "end"]


def test_run_forever_calls_health_reporter_every_nth_tick():
    verifier = GrantVerifier(pinned_admin_pubkey=b"\x01" * 32, own_hostname="itlab-03")
    loop = AgentLoop(verifier, _FakeIndicator(), _FakeRecorder(), inbox_dir=None)
    health_calls = []
    sleep_calls = []

    def fake_sleep(_interval):
        sleep_calls.append(1)
        if len(sleep_calls) >= 5:
            raise StopIteration

    with pytest.raises(StopIteration):
        run_forever(
            loop,
            sleep_fn=fake_sleep,
            health_reporter=lambda: health_calls.append(1),
            health_report_every=2,
        )

    assert health_calls == [1, 1]
