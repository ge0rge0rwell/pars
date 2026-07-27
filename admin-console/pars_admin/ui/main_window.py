import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from pars_admin.app import AdminApp


class MainWindow(Gtk.Window):
    def __init__(self, app: AdminApp):
        super().__init__(title="Pars Admin Console")
        self.set_default_size(800, 600)
        self._app = app

        notebook = Gtk.Notebook()
        self.add(notebook)

        notebook.append_page(self._build_registry_tab(), Gtk.Label(label="Machines"))
        notebook.append_page(self._build_audit_tab(), Gtk.Label(label="Audit log"))
        notebook.append_page(self._build_backup_tab(), Gtk.Label(label="Backup"))

    def _build_registry_tab(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        store = Gtk.ListStore(str, str, str, str, str)
        for record in self._app.list_machines():
            health = self._app.get_health(record.hostname)
            health_text = (
                f"disk free {health.disk_free_percent:.0f}%, "
                f"{health.pending_apt_updates} updates, "
                f"{health.failed_systemd_units} failed units"
                if health is not None
                else "no report yet"
            )
            store.append(
                [
                    record.hostname,
                    record.room_type,
                    record.cert_fingerprint,
                    record.enrollment_status,
                    health_text,
                ]
            )
        tree = Gtk.TreeView(model=store)
        columns = ("Hostname", "Room type", "Fingerprint", "Status", "Health")
        for index, title in enumerate(columns):
            tree.append_column(
                Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=index)
            )
        box.pack_start(tree, True, True, 0)

        buttons = Gtk.Box(spacing=6)
        approve_button = Gtk.Button(label="Approve selected")
        reject_button = Gtk.Button(label="Reject selected")
        kill_button = Gtk.Button(label="Kill session")
        buttons.pack_start(approve_button, False, False, 0)
        buttons.pack_start(reject_button, False, False, 0)
        buttons.pack_start(kill_button, False, False, 0)
        box.pack_start(buttons, False, False, 0)

        def selected_hostname():
            selection = tree.get_selection()
            model, tree_iter = selection.get_selected()
            return model[tree_iter][0] if tree_iter is not None else None

        def on_approve(_button):
            hostname = selected_hostname()
            if hostname:
                self._app.approve_enrollment(hostname)

        def on_reject(_button):
            hostname = selected_hostname()
            if hostname:
                self._app.reject_enrollment(hostname)

        def on_kill(_button):
            hostname = selected_hostname()
            if hostname:
                self._app.kill_session(hostname)

        approve_button.connect("clicked", on_approve)
        reject_button.connect("clicked", on_reject)
        kill_button.connect("clicked", on_kill)
        return box

    def _build_audit_tab(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        buttons = Gtk.Box(spacing=6)
        csv_button = Gtk.Button(label="Export CSV")
        pdf_button = Gtk.Button(label="Export PDF")
        csv_button.connect(
            "clicked", lambda _b: self._app.export_audit_csv("audit.csv")
        )
        pdf_button.connect(
            "clicked", lambda _b: self._app.export_audit_pdf("audit.pdf")
        )
        buttons.pack_start(csv_button, False, False, 0)
        buttons.pack_start(pdf_button, False, False, 0)
        box.pack_start(buttons, False, False, 0)
        return box

    def _build_backup_tab(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        backup_button = Gtk.Button(label="Back up now")
        backup_button.connect(
            "clicked", lambda _b: self._app.create_backup("backup.tar.gz")
        )
        box.pack_start(backup_button, False, False, 0)
        return box
