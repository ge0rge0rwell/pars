import os

from pars_admin.audit import AuditLog
from pars_admin.backup import create_backup as _create_backup
from pars_admin.bulk_import import BulkImportStaging
from pars_admin.enrollment_server import approve, handle_registration, reject
from pars_admin.health_store import HealthStore
from pars_admin.registry import Registry
from pars_admin.session_tracker import SessionTracker
from pars_admin.trust_root import ensure_admin_trust_root
from pars_shared.constants import GRANT_KIND_OPEN

_TRUST_ROOT_FILENAMES = ("admin_instance_id", "trust_root.key", "trust_root.pub")


class AdminApp:
    def __init__(
        self,
        data_dir: str,
        registry_db_path: str,
        audit_db_path: str,
        staging_db_path: str,
        health_db_path: str = None,
    ):
        self._data_dir = data_dir
        self.trust_root = ensure_admin_trust_root(data_dir)
        self.registry = Registry(registry_db_path)
        self.audit = AuditLog(audit_db_path)
        self.staging = BulkImportStaging(staging_db_path)
        self.health = HealthStore(
            health_db_path or os.path.join(data_dir, "health.sqlite3")
        )
        self.sessions = SessionTracker(self.trust_root, self.registry)
        self._registry_db_path = registry_db_path

    def list_machines(self) -> list:
        return self.registry.list_all()

    def get_health(self, hostname: str):
        return self.health.get(hostname)

    def handle_registration(self, message):
        return handle_registration(
            self.registry, self.trust_root, message, staging=self.staging
        )

    def approve_enrollment(self, hostname: str) -> None:
        approve(self.registry, hostname)

    def reject_enrollment(self, hostname: str) -> None:
        reject(self.registry, hostname)

    def bulk_import(self, csv_path: str) -> int:
        return self.staging.import_csv(csv_path)

    def open_session(
        self, subject: str, subject_kind: str, hostname: str, session_mode: str
    ) -> list:
        grants = self.sessions.request_open(
            subject, subject_kind, hostname, session_mode
        )
        for grant in grants:
            ended_at = None if grant.grant_kind == GRANT_KIND_OPEN else grant.issued_at
            self.audit.record(
                subject=grant.subject,
                hostname=grant.target_hostname,
                session_kind=grant.grant_kind,
                started_at=grant.issued_at,
                ended_at=ended_at,
            )
        return grants

    def kill_session(self, hostname: str):
        grant = self.sessions.revoke(hostname)
        self.audit.record(
            subject=grant.subject,
            hostname=grant.target_hostname,
            session_kind=grant.grant_kind,
            started_at=grant.issued_at,
            ended_at=grant.issued_at,
        )
        return grant

    def export_audit_csv(self, path: str) -> None:
        self.audit.export_csv(path)

    def export_audit_pdf(self, path: str) -> None:
        self.audit.export_pdf(path)

    def create_backup(self, output_path: str) -> None:
        paths = [self._registry_db_path]
        paths += [
            os.path.join(self._data_dir, name)
            for name in _TRUST_ROOT_FILENAMES
            if os.path.exists(os.path.join(self._data_dir, name))
        ]
        _create_backup(paths, output_path)
