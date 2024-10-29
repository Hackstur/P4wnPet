import random
from PIL import Image


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

        # Dirección inicial y última dirección utilizada
        self.direction = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.last_direction = self.direction  # Para registrar la última dirección

        # Contador para cambiar de dirección en fly
        self.direction_change_timer = random.randint(10, 50)

    def update_position(self):
        """Actualiza la posición del sprite según el patrón de comportamiento."""
        if self.behavior_type == "fly":
            if self.direction_change_timer <= 0:
                self.direction = [random.choice([-1, 1]), random.choice([-1, 1])]
                self.direction_change_timer = random.randint(20, 60)
            else:
                self.direction_change_timer -= 1

            dx = self.direction[0] * self.speed
            dy = self.direction[1] * self.speed
            self.position[0] += dx
            self.position[1] += dy
            self.position[0] = max(self.offset[0], min(self.screen_width, self.position[0]))
            self.position[1] = max(self.offset[1], min(self.screen_height, self.position[1]))

            # Actualizar la última dirección tomada
            self.last_direction = self.direction

        elif self.behavior_type == "crawl":
            dx = self.speed
            self.position[0] += dx
            if self.position[0] > self.screen_width:
                self.position[0] = self.offset[0]
            self.position[1] = self.screen_height - 20
            # La última dirección en 'crawl' sería siempre hacia la derecha.
            self.last_direction = [1, 0]

        elif self.behavior_type == "bounce":
            # Actualizamos la posición con la dirección actual
            self.position[0] += self.direction[0] * self.speed
            self.position[1] += self.direction[1] * self.speed
            
            # Comprobar límites para el rebote
            if self.position[0] >= self.screen_width or self.position[0] <= self.offset[0]:
                self.direction[0] = -self.direction[0]  # Cambiar dirección horizontal
                self.position[0] = max(self.offset[0], min(self.screen_width, self.position[0]))  # Ajustar posición

            if self.position[1] >= self.screen_height or self.position[1] <= self.offset[1]:
                self.direction[1] = -self.direction[1]  # Cambiar dirección vertical
                self.position[1] = max(self.offset[1], min(self.screen_height, self.position[1]))  # Ajustar posición

            # Actualizar la última dirección en el rebote
            self.last_direction = self.direction

        return self.position


class Sprite:
    def __init__(self, image_file, sprite_width, sprite_height, positions, frame_duration=10, columns=1, behavior_type="default", screen_width=64, screen_height=64, offset=(0, 0)):
        """
        Inicializa el sprite desde un archivo de imagen con varias filas y columnas de fotogramas.

        Args:
            image_file (str): Ruta del archivo de imagen de sprite.
            sprite_width (int): Ancho de cada fotograma del sprite.
            sprite_height (int): Alto de cada fotograma del sprite.
            positions (dict): Diccionario con las animaciones (nombre: (fila, índices de frames)).
            frame_duration (int): Duración de cada fotograma en ticks.
            columns (int): Número de columnas en la hoja de sprites.
            behavior_type (str): Tipo de comportamiento ("fly", "crawl", etc.).
            screen_width (int): Ancho de la pantalla.
            screen_height (int): Alto de la pantalla.
            offset (tuple): Desplazamiento para el marco de movimiento.
        """
        self.sprite_sheet = Image.open(image_file)
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.positions = positions  # Ejemplo: {'stay_normal': (0, [0, 1, 2, 3]), 'walk_right_normal': (1, [0, 1, 2, 3])}
        self.current_animation = None
        self.current_frame = 0
        self.frame_counter = 0
        self.frame_duration = frame_duration
        self.columns = columns  # Número de columnas en el sprite sheet
        self.offset = offset  # Desplazamiento del marco de movimiento
        
        # Crear el patrón de comportamiento con el marco desplazado
        self.behavior = BehaviorPattern(screen_width, screen_height, behavior_type, offset=offset)
        # Posición inicial de la mascota en el marco desplazado
        self.position = [offset[0], offset[1]]

    def set_animation(self, animation_name):
        """Establece la animación actual a una fila específica de fotogramas."""
        if animation_name in self.positions:
            self.current_animation = self.positions[animation_name]
            self.current_frame = 0
            self.frame_counter = 0
        else:
            raise ValueError(f"Animación '{animation_name}' no encontrada")

    def update(self):
        """Actualiza el sprite para el siguiente fotograma y su posición."""
        if self.current_animation is None:
            return

        # Actualización de fotogramas
        self.frame_counter += 1
        if self.frame_counter >= self.frame_duration:
            self.frame_counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.current_animation[1])
        
        # Actualizar la posición según el patrón de comportamiento
        self.position = self.behavior.update_position()

        # Cambiar la animación según la dirección
        direction = self.behavior.last_direction
        if direction == "right":
            self.set_animation("walk_right_normal")
        elif direction == "left":
            self.set_animation("walk_left_normal")
        elif direction == "up":
            self.set_animation("walk_right_normal")
        elif direction == "down":
            self.set_animation("walk_left_normal")
        else:
            self.set_animation("stay_normal")

    def draw(self, image):
        """
        Dibuja el sprite en la posición actual.

        Args:
            image (PIL.Image): La imagen en la que se dibujará el sprite.
        """
        if self.current_animation is not None:
            row, frame_indices = self.current_animation
            frame_index = frame_indices[self.current_frame]
            x = (frame_index % self.columns) * self.sprite_width
            y = row * self.sprite_height  # La fila define el desplazamiento en y para la animación
            
            # Extraer y dibujar el fotograma actual en la posición con desplazamiento
            frame = self.sprite_sheet.crop((x, y, x + self.sprite_width, y + self.sprite_height))
            image.paste(frame, (int(self.position[0]), int(self.position[1])), frame)
