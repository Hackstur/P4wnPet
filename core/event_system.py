
class EventSystem:
    """
    Sistema de eventos que permite suscribirse y publicar eventos con callbacks.
    
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

event_system = EventSystem()  # Instancia del sistema de eventos, para todos el mismo

"""
Ejemplo de uso:
    # Función que maneja el evento de registro de usuario.
    def on_user_registered(user_name):
        print(f"¡Usuario {user_name} se ha registrado exitosamente!")

    # Función que maneja el evento de error del sistema.
    def on_system_error(error_code):
        print(f"Error {error_code}: Ha ocurrido un error en el sistema.")

    # Suscribir callbacks a eventos específicos.
    event_system.subscribe("user_registered", on_user_registered)
    event_system.subscribe("system_error", on_system_error)

    # Publicar el evento 'user_registered'.
    event_system.publish("user_registered", "Juan")
    
    # Publicar el evento 'system_error'.
    event_system.publish("system_error", 500)

    # Verificar si un evento ha ocurrido.
    if event_system.has_event("user_registered"):
        print("El evento de registro de usuario ha ocurrido.")
    
    # Limpiar los eventos ocurridos.
    event_system.clear_events()
"""