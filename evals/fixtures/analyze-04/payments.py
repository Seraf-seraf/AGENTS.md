class Gateway:
    def __init__(self):
        self.records = {}
        self.lose_next_reply = False

    def charge(self, request_id, amount):
        if request_id not in self.records:
            self.records[request_id] = {"id": request_id, "amount": amount}
        if self.lose_next_reply:
            self.lose_next_reply = False
            raise TimeoutError("reply lost")
        return self.records[request_id]

    def lookup(self, request_id):
        return self.records.get(request_id)


def pay(gateway, new_id, amount):
    try:
        return gateway.charge(new_id(), amount)
    except TimeoutError:
        return gateway.charge(new_id(), amount)
