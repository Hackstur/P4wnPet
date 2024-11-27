class EventSystem:
    def __init__(self):
        self.subscribers = {}
        self.events = set()

    def subscribe(self, event_name, callback):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        if event_name in self.subscribers:
            try:
                self.subscribers[event_name].remove(callback)
                if not self.subscribers[event_name]:
                    del self.subscribers[event_name]
            except ValueError:
                pass

    def publish(self, event_name, *args, **kwargs):
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                callback(*args, **kwargs)
        self.events.add(event_name)

    def has_event(self, event_name):
        return event_name in self.events

    def clear_events(self):
        self.events.clear()


event_system = EventSystem()