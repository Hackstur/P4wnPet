# Configurar el logger
from core.logger import setup_logger
logger = setup_logger(__name__)


class MenuItem:
    def __init__(self, name, value=None, options=None, options_index=0, action_select=None, submenu=None, action_update=None):
        self.name = name
        self.value = value
        #self.options = options if options is not None else []
        #self.options_index = options_index

        self.action_select = action_select  # Acción al seleccionar el ítem
        self.action_update = action_update  # Acción al actualizar el ítem
        self.submenu = submenu if submenu else []  # Submenú que puede contener otros ítems (recursivo)

    def select(self):
        """Ejecuta la acción y navega al submenú si está presente."""
        if self.action_select:
            logger.info(f"Executing action for item: {self.name}")
            self.action_select(self)  # Si hay una acción asociada, la ejecutamos
            if self.action_update:
                self.action_update(self) # para actualizar textos
            

        if self.submenu:
            # Publicar evento para entrar en el submenú
            logger.info(f"Entering submenu: {self.submenu}")
            return self.submenu

        logger.debug(f"No submenu for item: {self.name}")
        return None

    def update(self):
        """Ejecuta la acción de actualización, si existe."""
        if self.action_update:
            logger.info(f"Updating item: {self.name}")
            self.action_update(self)
        else:
            logger.warning(f"No update action for item: {self.name}")

    def next_option(self):
        """Cambia a la siguiente opción del ítem si tiene varias."""
        if self.options:
            self.options_index = (self.options_index + 1) % len(self.options)
            logger.debug(f"Next option for item {self.name}: {self.options[self.options_index]}")

    def previous_option(self):
        """Cambia a la opción anterior del ítem si tiene varias."""
        if self.options:
            self.options_index = (self.options_index - 1) % len(self.options)
            logger.debug(f"Previous option for item {self.name}: {self.options[self.options_index]}")



class Menu:
    def __init__(self, name):
        self.name = name
        self.items = []  # Lista de items del menú
        self.current_index = 0  # Índice actual para navegación
        self.menu_cur_top = 0  # variable para el cur_top

    def add_item(self, item):
        """Añadir un ítem al menú."""
        self.items.append(item)
        logger.info(f"Added item: {item.name} to menu: {self.name}")

    def update_items(self):
        """Actualizar el nombre de cada ítem en el menú."""
        for item in self.items:
            item.update()  # Llamar al método de actualización de cada ítem

    def navigate_up(self):
        """Navega hacia arriba en las opciones del menú."""
        if self.current_index > 0:
            self.current_index -= 1
            logger.info(f"Navigated up to index: {self.current_index} in menu: {self.name}")

        else:
            logger.warning("Attempted to navigate up but already at the top.")

    def navigate_down(self):
        """Navega hacia abajo en las opciones del menú."""
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            logger.info(f"Navigated down to index: {self.current_index} in menu: {self.name}")

        else:
            logger.warning("Attempted to navigate down but already at the bottom.")

    def get_current_item(self):
        """Devuelve el ítem actualmente seleccionado."""
        current_item = self.items[self.current_index]
        logger.debug(f"Current item in menu {self.name}: {current_item.name}")
        return current_item

    def navigate(self, action):
        """Permite realizar la navegación."""
        logger.debug(f"Navigating with action: {action} in menu: {self.name}")
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
        """Navegar hacia arriba en el menú actual."""
        logger.debug("Navigating up in the current menu.")
        self.current_menu.navigate_up()

    def navigate_down(self):
        """Navegar hacia abajo en el menú actual."""
        logger.debug("Navigating down in the current menu.")
        self.current_menu.navigate_down()

    def select_current_item(self):
        """Selecciona el ítem actual y navega si es un submenú o ejecuta la acción."""
        logger.info(f"Selecting current item: {self.current_menu.get_current_item().name}")
        next_menu = self.current_menu.navigate('select')
        if next_menu:  # Si devuelve un submenú, navegamos a él
            logger.info("Navegando a submenu "+next_menu.name)
            self.menu_stack.append(next_menu)
            self.current_menu = next_menu
            #if self.current_menu.current_index>self.current_menu.items:
            self.current_menu.current_index=0
            self.current_menu.menu_cur_top=0
            self.current_menu.update_items()  # Actualizar ítems del nuevo menú
            logger.info(f"Navigated to submenu: {next_menu.name}")

    def back(self, aux=None):
        """Volver al menú anterior si es posible."""
        if len(self.menu_stack) > 1:
            self.menu_stack.pop()  # Eliminar el submenú actual
            self.current_menu = self.menu_stack[-1]  # Establecer el menú anterior
            self.current_menu.current_index=0
            self.current_menu.menu_cur_top=0
            self.current_menu.update_items()  # Actualizar ítems del menú anterior
            logger.info(f"Returned to menu: {self.current_menu.name}")
        else:
            logger.warning("Attempted to go back but already at the top menu.")

menu_manager=MenuManager()