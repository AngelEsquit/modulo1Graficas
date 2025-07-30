import pygame
from gl import Renderer, POINTS, LINES, TRIANGLES
from BMP_Writer import GenerateBMP
from objloader import OBJ
from objToModel import objToModel
from shaders import vertexShader
import math
from datetime import datetime

# --- Importamos las matrices de rasterización ---
from MathLib import ViewMatrix, ProjectionMatrix, ViewportMatrix

# --- Configuración global del motor ---
SCREEN_DIMENSIONS = (512, 512)
CAMERA_DISTANCE_START = 10
MODEL_SCALE = 2

# Parámetros de la matriz de proyección
FOV = 60
NEAR_PLANE = 0.1
FAR_PLANE = 100

def inicializar_entorno():
    """Configura Pygame y el motor de renderizado."""
    pygame.init()
    canvas = pygame.display.set_mode(SCREEN_DIMENSIONS, pygame.SCALED)
    time_clock = pygame.time.Clock()
    pygame.mouse.set_visible(True)
    return canvas, time_clock

def cargar_activo(filepath, texpath):
    """Carga un modelo OBJ con su textura y lo prepara para el renderizado."""
    try:
        mesh_data = OBJ(filepath)
        model_entity = objToModel(mesh_data, texpath)
        model_entity.vertexShader = vertexShader
        model_entity.scale = [MODEL_SCALE] * 3
        model_entity.rotation = [0, 180, 0]
        model_entity.position = [0, 1, 1]
        
        print(f"Éxito: Modelo '{filepath}' cargado con {len(mesh_data.vertices)} vértices y {len(mesh_data.faces)} caras.")
        return model_entity
        
    except Exception as e:
        print(f"Error fatal: Fallo al cargar el modelo o la textura: {e}")
        pygame.quit()
        exit()

def obtener_vectores_camara(yaw, pitch, roll):
    """Calcula los ejes de la cámara (adelante, derecha, arriba) desde ángulos de Euler."""
    yaw_rad, pitch_rad, roll_rad = map(math.radians, [yaw, pitch, roll])
    
    forward_vector = [
        math.cos(pitch_rad) * math.cos(yaw_rad),
        math.sin(pitch_rad),
        math.cos(pitch_rad) * math.sin(yaw_rad)
    ]
    
    right_base = [-math.sin(yaw_rad), 0, math.cos(yaw_rad)]
    up_base = [-math.sin(pitch_rad) * math.cos(yaw_rad), math.cos(pitch_rad), -math.sin(pitch_rad) * math.sin(yaw_rad)]
    
    cos_roll, sin_roll = math.cos(roll_rad), math.sin(roll_rad)
    
    right_vector = [
        right_base[i] * cos_roll - up_base[i] * sin_roll for i in range(3)
    ]
    up_vector = [
        right_base[i] * sin_roll + up_base[i] * cos_roll for i in range(3)
    ]
    
    return forward_vector, right_vector, up_vector

def actualizar_orientacion_camara(motor, yaw, pitch, roll):
    """Aplica la rotación a la cámara del motor de renderizado."""
    motor.cameraRotation[0] = pitch
    motor.cameraRotation[1] = yaw
    motor.cameraRotation[2] = roll

