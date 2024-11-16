
from core.event_system import event_system

from core.logger import setup_logger
logger = setup_logger(__name__)

class nmap:
    def __init__(self):
        self.name="nmap"
        self.author="Hackstur"
        self.description="NMAP functions and utilities"
        
    def initialize(self):
        a=1
        #event_system.subscribe("p4wn_settings_menu", self._on_settings_menu)

    def stop(self):
        a=1