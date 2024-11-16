from plugins.OLED.behaviorpattern import BehaviorPattern
from PIL import Image


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
