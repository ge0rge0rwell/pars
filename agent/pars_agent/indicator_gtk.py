import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

_INDICATOR_TEXT = "Session active"


class SessionIndicatorWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title=_INDICATOR_TEXT)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_deletable(False)
        self.connect("delete-event", lambda *_: True)
        self.add(Gtk.Label(label=_INDICATOR_TEXT))
