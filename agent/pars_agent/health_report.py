from __future__ import annotations

import socket

from pars_agent.config import AgentConfig
from pars_agent.health import HealthReport
from pars_shared import protocol
from pars_shared.constants import ENROLLMENT_TIMEOUT_SECONDS


def send_health_report(
    config: AgentConfig, hostname: str, report: HealthReport
) -> None:
    message = protocol.HealthReportMessage(
        hostname=hostname,
        disk_free_percent=report.disk_free_percent,
        pending_apt_updates=report.pending_apt_updates,
        failed_systemd_units=report.failed_systemd_units,
    )
    payload = protocol.to_json(message).encode("utf-8")

    with socket.create_connection(
        (config.admin_console_host, config.admin_console_port),
        timeout=ENROLLMENT_TIMEOUT_SECONDS,
    ) as sock:
        sock.sendall(payload)
