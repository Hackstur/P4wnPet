import subprocess
import requests
from core.menu_manager import Menu, MenuItem
from core.menu import update_filesearch_menu
from core.functions import run_command
from core.config import config
from core.event_system import event_system
import os

from core.logger import setup_logger
logger = setup_logger(__name__)


class JokerShell:
    def __init__(self):
        self.name="JokerShell"
        self.author="Hackstur"
        self.description="Launcher for JokerShell scripts, Pranks in powershell."
        #self.p4wnpet = None
        self.active = False  # Estado del módulo


    def initialize(self):
        # CHECK IF EXISTS
        if not self.check_jokershell_directory():
            self.download_jokershell()

        # check local version
        if self.check_jokershell_update_available():
            logger.info("[JOKERSHELL] UPDATE AVAILABLE")
        else:
            logger.info("[JOKERSHELL] YOU HAVE THE LAST VERSION")
        
        # SUBSCRIBE EVENTS
        event_system.subscribe("p4wn_hidscripts_menu", self._on_hidscripts_menu) 
        event_system.subscribe("p4wn_settings_menu", self._on_settings_menu)

    def stop(self):
        event_system.unsubscribe("p4wn_hidscripts_menu", self._on_hidscripts_menu)
        event_system.unsubscribe("p4wn_hidscripts_menu", self._on_settings_menu)
        

    def _on_settings_menu(self, menuitem):
        submenu=Menu("JOKERSHELL SETTINGS")
        submenu.add_item(MenuItem(
            name="DEPLOY: TYPE",    #TYPE / SHARED / UMS / WEBSRV / GITHUB (por ejemplo)
        ))
        menuitem.submenu.add_item(MenuItem(
            name="JOKERSHELL SETTINGS",
            submenu=submenu,
        ))

    def _on_hidscripts_menu(self, menuitem):
        menuitem.submenu.add_item(MenuItem(
            name="JOKERSHELL SCRIPTS",
            submenu=Menu("JOKERSHELL SCRIPTS"),
            action_select=lambda item: (
                update_filesearch_menu(menuitem=item, base_path="plugins/JokerShell/", file_extension=".ps1", action_for_file=self.run_jokershell_script)
        )))
        


    # TO-DO: No blocking launcher in processmanager for large running commands
    # TO-DO: Alternative script deploy for faster p4wn (access in shared folder/ums mount/webserver/etc)
    def run_jokershell_script(self, path):
        logger.info(f"Lanzando script: {path}")
        _, extension = os.path.splitext(path)

        if extension == ".ps1":
            # Configuración inicial de HID
            run_command(f"P4wnP1_cli hid run -c \"layout('{config.data.hid.keymap}'); typingSpeed({config.data.hid.type_speed});\"")

            # Abrir PowerShell con GUI + R (ejecutar)
            run_command("P4wnP1_cli hid run -c \"press('GUI r'); delay(500); type('powershell\\n'); delay(1200);\"")

            # Leer y ejecutar el archivo PowerShell línea por línea
            try:
                with open(path, 'r') as script_file:
                    for line in script_file:
                        if line.strip():  # Si la línea no está vacía
                            # Escapar comillas simples, dobles y $ en el código PowerShell
                            line = line.replace("'", "\\'").replace('"', '\\"').replace('$','\$')
                            # Enviar cada línea de manera individual
                            run_command(f"P4wnP1_cli hid  run -c \"type('{line.strip()}');\"")
                            

                    # Enviar ENTER y salir de PowerShell al final
                    run_command("P4wnP1_cli hid run -c \"press('ENTER'); delay(500); type('exit\\n');\"")

            except Exception as e:
                logger.error(f"Error al leer el script de PowerShell: {e}")


    
    def check_jokershell_directory(self):
        """
        Verifica si el directorio de JokerShell existe en la carpeta de plugins.
        
        Returns:
            bool: True si el directorio existe, False en caso contrario.
        """
        path = "plugins/JokerShell"
        if os.path.isdir(path):
            logger.info("El directorio JokerShell existe.")
            return True
        else:
            logger.warning("El directorio JokerShell no existe.")
            return False

    def get_local_jokershell_version(self):
        """
        Obtiene la versión actual del repositorio local de JokerShell.
        Si no es un repositorio Git válido, retorna None.

        Returns:
            str: Hash o versión local del repositorio JokerShell, o None si no está disponible.
        """
        try:
            # Obtener el último commit hash de la copia local
            result = subprocess.check_output(
                ["git", "-C", "plugins/JokerShell", "rev-parse", "HEAD"],
                stderr=subprocess.STDOUT
            ).strip().decode('utf-8')
            logger.info(f"Versión local de JokerShell: {result}")
            return result
        except subprocess.CalledProcessError:
            logger.error("No se pudo obtener la versión local de JokerShell. ¿Está el directorio en Git?")
            return None

    def get_remote_jokershell_version(self):
        """
        Obtiene el último commit hash de la rama principal (main) del repositorio de JokerShell en GitHub.

        Returns:
            str: Hash del último commit remoto del repositorio JokerShell, o None en caso de error.
        """
        url = "https://api.github.com/repos/Hackstur/JokerShell/commits/main"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                commit_hash = response.json()['sha']
                logger.info(f"Versión remota de JokerShell: {commit_hash}")
                return commit_hash
            else:
                logger.error(f"Error al obtener la versión remota de JokerShell: {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error en la solicitud a GitHub: {e}")
            return None

    def check_jokershell_update_available(self):
        """
        Verifica si hay una actualización disponible para JokerShell comparando las versiones local y remota.
        
        Returns:
            bool: True si hay una actualización disponible, False en caso contrario.
        """
        local_version = self.get_local_jokershell_version()
        remote_version = self.get_remote_jokershell_version()

        if local_version and remote_version:
            if local_version != remote_version:
                logger.info("Hay una actualización disponible para JokerShell.")
                return True
            else:
                logger.info("JokerShell está actualizado.")
                return False
        else:
            logger.warning("No se pudo verificar la versión de JokerShell.")
            return False
        
    def download_jokershell(self):
        """
        Descarga el repositorio de JokerShell en la carpeta de plugins.
        """
        url = "https://github.com/Hackstur/JokerShell.git"
        path = "plugins/JokerShell"
        try:
            logger.info(f"Clonando JokerShell en {path}...")
            subprocess.check_call(["git", "clone", url, path])
            logger.info("JokerShell ha sido descargado correctamente.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error al clonar JokerShell: {e}")
