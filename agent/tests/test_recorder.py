from pathlib import Path

from pars_agent.recorder import ScreenshotRecorder


def _fake_runner(calls):
    def run(cmd, **kwargs):
        calls.append(cmd)

        class _Result:
            returncode = 0

        return _Result()

    return run


def test_capture_writes_to_storage_dir_and_invokes_capture_cmd(tmp_path):
    calls = []
    recorder = ScreenshotRecorder(storage_dir=tmp_path, runner=_fake_runner(calls))

    path = recorder.capture("start")

    assert path is not None
    assert path.parent == tmp_path
    assert len(calls) == 1
    assert path.name.split("-", 1)[0] == "start"


def test_scripted_session_produces_screenshot_per_trigger(tmp_path):
    calls = []
    recorder = ScreenshotRecorder(storage_dir=tmp_path, runner=_fake_runner(calls))

    paths = [
        recorder.capture("start"),
        recorder.capture("interval"),
        recorder.capture("end"),
    ]

    assert all(p is not None for p in paths)
    assert len(calls) == 3
    assert len(set(paths)) == 3


def test_capture_missing_binary_returns_none_not_raise(tmp_path):
    def _missing_runner(cmd, **kwargs):
        raise FileNotFoundError(cmd[0])

    recorder = ScreenshotRecorder(storage_dir=tmp_path, runner=_missing_runner)

    assert recorder.capture("start") is None


def test_storage_dir_is_separate_from_audit_log_path(tmp_path):
    storage_dir = tmp_path / "screenshots"
    recorder = ScreenshotRecorder(storage_dir=storage_dir, runner=_fake_runner([]))

    path = recorder.capture("start")

    assert Path(path).is_relative_to(storage_dir)
