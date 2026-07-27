from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass


@dataclass(frozen=True)
class TunnelEndpoint:

    listen_host: str
    listen_port: int
    connect_host: str
    connect_port: int
    cert_path: str
    key_path: str
    role: str


def render_stunnel_config(endpoint: TunnelEndpoint) -> str:
    lines = [
        "[pars-session]",
        f"accept = {endpoint.listen_host}:{endpoint.listen_port}",
        f"connect = {endpoint.connect_host}:{endpoint.connect_port}",
        f"cert = {endpoint.cert_path}",
    ]
    if endpoint.role == "client":
        lines.append("client = yes")
        lines.append(f"CAfile = {endpoint.cert_path}")
    else:
        lines.append(f"key = {endpoint.key_path}")
    return "\n".join(lines) + "\n"


class SessionTunnelManager:

    def __init__(self, stunnel_binary: str = "stunnel", popen=subprocess.Popen):
        self._stunnel_binary = stunnel_binary
        self._popen = popen
        self._active_sessions: dict[str, list[tuple]] = {}

    def start_session(self, grant_id: str, endpoints: list[TunnelEndpoint]) -> None:
        if grant_id in self._active_sessions:
            raise ValueError(f"session already has active tunnels: {grant_id}")

        entries = []
        for endpoint in endpoints:
            config_text = render_stunnel_config(endpoint)
            config_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".conf", delete=False
            )
            config_file.write(config_text)
            config_file.close()
            process = self._popen([self._stunnel_binary, config_file.name])
            entries.append((process, config_file.name))

        self._active_sessions[grant_id] = entries

    def stop_session(self, grant_id: str) -> None:
        entries = self._active_sessions.pop(grant_id, [])
        for process, config_path in entries:
            process.terminate()
            try:
                os.unlink(config_path)
            except OSError:
                pass
