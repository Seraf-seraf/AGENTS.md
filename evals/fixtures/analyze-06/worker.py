class Worker:
    def __init__(self):
        self.state = "idle"
        self.device_owned = False

    def start(self):
        if self.state != "idle":
            raise RuntimeError("busy")
        self.device_owned = True
        self.state = "running"

    def cancel(self):
        self.state = "idle"

    def cleanup_complete(self):
        self.device_owned = False
        self.state = "idle"

    def status(self):
        return {"state": self.state, "device_owned": self.device_owned}
