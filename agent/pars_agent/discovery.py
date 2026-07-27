import socket

from zeroconf import ServiceInfo, Zeroconf

SERVICE_TYPE = "_pars-agent._tcp.local."


def advertise(hostname: str, port: int, ip: str) -> tuple[Zeroconf, ServiceInfo]:
    info = ServiceInfo(
        SERVICE_TYPE,
        f"{hostname}.{SERVICE_TYPE}",
        addresses=[socket.inet_aton(ip)],
        port=port,
        properties={},
    )
    zeroconf = Zeroconf()
    zeroconf.register_service(info)
    return zeroconf, info


def stop_advertising(zeroconf: Zeroconf, info: ServiceInfo) -> None:
    zeroconf.unregister_service(info)
    zeroconf.close()
