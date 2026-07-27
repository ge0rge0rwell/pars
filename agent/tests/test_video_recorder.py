import signal

from pars_agent.video_recorder import SessionVideoRecorder


class _FakeProcess:
    def __init__(self):
        self.signals = []
        self.terminated = False
        self.waited = False
        self._exited = False

    def send_signal(self, sig):
        self.signals.append(sig)
        self._exited = True

    def wait(self, timeout=None):
        self.waited = True
        if not self._exited:
            raise TimeoutError
        return 0

    def terminate(self):
        self.terminated = True
        self._exited = True

    def poll(self):
        return 0 if self._exited else None


def _fake_popen(calls, process=None):
    def popen(cmd, **kwargs):
        calls.append(cmd)
        return process or _FakeProcess()

    return popen


def test_start_launches_ffmpeg_x11grab_and_returns_path(tmp_path):
    calls = []
    recorder = SessionVideoRecorder(storage_dir=tmp_path, popen=_fake_popen(calls))

    path = recorder.start("start")

    assert path.parent == tmp_path
    assert path.suffix == ".mp4"
    assert len(calls) == 1
    cmd = calls[0]
    assert "ffmpeg" in cmd[0]
    assert "x11grab" in cmd
    assert str(path) in cmd


def test_start_twice_raises(tmp_path):
    calls = []
    recorder = SessionVideoRecorder(storage_dir=tmp_path, popen=_fake_popen(calls))
    recorder.start("start")

    try:
        recorder.start("start")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_stop_sends_sigint_for_clean_finalize(tmp_path):
    calls = []
    process = _FakeProcess()
    recorder = SessionVideoRecorder(
        storage_dir=tmp_path, popen=_fake_popen(calls, process)
    )
    recorder.start("start")

    recorder.stop()

    assert process.signals == [signal.SIGINT]
    assert process.waited is True


def test_stop_when_not_recording_is_safe_no_op(tmp_path):
    recorder = SessionVideoRecorder(storage_dir=tmp_path, popen=_fake_popen([]))

    recorder.stop()


def test_start_missing_ffmpeg_returns_none_not_raise(tmp_path):
    def missing_popen(cmd, **kwargs):
        raise FileNotFoundError(cmd[0])

    recorder = SessionVideoRecorder(storage_dir=tmp_path, popen=missing_popen)

    assert recorder.start("start") is None


def test_start_after_stop_allows_new_recording(tmp_path):
    calls = []
    recorder = SessionVideoRecorder(storage_dir=tmp_path, popen=_fake_popen(calls))
    recorder.start("start")
    recorder.stop()

    path = recorder.start("start")

    assert path is not None
    assert len(calls) == 2