# --- Bucle principal del programa ---
if __name__ == "__main__":
    screen, clock = inicializar_entorno()
    graphics_engine = Renderer(screen)
    graphics_engine.primitiveType = TRIANGLES
    graphics_engine.cameraPos = [0, 0, CAMERA_DISTANCE_START]
    
    model_data = cargar_activo("models/yoshi.obj", "textures/yoshi.png")
    graphics_engine.models.append(model_data)
    
    if not graphics_engine.loadTexture("textures/yoshi.png", id(model_data)):
        print("Advertencia: No se pudo cargar la textura, renderizando sin ella.")
    else:
        print("Éxito: Textura aplicada al modelo.")
    
    # Imprimir los controles
    print("\n--- Controles del programa ---")
    print("W / S: Mover la cámara adelante/atrás")
    print("UP / DOWN: Mover la cámara arriba/abajo")
    print("LEFT / RIGHT: Mover la cámara izquierda/derecha")
    print("Q / E: Rotar la cámara (yaw)")
    print("A / D: Ladear la cámara (roll)")
    print("R / F: Inclinar la cámara (pitch)")
    print("Clic Izquierdo + Mover Ratón: Girar la cámara libremente")
    print("Rueda del Ratón: Acercar y alejar")
    print("1 / 2 / 3: Cambiar primitiva (Puntos, Líneas, Triángulos)")
    print("ENTER: Guardar captura de pantalla (BMP)")
    print("ESC: Salir del programa")
    print("------------------------------\n")

    # Parámetros de control
    move_speed = 1.0
    mouse_sensitivity = 0.2
    rotation_speed = 15.0
    
    yaw_angle, pitch_angle, roll_angle = 0.0, 0.0, 0.0
    
    mouse_dragging = False
    last_mouse_pos = [0, 0]

    # --- Se calculan las matrices de la tubería de rasterización ---
    # Matriz de Proyección (estática)
    aspect_ratio = SCREEN_DIMENSIONS[0] / SCREEN_DIMENSIONS[1]
    graphics_engine.projectionMatrix = ProjectionMatrix(FOV, aspect_ratio, NEAR_PLANE, FAR_PLANE)
    print("Matriz de Proyección calculada.")

    # Matriz de Viewport (estática)
    graphics_engine.viewportMatrix = ViewportMatrix(SCREEN_DIMENSIONS[0], SCREEN_DIMENSIONS[1])
    print("Matriz de Viewport calculada.")

    running = True
    while running:
        deltaTime = clock.tick(60) / 1000.0
        
        # Configurar la textura activa
        graphics_engine.activeTexture = graphics_engine.textures.get(id(model_data), None)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    graphics_engine.primitiveType = POINTS
                elif event.key == pygame.K_2:
                    graphics_engine.primitiveType = LINES
                elif event.key == pygame.K_3:
                    graphics_engine.primitiveType = TRIANGLES
                elif event.key == pygame.K_RETURN:
                    # Guardar el BMP al presionar ENTER
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    GenerateBMP(f"salida_{timestamp}.bmp", *SCREEN_DIMENSIONS, 3, graphics_engine.frameBuffer)
                    print(f"Captura de pantalla guardada como salida_{timestamp}.bmp")
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_dragging = True
                    pygame.mouse.set_visible(False)
                    last_mouse_pos = pygame.mouse.get_pos()
                    pygame.event.set_grab(True)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_dragging = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    forward, _, _ = obtener_vectores_camara(yaw_angle, pitch_angle, roll_angle)
                    graphics_engine.cameraPos[0] += forward[0] * move_speed * 0.15
                    graphics_engine.cameraPos[1] += forward[1] * move_speed * 0.15
                    graphics_engine.cameraPos[2] += forward[2] * move_speed * 0.15
                elif event.button == 5:
                    forward, _, _ = obtener_vectores_camara(yaw_angle, pitch_angle, roll_angle)
                    graphics_engine.cameraPos[0] -= forward[0] * move_speed * 0.15
                    graphics_engine.cameraPos[1] -= forward[1] * move_speed * 0.15
                    graphics_engine.cameraPos[2] -= forward[2] * move_speed * 0.15
            elif event.type == pygame.MOUSEMOTION and mouse_dragging:
                current_mouse_pos = pygame.mouse.get_pos()
                rel_x = current_mouse_pos[0] - last_mouse_pos[0]
                rel_y = current_mouse_pos[1] - last_mouse_pos[1]
                
                yaw_angle -= rel_x * mouse_sensitivity
                pitch_angle += rel_y * mouse_sensitivity
                
                pitch_angle = max(-89, min(89, pitch_angle))
                
                last_mouse_pos = current_mouse_pos

        # Control del teclado
        keys = pygame.key.get_pressed()
        
        # Movimiento de posición de la cámara (ejes globales)
        if keys[pygame.K_w]: graphics_engine.cameraPos[2] -= move_speed * deltaTime
        if keys[pygame.K_s]: graphics_engine.cameraPos[2] += move_speed * deltaTime
        if keys[pygame.K_RIGHT]: graphics_engine.cameraPos[0] += move_speed * deltaTime
        if keys[pygame.K_LEFT]: graphics_engine.cameraPos[0] -= move_speed * deltaTime
        if keys[pygame.K_UP]: graphics_engine.cameraPos[1] += move_speed * deltaTime
        if keys[pygame.K_DOWN]: graphics_engine.cameraPos[1] -= move_speed * deltaTime

        # Rotaciones de la cámara (ejes locales)
        if keys[pygame.K_a]: roll_angle += rotation_speed * deltaTime
        if keys[pygame.K_d]: roll_angle -= rotation_speed * deltaTime
        if keys[pygame.K_q]: yaw_angle += rotation_speed * deltaTime
        if keys[pygame.K_e]: yaw_angle -= rotation_speed * deltaTime
        
        if keys[pygame.K_r]: pitch_angle += rotation_speed * deltaTime
        if keys[pygame.K_f]: pitch_angle -= rotation_speed * deltaTime
        
        pitch_angle = max(-89, min(89, pitch_angle))
        
        # --- Se calcula y se asigna la Matriz de Vista (dinámica) ---
        graphics_engine.viewMatrix = ViewMatrix(graphics_engine.cameraPos, [pitch_angle, yaw_angle, roll_angle])
        
        # Aplicar la rotación
        actualizar_orientacion_camara(graphics_engine, yaw_angle, pitch_angle, roll_angle)

        # Renderizado
        graphics_engine.glClear()
        graphics_engine.glRender()
        pygame.display.flip()

    # Guardar imagen y salir
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    GenerateBMP(f"Captura_{timestamp}.bmp", *SCREEN_DIMENSIONS, 3, graphics_engine.frameBuffer)
    pygame.quit()