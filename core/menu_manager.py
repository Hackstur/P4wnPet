import os
import re
import threading
import time
from core.logger import setup_logger
logger = setup_logger(__name__)


class MenuItem:
    def __init__(self, name, value=None, options=None, options_index=0, action_select=None, submenu=None, action_update=None):
        self.name = name
        self.value = value
        self.action_select = action_select  # Acción al seleccionar el ítem
        self.action_update = action_update  # Acción al actualizar el ítem

    def select(self):
        if self.action_select:
            self.action_select(self)  # Si hay una acción asociada, la ejecutamos
            if self.action_update:
                self.action_update(self) # para actualizar textos
        return None

    def update(self):
        if self.action_update:
            self.action_update(self)


class SelectorItem(MenuItem):
    def __init__(self, name, options=None, action_select=None, selected_index=-1):
        super().__init__(name, action_select=action_select)
        self.options = options if options else []  # Lista de opciones disponibles
        self.selected_index = selected_index  # Índice de la opción seleccionada
        self.update_name()  # Actualizar el nombre inicial con la opción seleccionada
        self.submenu = self.create_options_menu()  # Crear un menú con las opciones
        

    def select(self):
        if self.submenu:
            return self.submenu

    def update_name(self):
        if self.selected_index==-1:
            self.name = f"{self.name.split(':')[0]}: NOT SELECTED"
        else:
            if self.options:
                logger.info(self.options)
                self.name = f"{self.name.split(':')[0]}: {self.options[self.selected_index]}"
            else:
                self.name = f"{self.name.split(':')[0]}: NOT OPTIONS"

    def create_options_menu(self):
        options_menu = Menu(name=f"Opciones de {self.name}")
        for idx, opt in enumerate(self.options):
            options_menu.add_item(MenuItem(
                name=opt,
                action_select=self.select_option(idx)  # Acción para seleccionar esta opción
            ))
        return options_menu

    def select_option(self, index):
        def action(item):
            self.selected_index = index
            self.update_name()  # Actualiza el nombre después de seleccionar la opción

            if self.action_select:
                self.action_select(self)  # Si hay una acción asociada, la ejecutamos

            menu_manager.back()

        return action

    def list_options(self):
        return self.submenu

    def __str__(self):
        return f"SelectorItem: {self.name} (opciones: {len(self.options)})"


class SubmenuItem(MenuItem):
    def __init__(self, name, submenu=None, action_select=None, action_update=None):
        # Asegúrate de que si el submenú no se pasa, se cree un submenú vacío con el nombre adecuado.
        self.submenu = submenu if submenu else Menu(name)
        super().__init__(name, action_select=action_select, action_update=action_update)

    def select(self):
        # Verificar que el submenú tiene ítems antes de intentar navegar.
        # Disparamos la accion select antes (asi se podran hacer dinamicos)
        if self.action_select:
            self.action_select(self)

        if self.submenu.items:
            return self.submenu  # Si tiene ítems, devolvemos el submenú.
        else:
            logger.warning(f"Submenu '{self.name}' is empty.")
            return None


class SwitchItem(MenuItem):
    def __init__(self, name, action_select=None, action_update=None, state=False, labels=("OFF", "ON")):
        self.state = state  # Estado inicial del switch.
        self.labels = labels  # Etiquetas para los estados.
        super().__init__(name, action_select=action_select, action_update=action_update)
        self.update_name()  # Actualiza el nombre para reflejar el estado inicial.

    def toggle(self):
        self.state = not self.state  # Cambia entre True y False.
        self.update_name()  # Actualiza el nombre.

    def update_name(self):
        state_label = self.labels[1] if self.state else self.labels[0]
        self.name = f"{self.name.split(':')[0]}: {state_label}"

    def select(self):
        self.toggle()  # Alterna el estado.
        if self.action_select:
            self.action_select(self)  # Ejecuta la acción asociada.
        if self.action_update:
            self.action_update(self)  # Actualiza dinámicamente si es necesario.

    def set_labels(self, off_label, on_label):
        self.labels = (off_label, on_label)
        self.update_name()  # Actualiza el nombre para reflejar las nuevas etiquetas.

    def __str__(self):
        return f"SwitchItem: {self.name} (Estado: {'ON' if self.state else 'OFF'})"
    

    
