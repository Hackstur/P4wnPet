class EventSystem:
    """
    Sistema de eventos que permite suscribirse, desuscribirse y publicar eventos con callbacks.
    
    Attributes:
        subscribers (dict): Un diccionario que mapea nombres de eventos a listas de callbacks asociados.
        events (set): Un conjunto que almacena los eventos que ya han sido publicados.
    """

    def __init__(self):
        """
        Inicializa el sistema de eventos con un diccionario vacío de suscriptores y un conjunto vacío de eventos ocurridos.
        """
        self.subscribers = {}
        self.events = set()

    def subscribe(self, event_name, callback):
        """
        Registra un callback para que sea llamado cuando se publique un evento específico.
        
        Args:
            event_name (str): Nombre del evento al que se desea suscribir el callback.
            callback (function): Función que será ejecutada cuando el evento ocurra.
        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        """
        Elimina un callback de la lista de suscriptores de un evento específico.
        
        Args:
            event_name (str): Nombre del evento del que se desea desuscribir el callback.
            callback (function): Función que se desea desuscribir del evento.
        """
        if event_name in self.subscribers:
            try:
                self.subscribers[event_name].remove(callback)
                # Elimina la entrada si la lista de suscriptores está vacía
                if not self.subscribers[event_name]:
                    del self.subscribers[event_name]
            except ValueError:
                # El callback no está en la lista de suscriptores
                pass

    def publish(self, event_name, *args, **kwargs):
        """
        Publica un evento y ejecuta todos los callbacks suscritos a ese evento, si existen.
        
        Args:
            event_name (str): Nombre del evento que se desea publicar.
            *args: Argumentos posicionales que se pasarán a los callbacks suscritos.
            **kwargs: Argumentos clave que se pasarán a los callbacks suscritos.
        """
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                callback(*args, **kwargs)
        self.events.add(event_name)

    def has_event(self, event_name):
        """
        Verifica si un evento ha sido publicado.
        
        Args:
            event_name (str): Nombre del evento que se desea verificar.
        
        Returns:
            bool: True si el evento ha ocurrido, False de lo contrario.
        """
        return event_name in self.events

    def clear_events(self):
        """
        Elimina todos los eventos registrados como ocurridos, reiniciando el sistema de eventos.
        """
        self.events.clear()

# Ejemplo de uso de unsubscribe
event_system = EventSystem()  # Instancia del sistema de eventos, para todos el mismo