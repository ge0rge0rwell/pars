from twisted.protocols import amp


class EnumerateClients(amp.Command):
    arguments = []
    response = [(b"handles", amp.ListOf(amp.Unicode()))]


class ClientCommand(amp.Command):
    arguments = [(b"handle", amp.Unicode()), (b"command", amp.Unicode())]
    response = [(b"result", amp.String()), (b"filename", amp.Unicode())]


class EpoptesLink(amp.AMP):

    def enumerate_clients(self):
        deferred = self.callRemote(EnumerateClients)
        deferred.addCallback(lambda response: response["handles"])
        return deferred

    def send_command(self, handle: str, command: str):
        deferred = self.callRemote(ClientCommand, handle=handle, command=command)
        deferred.addCallback(lambda response: response["result"])
        return deferred
