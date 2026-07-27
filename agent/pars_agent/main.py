from __future__ import annotations

import argparse
import socket
import time
from pathlib import Path

from pars_agent.admin_pin import AdminPinStore
from pars_agent.config import load_config
from pars_agent.enrollment import ensure_agent_identity
from pars_agent.grant_inbox import check_inbox
from pars_agent.grant_verify import GrantVerifier
from pars_agent.health import collect_health
from pars_agent.health_report import send_health_report
from pars_agent.recorder import ScreenshotRecorder
from pars_agent.register import send_register_message
from pars_agent.video_recorder import SessionVideoRecorder
from pars_shared.protocol import EnrollmentResultMessage

_TICK_INTERVAL_SECONDS = 30


class AgentLoop:
    def __init__(
        self,
        verifier: GrantVerifier,
        indicator,
        recorder,
        inbox_dir,
        video_recorder=None,
    ):
        self._verifier = verifier
        self._indicator = indicator
        self._recorder = recorder
        self._inbox_dir = inbox_dir
        self._video_recorder = video_recorder
        self._last_subject = None

    def tick(self) -> None:
        if self._inbox_dir is not None:
            check_inbox(self._verifier, self._inbox_dir)

        subject = self._verifier.active_session_subject()
        self._indicator.update(subject)

        if subject is not None and self._last_subject is None:
            self._recorder.capture("start")
            if self._video_recorder is not None:
                self._video_recorder.start("session")
        elif subject is None and self._last_subject is not None:
            self._recorder.capture("end")
            if self._video_recorder is not None:
                self._video_recorder.stop()
        elif subject is not None:
            self._recorder.capture("interval")

        self._last_subject = subject


class _NullIndicator:

    def update(self, active_subject) -> None:
        pass


def _build_indicator():
    try:
        from pars_agent.indicator import SessionIndicatorController
        from pars_agent.indicator_gtk import SessionIndicatorWindow

        return SessionIndicatorController(SessionIndicatorWindow())
    except (ImportError, ValueError):
        return _NullIndicator()


def bootstrap(answer_file: str, data_dir: str) -> AgentLoop:
    config = load_config(answer_file)
    identity = ensure_agent_identity(data_dir)
    pin_store = AdminPinStore(data_dir)

    hostname = config.hostname_override or socket.gethostname()
    response = send_register_message(
        config, identity, hostname=hostname, current_ip=socket.gethostbyname(hostname)
    )

    admin_pubkey = b"\x00" * 32
    if isinstance(response, EnrollmentResultMessage) and response.approved:
        admin_pubkey_bytes = bytes.fromhex(response.admin_pubkey)
        pin_store.pin_or_verify(response.admin_instance_id, admin_pubkey_bytes)
        admin_pubkey = admin_pubkey_bytes

    verifier = GrantVerifier(pinned_admin_pubkey=admin_pubkey, own_hostname=hostname)
    recorder = ScreenshotRecorder(storage_dir=Path(data_dir) / "screenshots")
    video_recorder = SessionVideoRecorder(storage_dir=Path(data_dir) / "videos")
    indicator = _build_indicator()
    inbox_dir = Path(data_dir) / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    loop = AgentLoop(
        verifier, indicator, recorder, inbox_dir, video_recorder=video_recorder
    )

    def health_reporter():
        send_health_report(config, hostname=hostname, report=collect_health())

    return loop, health_reporter


def run_forever(
    loop: AgentLoop,
    interval=_TICK_INTERVAL_SECONDS,
    sleep_fn=time.sleep,
    health_reporter=None,
    health_report_every=10,
) -> None:
    tick_count = 0
    while True:
        loop.tick()
        tick_count += 1
        if health_reporter is not None and tick_count % health_report_every == 0:
            health_reporter()
        sleep_fn(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pars agent")
    parser.add_argument("--answer-file", required=True)
    parser.add_argument("--data-dir", required=True)
    args = parser.parse_args()

    loop, health_reporter = bootstrap(args.answer_file, args.data_dir)
    run_forever(loop, health_reporter=health_reporter)


if __name__ == "__main__":
    main()
