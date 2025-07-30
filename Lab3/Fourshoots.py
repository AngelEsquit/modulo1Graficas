import pygame
import math
import time
from gl import Renderer, POINTS, LINES, TRIANGLES
from BMP_Writer import GenerateBMP
from objloader import OBJ
from objToModel import objToModel
from shaders import vertexShader

# --- Engine Configuration ---
VIEWPORT_WIDTH, VIEWPORT_HEIGHT = 512, 512

class App:
    def __init__(self):
        pygame.init()
        self.canvas = pygame.display.set_mode((VIEWPORT_WIDTH, VIEWPORT_HEIGHT), pygame.SCALED)
        self.main_clock = pygame.time.Clock()
        self.render_core = Renderer(self.canvas)
        self.render_core.primitiveType = TRIANGLES
        
        self.camera_shots = {
            "standard_view": {
                "position": [0, -3.8, 1.6],
                "rotation": [80, 0, 0]
            },
            "hero_shot": {
                "position": [0, -3.0, -1.2],
                "rotation": [115, 0, 0]
            },
            "vulnerable_shot": {
                "position": [0, -0.8, 3.5],
                "rotation": [18, 0, 0]
            },
            "dynamic_shot": {
                "position": [0, -3.7, 1.5],
                "rotation": [80, 0, 18]
            }
        }
        
        self.load_model()
        self.cam_yaw, self.cam_pitch, self.cam_roll = 0.0, 0.0, 0.0
        self.mouse_dragging = False
        self.last_mouse_pos = [0, 0]

    def load_model(self):
        print("\nCargando activos del modelo...")
        try:
            mesh_filepath = "models/yoshi.obj"
            tex_filepath = "textures/yoshi.png"
            
            mesh_data = OBJ(mesh_filepath)
            model_entity = objToModel(mesh_data, tex_filepath)
            model_entity.vertexShader = vertexShader
            model_entity.scale = [1.5, 1.5, 1.5]
            model_entity.rotation = [90, 180, 0]
            
            self.render_core.models.append(model_entity)
            
            if self.render_core.loadTexture(tex_filepath, id(model_entity)):
                self.render_core.activeTexture = self.render_core.textures[id(model_entity)]
                print("Textura cargada correctamente.")
            else:
                print("¡Error! La textura no se pudo cargar. Renderizando sin ella.")

        except Exception as e:
            print(f"Error crítico al cargar el modelo o sus texturas: {e}")
            pygame.quit()
            exit()

    def set_camera_from_preset(self, preset_name):
        config = self.camera_shots.get(preset_name)
        if config:
            self.render_core.cameraPos = config["position"]
            self.render_core.cameraRotation = config["rotation"]

    def export_frame(self, filename_tag, title):
        print(f"Generando imagen '{title}'...")
        self.render_core.glClear()
        self.render_core.glRender()
        pygame.display.flip()
        
        output_filename = f"render_{filename_tag}.bmp"
        GenerateBMP(output_filename, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 3, self.render_core.frameBuffer)
        print(f"Archivo guardado como {output_filename}.")
        time.sleep(0.75)

    def _get_camera_vectors(self, pitch, yaw, roll):
        yaw_rad, pitch_rad, roll_rad = math.radians(yaw), math.radians(pitch), math.radians(roll)
        forward_v = [math.cos(pitch_rad) * math.cos(yaw_rad), math.sin(pitch_rad), math.cos(pitch_rad) * math.sin(yaw_rad)]
        right_base_v = [-math.sin(yaw_rad), 0, math.cos(yaw_rad)]
        up_base_v = [-math.sin(pitch_rad) * math.cos(yaw_rad), math.cos(pitch_rad), -math.sin(pitch_rad) * math.sin(yaw_rad)]
        cos_roll, sin_roll = math.cos(roll_rad), math.sin(roll_rad)
        right_v = [right_base_v[i] * cos_roll - up_base_v[i] * sin_roll for i in range(3)]
        up_v = [right_base_v[i] * sin_roll + up_base_v[i] * cos_roll for i in range(3)]
        return forward_v, right_v, up_v

    def run_automated_sequence(self):
        print("\n--- INICIANDO CAPTURA AUTOMÁTICA DE TOMAS ---")
        
        self.set_camera_from_preset("standard_view")
        self.export_frame("medium_shot", "Toma media")
        
        self.set_camera_from_preset("hero_shot")
        self.export_frame("low_angle", "Ángulo bajo")
        
        self.set_camera_from_preset("vulnerable_shot")
        self.export_frame("high_angle", "Ángulo alto")
        
        self.set_camera_from_preset("dynamic_shot")
        self.export_frame("dutch_angle", "Ángulo holandés")
        
        print("\n--- SECUENCIA AUTOMÁTICA FINALIZADA ---\n")
        print("Esperando la interacción del usuario...")
        
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                break

    def start_interactive_mode(self):
        print("\n--- MODO DE CÁMARA INTERACTIVO ACTIVADO ---\n")
        
        move_speed = 3.0
        mouse_sens = 0.2
        
        while True:
            delta_time = self.main_clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_app()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: self.render_core.primitiveType = POINTS
                    elif event.key == pygame.K_2: self.render_core.primitiveType = LINES
                    elif event.key == pygame.K_3: self.render_core.primitiveType = TRIANGLES
                    elif event.key == pygame.K_ESCAPE: self.exit_app()
                    elif event.key == pygame.K_F1: self.export_frame("medium_shot_manual", "Manual M-Shot")
                    elif event.key == pygame.K_F2: self.export_frame("low_angle_manual", "Manual L-Angle")
                    elif event.key == pygame.K_F3: self.export_frame("high_angle_manual", "Manual H-Angle")
                    elif event.key == pygame.K_F4: self.export_frame("dutch_angle_manual", "Manual D-Angle")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.mouse_dragging = True
                        pygame.mouse.set_visible(False)
                        self.last_mouse_pos = pygame.mouse.get_pos()
                        pygame.event.set_grab(True)
                    elif event.button == 4: # Scroll Up
                        forward_v, _, _ = self._get_camera_vectors(self.cam_pitch, self.cam_yaw, self.cam_roll)
                        for i in range(3): self.render_core.cameraPos[i] += forward_v[i] * move_speed * 0.5
                    elif event.button == 5: # Scroll Down
                        forward_v, _, _ = self._get_camera_vectors(self.cam_pitch, self.cam_yaw, self.cam_roll)
                        for i in range(3): self.render_core.cameraPos[i] -= forward_v[i] * move_speed * 0.5
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.mouse_dragging = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                elif event.type == pygame.MOUSEMOTION and self.mouse_dragging:
                    current_mouse_pos = pygame.mouse.get_pos()
                    rel_x, rel_y = current_mouse_pos[0] - self.last_mouse_pos[0], current_mouse_pos[1] - self.last_mouse_pos[1]
                    self.cam_yaw -= rel_x * mouse_sens
                    self.cam_pitch = max(-89, min(89, self.cam_pitch + rel_y * mouse_sens))
                    self.last_mouse_pos = current_mouse_pos

            keys = pygame.key.get_pressed()
            forward_v, right_v, up_v = self._get_camera_vectors(self.cam_pitch, self.cam_yaw, self.cam_roll)
            
            if keys[pygame.K_w]: [self.render_core.cameraPos.__setitem__(i, self.render_core.cameraPos[i] + forward_v[i] * move_speed * delta_time) for i in range(3)]
            if keys[pygame.K_s]: [self.render_core.cameraPos.__setitem__(i, self.render_core.cameraPos[i] - forward_v[i] * move_speed * delta_time) for i in range(3)]
            if keys[pygame.K_d]: [self.render_core.cameraPos.__setitem__(i, self.render_core.cameraPos[i] + right_v[i] * move_speed * delta_time) for i in range(3)]
            if keys[pygame.K_a]: [self.render_core.cameraPos.__setitem__(i, self.render_core.cameraPos[i] - right_v[i] * move_speed * delta_time) for i in range(3)]
            if keys[pygame.K_e]: [self.render_core.cameraPos.__setitem__(i, self.render_core.cameraPos[i] + up_v[i] * move_speed * delta_time) for i in range(3)]
            if keys[pygame.K_q]: [self.render_core.cameraPos.__setitem__(i, self.render_core.cameraPos[i] - up_v[i] * move_speed * delta_time) for i in range(3)]

            self.render_core.cameraRotation = [self.cam_pitch, self.cam_yaw, self.cam_roll]

            self.render_core.glClear()
            self.render_core.glRender()
            pygame.display.flip()

    def exit_app(self):
        GenerateBMP("interactive_final_capture.bmp", VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 3, self.render_core.frameBuffer)
        pygame.quit()
        print("\n¡Gracias por usar la aplicación! Saliendo del programa.")
        exit()

if __name__ == "__main__":
    app_instance = App()
    app_instance.run_automated_sequence()
    app_instance.start_interactive_mode()