class LogMonitorItem(SubmenuItem):
    def __init__(self, name, log_file=None, max_displayed_logs=100, update_interval=1, filters=None):
        super().__init__(name, submenu=Menu(name=f"Log Monitor: {name}"))
        self.logs = []  # Lista para almacenar todos los mensajes de log
        self.max_displayed_logs = max_displayed_logs  # Límite de logs visibles en el menú
        self.auto_scroll = True  # Habilitar/deshabilitar autoscroll
        self.log_file = log_file  # Ruta al fichero de logs (puede ser None)
        self.update_interval = update_interval  # Intervalo en segundos para comprobar nuevos logs
        self.filters = filters if filters else []  # Lista de filtros (tuplas de regex y reemplazo)
        self.last_read_position = 0  # Inicializamos la posición de lectura al principio del archivo

        if self.log_file and os.path.exists(self.log_file):
            self._load_logs_from_file()  # Cargar logs desde el fichero, si existe

        self._start_log_update_thread()  # Iniciar el hilo para actualizar los logs automáticamente

    def _start_log_update_thread(self):
        """Inicia un hilo que actualiza los logs automáticamente."""
        self.thread = threading.Thread(target=self._auto_update_logs)
        self.thread.daemon = True  # El hilo se cierra cuando el programa termina
        self.thread.start()

    def _auto_update_logs(self):
        """Revisa el archivo de logs a intervalos regulares y actualiza los logs en el menú."""
        while True:
            time.sleep(self.update_interval)  # Espera el intervalo antes de verificar el archivo
            if self.log_file and os.path.exists(self.log_file):
                self._load_new_logs_from_file()  # Cargar solo los logs nuevos
                self._update_displayed_logs()  # Actualiza el menú con los logs

    def _apply_filters(self, log_message):
        """Aplica los filtros de reemplazo a un mensaje de log."""
        original_message = log_message
        for pattern, replacement in self.filters:
            log_message = re.sub(pattern, replacement, log_message)
        # Agregar debug para ver los cambios
        if original_message != log_message:
            logger.info(f"Original: {original_message} -> Filtrado: {log_message}")
        return log_message

    def _load_logs_from_file(self):
        """Carga los logs desde el fichero al iniciar o cuando se detecta que el fichero se ha creado."""
        if self.log_file and os.path.exists(self.log_file):
            with open(self.log_file, 'r') as file:
                self.logs = []  # Reinicia los logs cuando se carga desde el archivo por primera vez
                for line in file:
                    log_message = line.strip()
                    log_message = self._apply_filters(log_message)  # Aplica los filtros
                    self.logs.append(log_message)
            logger.info(f"Loaded logs from {self.log_file}.")
            self._update_displayed_logs()
            self.update_name()  # Actualiza el nombre después de cargar los logs

    def _load_new_logs_from_file(self):
        """Carga solo los logs nuevos desde la última posición leída."""
        if self.log_file and os.path.exists(self.log_file):
            with open(self.log_file, 'r') as file:
                # Mover el puntero al final de los logs ya leídos
                file.seek(self.last_read_position)

                new_logs = []
                for line in file:
                    log_message = line.strip()
                    log_message = self._apply_filters(log_message)  # Aplica los filtros
                    new_logs.append(log_message)

                if new_logs:
                    # Agregar solo los nuevos logs a los existentes
                    self.logs.extend(new_logs)
                    self.last_read_position = file.tell()  # Actualizar la posición de lectura

    def _update_displayed_logs(self):
        """
        Actualiza los ítems en el submenú para mostrar solo los últimos N logs.
        """
        displayed_logs = self.logs[-self.max_displayed_logs:]  # Últimos N logs
        self.submenu.items.clear()  # Limpia el menú actual
        for log in displayed_logs:
            self.submenu.add_item(MenuItem(name=log))

    def update_name(self):
        """Actualiza el nombre del item para reflejar la cantidad de logs cargados."""
        log_count = len(self.logs)
        self.name = f"{self.name.split(':')[0]}: {log_count}"

    def toggle_autoscroll(self):
        """Alterna el estado de autoscroll."""
        self.auto_scroll = not self.auto_scroll

    def select(self):
        """Cuando seleccionas este ítem, abre el submenú de logs."""
        # Recargar los logs si el archivo fue creado o actualizado mientras tanto
        if self.log_file and os.path.exists(self.log_file):
            self._load_new_logs_from_file()
        self._update_displayed_logs()
        return self.submenu

    def update(self):
        self._update_displayed_logs()

    def clear_logs(self):
        """Limpia todos los logs del monitor en memoria."""
        self.logs.clear()
        self.submenu.items.clear()  # Limpia los ítems del menú
        self.update_name()  # Actualiza el nombre después de limpiar los logs




