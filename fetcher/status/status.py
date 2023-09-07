from abc import abstractmethod

from . import ping as ping_module


class Status:
    def __init__(self, ping: ping_module.Ping):
        self._ping = ping

    @abstractmethod
    def update(self):
        raise NotImplementedError


class DockerStatus(Status):
    def __init__(self, container, ping: ping_module.Ping, update_on_ping: bool = True):
        super().__init__(ping=ping)

        self._container = container
        self._update_on_ping = update_on_ping

    @property
    def exited(self):
        return not self._container.attrs["State"]["Running"]

    def update(self):
        self._container.reload()

    def ping(self):
        self._container.reload() if self._update_on_ping else None

        match self._container.attrs["State"]:
            case {"Status": "running"}:
                self._ping.ping("running", None, None)
            case {"Status": "exited", "ExitCode": 0}:
                self._ping.ping("stopped", 0, None)
            case {"Status": "exited", "ExitCode": exit_code, "Error": err_info}:
                self._ping.ping("error", exit_code, err_info)
            case _:
                raise ValueError