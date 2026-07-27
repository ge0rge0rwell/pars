import socket
import threading
import time

from pars_admin.bulk_import import BulkImportStaging
from pars_admin.enrollment_server import (
    approve,
    handle_connection,
    handle_registration,
    reject,
)
from pars_admin.registry import Registry
from pars_admin.trust_root import ensure_admin_trust_root
from pars_shared import protocol


def _register_message(hostname="itlab-03", fingerprint="ab:cd"):
    return protocol.RegisterMessage(
        hostname=hostname,
        cert_fingerprint=fingerprint,
        cert_pubkey="00" * 32,
        current_ip="10.0.1.5",
        agent_version="0.1.0",
    )


def test_first_contact_creates_pending_registry_entry_no_response(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))

    response = handle_registration(registry, trust_root, _register_message())

    assert response is None
    record = registry.get("itlab-03")
    assert record.enrollment_status == "pending"
    assert record.cert_fingerprint == "ab:cd"


def test_approve_then_registration_returns_enrollment_result(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    handle_registration(registry, trust_root, _register_message())

    approve(registry, "itlab-03")
    response = handle_registration(registry, trust_root, _register_message())

    assert isinstance(response, protocol.EnrollmentResultMessage)
    assert response.approved is True
    assert response.admin_instance_id == trust_root.admin_instance_id


def test_reject_removes_entry_agent_stays_unenrolled(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    handle_registration(registry, trust_root, _register_message())

    reject(registry, "itlab-03")

    assert registry.get("itlab-03") is None


def test_conflicting_fingerprint_returns_conflict_rejection_registry_untouched(
    tmp_path,
):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    handle_registration(registry, trust_root, _register_message())
    approve(registry, "itlab-03")

    response = handle_registration(
        registry, trust_root, _register_message(fingerprint="ff:ff")
    )

    assert isinstance(response, protocol.ConflictRejectionMessage)
    record = registry.get("itlab-03")
    assert record.cert_fingerprint == "ab:cd"
    assert record.enrollment_status == "approved"


def test_handle_connection_over_real_socket_creates_pending_entry(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(conn, registry, trust_root)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(_register_message()).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        reply = client.recv(4096)
    thread.join(timeout=2)

    assert reply == b""
    assert registry.get("itlab-03").enrollment_status == "pending"


def test_handle_connection_malformed_input_does_not_raise(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    errors = []

    def accept_one():
        conn, _addr = server.accept()
        try:
            handle_connection(conn, registry, trust_root)
        except Exception as exc:
            errors.append(exc)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(b"not json")
        client.shutdown(socket.SHUT_WR)
        client.recv(4096)
    thread.join(timeout=2)

    assert errors == []


def test_staged_room_type_auto_applied_on_first_contact(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    staging = BulkImportStaging(str(tmp_path / "staging.sqlite3"))
    csv_path = tmp_path / "machines.csv"
    csv_path.write_text("hostname,room_type\nitlab-03,it_lab\n")
    staging.import_csv(str(csv_path))

    handle_registration(registry, trust_root, _register_message(), staging=staging)

    assert registry.get("itlab-03").room_type == "it_lab"


def test_handle_connection_over_socket_also_applies_staged_room_type(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    staging = BulkImportStaging(str(tmp_path / "staging.sqlite3"))
    csv_path = tmp_path / "machines.csv"
    csv_path.write_text("hostname,room_type\nitlab-03,it_lab\n")
    staging.import_csv(str(csv_path))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(conn, registry, trust_root, staging=staging)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(_register_message()).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        client.recv(4096)
    thread.join(timeout=2)

    assert registry.get("itlab-03").room_type == "it_lab"


def test_handle_connection_dispatches_health_report_to_store(tmp_path):
    from pars_admin.health_store import HealthStore

    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    health_store = HealthStore(str(tmp_path / "health.sqlite3"))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(conn, registry, trust_root, health_store=health_store)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    health_message = protocol.HealthReportMessage(
        hostname="itlab-03",
        disk_free_percent=42.5,
        pending_apt_updates=3,
        failed_systemd_units=0,
    )
    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(health_message).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        client.recv(4096)
    thread.join(timeout=2)

    record = health_store.get("itlab-03")
    assert record.disk_free_percent == 42.5


def test_handle_connection_dispatches_login_request_success(tmp_path):
    from pars_admin.accounts import AccountStore

    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    accounts = AccountStore(str(tmp_path / "accounts.sqlite3"))
    accounts.create_account("teacher.ayse", "correct horse battery staple")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(conn, registry, trust_root, accounts=accounts)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    login_message = protocol.LoginRequestMessage(
        username="teacher.ayse", password="correct horse battery staple"
    )
    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(login_message).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        reply = client.recv(4096)
    thread.join(timeout=2)

    parsed = protocol.from_json(reply.decode("utf-8"))
    assert isinstance(parsed, protocol.LoginResultMessage)
    assert parsed.success is True


def test_handle_connection_dispatches_login_request_wrong_password(tmp_path):
    from pars_admin.accounts import AccountStore

    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    accounts = AccountStore(str(tmp_path / "accounts.sqlite3"))
    accounts.create_account("teacher.ayse", "correct horse battery staple")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(conn, registry, trust_root, accounts=accounts)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    login_message = protocol.LoginRequestMessage(
        username="teacher.ayse", password="wrong"
    )
    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(login_message).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        reply = client.recv(4096)
    thread.join(timeout=2)

    parsed = protocol.from_json(reply.decode("utf-8"))
    assert isinstance(parsed, protocol.LoginResultMessage)
    assert parsed.success is False


def test_handle_connection_dispatches_machine_list_request(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))
    registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")
    registry.upsert("office-01", "office", "11:22", "approved")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(conn, registry, trust_root)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    request = protocol.MachineListRequestMessage(username="teacher.ayse")
    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(request).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        reply = client.recv(4096)
    thread.join(timeout=2)

    parsed = protocol.from_json(reply.decode("utf-8"))
    assert isinstance(parsed, protocol.MachineListResultMessage)
    assert parsed.hostnames == ["itlab-03"]


def test_handle_connection_dispatches_session_request_success(tmp_path):
    from pars_admin.app import AdminApp

    app = AdminApp(
        data_dir=str(tmp_path / "trust"),
        registry_db_path=str(tmp_path / "registry.sqlite3"),
        audit_db_path=str(tmp_path / "audit.sqlite3"),
        staging_db_path=str(tmp_path / "staging.sqlite3"),
    )
    app.registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(conn, app.registry, app.trust_root, app=app)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    request = protocol.SessionRequestMessage(
        username="teacher.ayse",
        hostname="itlab-03",
        action="control",
        session_mode="control",
    )
    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(request).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        reply = client.recv(4096)
    thread.join(timeout=2)

    parsed = protocol.from_json(reply.decode("utf-8"))
    assert isinstance(parsed, protocol.SessionRequestResultMessage)
    assert parsed.error == ""
    assert parsed.grant["target_hostname"] == "itlab-03"


def test_handle_connection_dispatches_session_request_conflict(tmp_path):
    from pars_admin.app import AdminApp

    app = AdminApp(
        data_dir=str(tmp_path / "trust"),
        registry_db_path=str(tmp_path / "registry.sqlite3"),
        audit_db_path=str(tmp_path / "audit.sqlite3"),
        staging_db_path=str(tmp_path / "staging.sqlite3"),
    )
    app.registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")
    app.open_session("teacher.ayse", "teacher", "itlab-03", "control")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(conn, app.registry, app.trust_root, app=app)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    request = protocol.SessionRequestMessage(
        username="teacher.mehmet",
        hostname="itlab-03",
        action="control",
        session_mode="control",
    )
    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(request).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        reply = client.recv(4096)
    thread.join(timeout=2)

    parsed = protocol.from_json(reply.decode("utf-8"))
    assert isinstance(parsed, protocol.SessionRequestResultMessage)
    assert parsed.error != ""
    assert parsed.grant == {}


def test_teacher_moving_machines_session_request_delivers_revoke_to_broker(tmp_path):
    from pars_admin.app import AdminApp

    app = AdminApp(
        data_dir=str(tmp_path / "trust"),
        registry_db_path=str(tmp_path / "registry.sqlite3"),
        audit_db_path=str(tmp_path / "audit.sqlite3"),
        staging_db_path=str(tmp_path / "staging.sqlite3"),
    )
    app.registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")
    app.registry.upsert("itlab-04", "it_lab", "11:22", "approved")
    app.open_session("teacher.ayse", "teacher", "itlab-03", "control")

    broker_received = []

    def broker_accept():
        broker_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        broker_server_sock.bind(("127.0.0.1", 0))
        broker_server_sock.listen(1)
        broker_port_local[0] = broker_server_sock.getsockname()[1]
        conn, _addr = broker_server_sock.accept()
        data = b""
        while not data.endswith(b"\r\n"):
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        broker_received.append(data)
        conn.sendall(
            protocol.to_json(protocol.BrokerSessionResultMessage(success=True)).encode(
                "utf-8"
            )
            + b"\r\n"
        )
        conn.close()
        broker_server_sock.close()

    broker_port_local = [None]
    broker_thread = threading.Thread(target=broker_accept, daemon=True)
    broker_thread.start()

    while broker_port_local[0] is None:
        time.sleep(0.01)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        handle_connection(
            conn,
            app.registry,
            app.trust_root,
            app=app,
            broker_host="127.0.0.1",
            broker_port=broker_port_local[0],
        )
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()

    request = protocol.SessionRequestMessage(
        username="teacher.ayse",
        hostname="itlab-04",
        action="control",
        session_mode="control",
    )
    with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
        client.sendall(protocol.to_json(request).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        client.recv(4096)
    thread.join(timeout=2)
    broker_thread.join(timeout=2)

    assert len(broker_received) == 1
    delivered = protocol.from_json(broker_received[0].rstrip(b"\r\n").decode("utf-8"))
    assert isinstance(delivered, protocol.BrokerGrantDeliveryMessage)
    assert delivered.grant["grant_kind"] == "revoke"
    assert delivered.grant["target_hostname"] == "itlab-03"