class Separator(MenuItem):
    def __init__(self, name="Separator"):
        super().__init__(name)
    
    def __str__(self):
        return "--------------------"


class Menu:
    def __init__(self, name):
        self.name = name
        self.items = []  # Lista de items del menú
        self.current_index = 0  # Índice actual para navegación
        self.menu_cur_top = 0  # variable para el cur_top

    def add_item(self, item):
        self.items.append(item)

    def update_items(self):
        for item in self.items:
            item.update()  # Llamar al método de actualización de cada ítem

    def navigate_up(self):
        if self.current_index > 0:
            self.current_index -= 1

        else:
            logger.warning("Attempted to navigate up but already at the top.")

    def navigate_down(self):
        if self.current_index < len(self.items) - 1:
            self.current_index += 1

        else:
            logger.warning("Attempted to navigate down but already at the bottom.")

    def get_current_item(self):
        current_item = self.items[self.current_index]
        return current_item

    def navigate(self, action):
        if action == 'up':
            self.navigate_up()
        elif action == 'down':
            self.navigate_down()
        elif action == 'select':
            selected_item = self.get_current_item()
            return selected_item.select()
        return None


class MenuManager:
    def __init__(self):
        self.menu_stack = []  # Pila de menús para navegar entre submenús
        self.current_menu = None  # Menú actual

    def set_menu(self, menu):
        """Establece el menú actual y actualiza los ítems."""
        self.current_menu = menu
        self.menu_stack = [menu]  # Reinicia la pila con el menú principal
        self.current_menu.update_items()  # Actualiza los ítems del menú
        logger.info(f"Menu set to: {menu.name}")

    def navigate_up(self):
        self.current_menu.navigate_up()

    def navigate_down(self):
        self.current_menu.navigate_down()

    def select_current_item(self):
        logger.info(f"Selecting current item: {self.current_menu.get_current_item().name}")
        next_menu = self.current_menu.navigate('select')
        if next_menu:  # Si devuelve un submenú, navegamos a él
            self.menu_stack.append(next_menu)
            self.current_menu = next_menu
            #if self.current_menu.current_index>self.current_menu.items:
            self.current_menu.current_index=0
            self.current_menu.menu_cur_top=0
            self.current_menu.update_items()  # Actualizar ítems del nuevo menú

    def back(self, aux=None):
        if len(self.menu_stack) > 1:
            self.menu_stack.pop()  # Eliminar el submenú actual
            self.current_menu = self.menu_stack[-1]  # Establecer el menú anterior
            self.current_menu.current_index=0
            self.current_menu.menu_cur_top=0
            self.current_menu.update_items()  # Actualizar ítems del menú anterior
        else:
            logger.warning("Attempted to go back but already at the top menu.")


menu_manager=MenuManager()