import pygame
from datetime import datetime
from BMP_Writer import GenerateBMP
from shaders_registry import handle_shader_key
from config import MOVE_SPEED, ROTATION_SPEED, MOUSE_SENSITIVITY, ZOOM_SPEED_FACTOR, SCREEN_DIMENSIONS
from MathLib import RotationMatrix
import math

class InputController:
    """Encapsula toda la lógica de entrada (eventos y teclas mantenidas)."""
    def __init__(self, renderer, camera, model_manager):
        self.renderer = renderer
        self.camera = camera
        self.model_manager = model_manager

        # Parámetros dinámicos
        self.move_speed = MOVE_SPEED
        self.rotation_speed = ROTATION_SPEED
        self.mouse_sensitivity = MOUSE_SENSITIVITY
        self.zoom_factor = ZOOM_SPEED_FACTOR

        # Estado de mouse / free-look
        self.mouse_dragging = False
        self.last_mouse_pos = [0, 0]

        # Cache de ángulos locales (sincronizados con camera)
        self.yaw_angle = camera.yaw
        self.pitch_angle = camera.pitch
        self.roll_angle = camera.roll

        self.running = True

    # --- Utilidades ---
    def _apply_camera_angles(self):
        self.camera.rotation[0] = self.pitch_angle
        self.camera.rotation[1] = self.yaw_angle
        self.camera.rotation[2] = self.roll_angle

    def _zoom(self, direction):
        # direction: +1 acercar, -1 alejar
        forward, _, _ = self._compute_forward_vectors()
        zoom_speed = self.move_speed * self.zoom_factor
        self.renderer.cameraPos[0] += forward[0] * zoom_speed * direction
        self.renderer.cameraPos[1] += forward[1] * zoom_speed * direction
        self.renderer.cameraPos[2] += forward[2] * zoom_speed * direction

    def _compute_forward_vectors(self):
        # Replica de obtener_vectores_camara pero usando estado local
        R = RotationMatrix(self.pitch_angle, self.yaw_angle, self.roll_angle)
        r = [[R[i, j] for j in range(3)] for i in range(3)]
        base_forward = [0, 0, -1]
        base_right = [1, 0, 0]
        base_up = [0, 1, 0]

        def transform(v):
            return [
                r[0][0]*v[0] + r[0][1]*v[1] + r[0][2]*v[2],
                r[1][0]*v[0] + r[1][1]*v[1] + r[1][2]*v[2],
                r[2][0]*v[0] + r[2][1]*v[1] + r[2][2]*v[2]
            ]

        def normalize(v):
            l = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]) or 1
            return [v[0]/l, v[1]/l, v[2]/l]

        forward = normalize(transform(base_forward))
        right = normalize(transform(base_right))
        up = normalize(transform(base_up))
        return forward, right, up

    # --- Procesamiento de eventos discretos ---
    def process_events(self, delta_time):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.model_manager.prev()
                    else:
                        self.model_manager.next()
                    if self.model_manager.active:
                        active = self.model_manager.active
                        name = getattr(active, 'name', None)
                        if name:
                            print(f"Modelo activo -> {name} (index {self.model_manager.active_index})")
                        else:
                            print(f"Modelo activo -> index {self.model_manager.active_index} id={id(active)}")
                elif event.key == pygame.K_1:
                    self.renderer.primitiveType = 0
                elif event.key == pygame.K_2:
                    self.renderer.primitiveType = 1
                elif event.key == pygame.K_3:
                    self.renderer.primitiveType = 2
                    self.renderer.activeTexture = None
                    if self.model_manager.active:
                        self.model_manager.active.fragmentShader = None
                    self.renderer.forceNoTexture = True
                    print("Primitiva: Triángulos (modelo sin textura ni fragment shader)")
                else:
                    # Shaders dinámicos (toggle / cadena)
                    if handle_shader_key(event.key, self.model_manager.active, self.renderer):
                        continue
                    # Limpiar cadena fragment con tecla C
                    if event.key == pygame.K_c and self.model_manager.active:
                        self.model_manager.active.clear_fragment_chain()
                        print("Cadena fragment limpia.")
                        continue
                if event.key == pygame.K_RETURN:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    GenerateBMP(f"salida_{timestamp}.bmp", *SCREEN_DIMENSIONS, 3, self.renderer.frameBuffer)
                    print(f"Captura de pantalla guardada como salida_{timestamp}.bmp")
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_dragging = True
                    pygame.mouse.set_visible(False)
                    self.last_mouse_pos = pygame.mouse.get_pos()
                    pygame.event.set_grab(True)
                elif event.button == 4:  # scroll up
                    self._zoom(+1)
                elif event.button == 5:  # scroll down
                    self._zoom(-1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_dragging = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
            elif event.type == pygame.MOUSEMOTION and self.mouse_dragging:
                current_mouse_pos = pygame.mouse.get_pos()
                rel_x = current_mouse_pos[0] - self.last_mouse_pos[0]
                rel_y = current_mouse_pos[1] - self.last_mouse_pos[1]
                self.yaw_angle -= rel_x * self.mouse_sensitivity
                self.pitch_angle -= rel_y * self.mouse_sensitivity
                self.pitch_angle = max(-89, min(89, self.pitch_angle))
                if self.yaw_angle > 180: self.yaw_angle -= 360
                elif self.yaw_angle < -180: self.yaw_angle += 360
                self.last_mouse_pos = current_mouse_pos
        return self.running

    # --- Teclas mantenidas (movimiento continuo) ---
    def update_held_keys(self, delta_time):
        keys = pygame.key.get_pressed()

        # 1. Rotaciones con teclas (modifican ángulos locales acumulados)
        if keys[pygame.K_a]:
            self.yaw_angle += self.rotation_speed * delta_time
        if keys[pygame.K_d]:
            self.yaw_angle -= self.rotation_speed * delta_time
        if keys[pygame.K_q]:
            self.roll_angle += self.rotation_speed * delta_time
        if keys[pygame.K_e]:
            self.roll_angle -= self.rotation_speed * delta_time
        if keys[pygame.K_r]:
            self.pitch_angle += self.rotation_speed * delta_time
        if keys[pygame.K_f]:
            self.pitch_angle -= self.rotation_speed * delta_time

        # 2. Aplicar y normalizar
        self._apply_camera_angles()
        self.camera.normalize_angles()
        self.pitch_angle, self.yaw_angle, self.roll_angle = self.camera.rotation

        # 3. Movimiento relativo a la orientación actual
        if keys[pygame.K_w]:
            self.camera.move_local(up=self.move_speed * delta_time)
        if keys[pygame.K_s]:
            self.camera.move_local(up=-self.move_speed * delta_time)
        if keys[pygame.K_UP]:
            self.camera.move_local(forward=self.move_speed * delta_time)
        if keys[pygame.K_DOWN]:
            self.camera.move_local(forward=-self.move_speed * delta_time)
        if keys[pygame.K_LEFT]:
            self.camera.move_local(right=-self.move_speed * delta_time)
        if keys[pygame.K_RIGHT]:
            self.camera.move_local(right=self.move_speed * delta_time)

        # 4. Sincronizar con renderer
        self.camera.sync_renderer(self.renderer)
