class SessionIndicatorController:
    def __init__(self, window):
        self._window = window
        self._visible = False

    def update(self, active_subject) -> None:
        should_show = active_subject is not None
        if should_show and not self._visible:
            self._window.show()
            self._visible = True
        elif not should_show and self._visible:
            self._window.hide()
            self._visible = False
