import random

class BehaviorPattern:
    def __init__(self, screen_width, screen_height, behavior_type="default", offset=(0, 0)):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.behavior_type = behavior_type
        self.offset = offset
        self.position = [
            random.randint(self.offset[0], screen_width),
            random.randint(self.offset[1], screen_height)
        ]
        self.speed = random.uniform(0.5, 2)

        # Dirección inicial
        self.direction = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.last_direction = self.direction

        # Contador para cambios de dirección y estados adicionales
        self.direction_change_timer = random.randint(10, 50)
        self.zigzag_step = 0  # Para movimientos de zigzag
        self.wander_timer = random.randint(20, 100)  # Para patrones de merodeo

    def update_position(self):
        """Actualiza la posición del sprite según el patrón de comportamiento."""
        if self.behavior_type == "fly":
            self._fly_behavior()
        elif self.behavior_type == "crawl":
            self._crawl_behavior()
        elif self.behavior_type == "bounce":
            self._bounce_behavior()
        elif self.behavior_type == "zigzag":
            self._zigzag_behavior()
        elif self.behavior_type == "wander":
            self._wander_behavior()
        elif self.behavior_type == "playful":
            self._playful_behavior()
        elif self.behavior_type == "run":
            self._run_behavior()

        return self.position

    # ------ BEHAVIOR PATTERNS ------ #
    
    def _fly_behavior(self):
        """Movimiento aleatorio flotando."""
        if self.direction_change_timer <= 0:
            self.direction = [random.choice([-1, 1]), random.choice([-1, 1])]
            self.direction_change_timer = random.randint(20, 60)
        else:
            self.direction_change_timer -= 1

        dx = self.direction[0] * self.speed
        dy = self.direction[1] * self.speed
        self._move(dx, dy)
    
    def _crawl_behavior(self):
        """Movimiento lento y horizontal, simulando arrastre."""
        dx = self.speed
        self.position[0] += dx
        if self.position[0] > self.screen_width:
            self.position[0] = self.offset[0]
        self.position[1] = self.screen_height - 20  # Mantener cerca del suelo
        self.last_direction = [1, 0]
    
    def _bounce_behavior(self):
        """Rebota en las paredes de la pantalla."""
        dx = self.direction[0] * self.speed
        dy = self.direction[1] * self.speed
        self._move(dx, dy)

        # Cambiar dirección al tocar los bordes
        if self.position[0] >= self.screen_width or self.position[0] <= self.offset[0]:
            self.direction[0] = -self.direction[0]
        if self.position[1] >= self.screen_height or self.position[1] <= self.offset[1]:
            self.direction[1] = -self.direction[1]
    
    def _zigzag_behavior(self):
        """Movimiento en zigzag, cambiando de dirección periódicamente."""
        if self.zigzag_step % 20 == 0:  # Cambiar dirección cada 20 pasos
            self.direction[1] = -self.direction[1]
        dx = self.speed
        dy = self.direction[1] * self.speed
        self.zigzag_step += 1
        self._move(dx, dy)
    
    def _wander_behavior(self):
        """Movimiento aleatorio lento, simulando merodeo."""
        if self.wander_timer <= 0:
            self.direction = [random.choice([-1, 1]), random.choice([-1, 1])]
            self.wander_timer = random.randint(20, 100)
        else:
            self.wander_timer -= 1

        dx = self.direction[0] * self.speed * 0.5
        dy = self.direction[1] * self.speed * 0.5
        self._move(dx, dy)
    
    def _playful_behavior(self):
        """Movimiento rápido y errático, simulando juego."""
        if random.randint(0, 10) > 8:  # Cambiar dirección al azar
            self.direction = [random.choice([-1, 1]), random.choice([-1, 1])]

        dx = self.direction[0] * self.speed * 1.5
        dy = self.direction[1] * self.speed * 1.5
        self._move(dx, dy)
    
    def _run_behavior(self):
        """Movimiento rápido en línea recta, simulando una carrera."""
        dx = self.direction[0] * self.speed * 2
        dy = self.direction[1] * self.speed * 2
        self._move(dx, dy)

        # Cambiar dirección si toca los bordes
        if self.position[0] >= self.screen_width or self.position[0] <= self.offset[0]:
            self.direction[0] = -self.direction[0]
        if self.position[1] >= self.screen_height or self.position[1] <= self.offset[1]:
            self.direction[1] = -self.direction[1]

    # ------ HELPER FUNCTIONS ------ #
    
    def _move(self, dx, dy):
        """Mueve el sprite y ajusta su posición dentro de los límites."""
        self.position[0] += dx
        self.position[1] += dy
        self.position[0] = max(self.offset[0], min(self.screen_width, self.position[0]))
        self.position[1] = max(self.offset[1], min(self.screen_height, self.position[1]))
        self.last_direction = self.direction