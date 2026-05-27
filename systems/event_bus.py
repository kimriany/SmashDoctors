class EventBus:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name, callback):
        if event_name not in self.listeners:
            self.listeners[event_name] = []

        self.listeners[event_name].append(callback)

    def emit(self, event_name, data=None):
        if data is None:
            data = {}

        for callback in self.listeners.get(event_name, []):
            callback(data)
