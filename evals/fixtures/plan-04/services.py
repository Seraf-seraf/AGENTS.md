class NotificationService:
    def __init__(self):
        self.events = []

    def send(self, event, payload):
        self.events.append((event, dict(payload)))


class Services:
    def __init__(self):
        self.notifications = NotificationService()
