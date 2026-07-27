import argparse

from twisted.internet import defer, reactor
from twisted.internet.endpoints import TCP4ServerEndpoint, UNIXClientEndpoint
from twisted.internet.protocol import ClientFactory, Factory
from twisted.protocols import basic

from pars_admin.broker.authz import BrokerAuthzError, GrantGatedBroker
from pars_admin.broker.broker_server import (
    process_broker_grant_delivery,
    process_broker_session_request,
)
from pars_admin.broker.epoptes_link import EpoptesLink
from pars_shared.protocol import (
    BrokerGrantDeliveryMessage,
    BrokerSessionRequestMessage,
    BrokerSessionResultMessage,
    from_json,
    to_json,
)

_DEFAULT_BROKER_LISTEN_HOST = "127.0.0.1"
_DEFAULT_BROKER_LISTEN_PORT = 8744
_DEFAULT_EPOPTESD_SOCKET = "/run/epoptes/epoptes.socket"


class BrokerSessionProtocol(basic.LineReceiver):
    delimiter = b"\r\n"

    def __init__(self, gated_broker: GrantGatedBroker):
        self._gated_broker = gated_broker

    def lineReceived(self, line: bytes) -> None:
        try:
            message = from_json(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            self._reply(BrokerSessionResultMessage(success=False, error=str(exc)))
            return

        if isinstance(message, BrokerSessionRequestMessage):
            processor = process_broker_session_request
        elif isinstance(message, BrokerGrantDeliveryMessage):
            processor = process_broker_grant_delivery
        else:
            self._reply(
                BrokerSessionResultMessage(
                    success=False,
                    error=f"unsupported message type: {message.msg_type!r}",
                )
            )
            return

        try:
            outcome = processor(self._gated_broker, message)
        except (BrokerAuthzError, ValueError) as exc:
            self._reply(BrokerSessionResultMessage(success=False, error=str(exc)))
            return

        deferred = defer.maybeDeferred(lambda: outcome)
        deferred.addCallback(
            lambda _: self._reply(BrokerSessionResultMessage(success=True))
        )
        deferred.addErrback(
            lambda failure: self._reply(
                BrokerSessionResultMessage(success=False, error=str(failure.value))
            )
        )

    def _reply(self, response: BrokerSessionResultMessage) -> None:
        self.sendLine(to_json(response).encode("utf-8"))
        self.transport.loseConnection()


class BrokerSessionFactory(Factory):
    def __init__(self, gated_broker: GrantGatedBroker):
        self._gated_broker = gated_broker

    def buildProtocol(self, addr):
        return BrokerSessionProtocol(self._gated_broker)


class _EpoptesLinkClientFactory(ClientFactory):
    protocol = EpoptesLink

    def __init__(self):
        self.link_deferred = defer.Deferred()

    def buildProtocol(self, addr):
        link = self.protocol()
        self.link_deferred.callback(link)
        return link


def run_broker(
    admin_pubkey: bytes,
    listen_host: str = _DEFAULT_BROKER_LISTEN_HOST,
    listen_port: int = _DEFAULT_BROKER_LISTEN_PORT,
    epoptesd_socket: str = _DEFAULT_EPOPTESD_SOCKET,
) -> None:
    epoptes_factory = _EpoptesLinkClientFactory()
    UNIXClientEndpoint(reactor, epoptesd_socket).connect(epoptes_factory)

    def start_listening(epoptes_link):
        gated_broker = GrantGatedBroker(epoptes_link, admin_pubkey)
        TCP4ServerEndpoint(reactor, listen_port, interface=listen_host).listen(
            BrokerSessionFactory(gated_broker)
        )

    epoptes_factory.link_deferred.addCallback(start_listening)
    reactor.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pars broker")
    pubkey_group = parser.add_mutually_exclusive_group(required=True)
    pubkey_group.add_argument("--admin-pubkey")
    pubkey_group.add_argument("--admin-pubkey-file")
    parser.add_argument("--listen-host", default=_DEFAULT_BROKER_LISTEN_HOST)
    parser.add_argument("--listen-port", type=int, default=_DEFAULT_BROKER_LISTEN_PORT)
    parser.add_argument("--epoptesd-socket", default=_DEFAULT_EPOPTESD_SOCKET)
    args = parser.parse_args()

    if args.admin_pubkey_file:
        with open(args.admin_pubkey_file, "rb") as f:
            admin_pubkey = f.read()
    else:
        admin_pubkey = bytes.fromhex(args.admin_pubkey)

    run_broker(admin_pubkey, args.listen_host, args.listen_port, args.epoptesd_socket)


if __name__ == "__main__":
    main()
