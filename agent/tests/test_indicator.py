from pars_agent.indicator import SessionIndicatorController


class _FakeWindow:
    def __init__(self):
        self.visible = False
        self.show_calls = 0
        self.hide_calls = 0

    def show(self):
        self.visible = True
        self.show_calls += 1

    def hide(self):
        self.visible = False
        self.hide_calls += 1


def test_active_subject_shows_window():
    window = _FakeWindow()
    controller = SessionIndicatorController(window)

    controller.update(active_subject="teacher.ayse")

    assert window.visible is True
    assert window.show_calls == 1


def test_none_subject_hides_window():
    window = _FakeWindow()
    controller = SessionIndicatorController(window)
    controller.update(active_subject="teacher.ayse")

    controller.update(active_subject=None)

    assert window.visible is False
    assert window.hide_calls == 1


def test_repeated_same_state_does_not_re_trigger():
    window = _FakeWindow()
    controller = SessionIndicatorController(window)

    controller.update(active_subject="teacher.ayse")
    controller.update(active_subject="teacher.ayse")

    assert window.show_calls == 1


def test_no_close_method_exposed():
    window = _FakeWindow()
    controller = SessionIndicatorController(window)
    controller.update(active_subject="teacher.ayse")

    assert not hasattr(controller, "close")
    assert not hasattr(controller, "dismiss")
