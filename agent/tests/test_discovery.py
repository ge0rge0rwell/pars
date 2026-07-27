import socket

from zeroconf import Zeroconf

from pars_agent.discovery import SERVICE_TYPE, advertise, stop_advertising


def test_advertised_service_is_discoverable_on_local_segment():
    local_ip = socket.gethostbyname(socket.gethostname())
    zc_server, info = advertise(hostname="itlab-test", port=5901, ip=local_ip)
    try:
        browser_zc = Zeroconf()
        try:
            found = browser_zc.get_service_info(
                SERVICE_TYPE, f"itlab-test.{SERVICE_TYPE}", timeout=5000
            )
            assert found is not None
            assert found.port == 5901
        finally:
            browser_zc.close()
    finally:
        stop_advertising(zc_server, info)
