import socket
import threading

from pars_agent.config import AgentConfig
from pars_agent.health import HealthReport
from pars_agent.health_report import send_health_report
from pars_shared import protocol


def _stub_listener(received: list):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        received.append(data.decode("utf-8"))
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()
    return port, thread


def test_sends_well_formed_health_report_message():
    received = []
    port, thread = _stub_listener(received)
    config = AgentConfig(
        admin_console_host="127.0.0.1", admin_console_port=port, hostname_override=None
    )
    report = HealthReport(
        disk_free_percent=42.5, pending_apt_updates=3, failed_systemd_units=0
    )

    send_health_report(config, hostname="itlab-03", report=report)
    thread.join(timeout=2)

    assert len(received) == 1
    parsed = protocol.from_json(received[0])
    assert isinstance(parsed, protocol.HealthReportMessage)
    assert parsed.hostname == "itlab-03"
    assert parsed.disk_free_percent == 42.5
    assert parsed.pending_apt_updates == 3
    assert parsed.failed_systemd_units == 0
