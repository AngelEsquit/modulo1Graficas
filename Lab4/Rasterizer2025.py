import pygame
from gl import Renderer, POINTS, LINES, TRIANGLES
from BMP_Writer import GenerateBMP
from objloader import OBJ
from objToModel import objToModel
from shaders import (vertexShader, waveVertexShader, pulseVertexShader, mathPathVertexShader, rainbowFragmentShader, 
                    textureFragmentShader, toonFragmentShader, mathPathFragmentShader, sliceFragmentShader)
import math
from datetime import datetime

# --- Importamos las matrices de rasterización ---
from MathLib import ViewMatrix, ProjectionMatrix, ViewportMatrix

# --- Configuración global del motor ---
SCREEN_DIMENSIONS = (512, 512)
CAMERA_DISTANCE_START = -10
MODEL_SCALE = .05

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
        model_entity.rotation = [0, 0, 180]
        model_entity.translation = [0, 4, 0]
        
        # NUEVO: Calcular normales para iluminación
        model_entity.calculateNormals()
        print(f"Normales calculadas: {len(model_entity.normals)} normales generadas.")
        
        print(f"Éxito: Modelo '{filepath}' cargado con {len(mesh_data.vertices)} vértices y {len(mesh_data.faces)} caras.")
        return model_entity
        
    except Exception as e:
        print(f"Error fatal: Fallo al cargar el modelo o la textura: {e}")
        pygame.quit()
        exit()

def obtener_vectores_camara(yaw, pitch, roll):
    """Calcula los ejes de la cámara (adelante, derecha, arriba) desde ángulos de Euler."""
    yaw_rad, pitch_rad, roll_rad = map(math.radians, [yaw, pitch, roll])
    
    # Sistema de coordenadas estándar OpenGL
    # Forward (mirando hacia Z negativo en OpenGL)
    forward_vector = [
        -math.cos(pitch_rad) * math.sin(yaw_rad),  # X: invertido para mirar hacia -Z
        math.sin(pitch_rad),                       # Y: hacia arriba
        -math.cos(pitch_rad) * math.cos(yaw_rad)   # Z: hacia adelante (negativo en OpenGL)
    ]
    
    # Right vector (producto cruz de forward y world up)
    world_up = [0, 1, 0]
    right_vector = [
        forward_vector[1] * world_up[2] - forward_vector[2] * world_up[1],
        forward_vector[2] * world_up[0] - forward_vector[0] * world_up[2],
        forward_vector[0] * world_up[1] - forward_vector[1] * world_up[0]
    ]
    
    # Normalizar right vector
    right_length = math.sqrt(sum(x*x for x in right_vector))
    if right_length > 0:
        right_vector = [x/right_length for x in right_vector]
    
    # Up vector (producto cruz de right y forward)
    up_vector = [
        right_vector[1] * forward_vector[2] - right_vector[2] * forward_vector[1],
        right_vector[2] * forward_vector[0] - right_vector[0] * forward_vector[2],
        right_vector[0] * forward_vector[1] - right_vector[1] * forward_vector[0]
    ]
    
    # Aplicar roll (rotación alrededor del eje forward)
    if abs(roll_rad) > 0.001:  # Solo aplicar roll si es significativo
        cos_roll, sin_roll = math.cos(roll_rad), math.sin(roll_rad)
        
        # Rotar right vector
        new_right = [
            right_vector[0] * cos_roll + up_vector[0] * sin_roll,
            right_vector[1] * cos_roll + up_vector[1] * sin_roll,
            right_vector[2] * cos_roll + up_vector[2] * sin_roll
        ]
        
        # Rotar up vector
        new_up = [
            -right_vector[0] * sin_roll + up_vector[0] * cos_roll,
            -right_vector[1] * sin_roll + up_vector[1] * cos_roll,
            -right_vector[2] * sin_roll + up_vector[2] * cos_roll
        ]
        
        right_vector = new_right
        up_vector = new_up
    
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
    graphics_engine.cameraRotation = [0, 0, 0]
    
    model_data = cargar_activo("models/crashbandicoot.obj", "textures/color_pallete.png")
    model_data.vertexShader = vertexShader  # Vertex shader normal por defecto
    model_data.fragmentShader = None  # Sin fragment shader por defecto 
    graphics_engine.models.append(model_data)

    # Cargar textura pero no la activamos por defecto (para triángulos sin textura)
    if not graphics_engine.loadTexture("textures/color_pallete.png", id(model_data)):
        print("Advertencia: No se pudo cargar la textura, renderizando sin ella.")
    else:
        print("Éxito: Textura cargada (no activa por defecto).")
    
    # CONFIGURACIÓN INICIAL: Triángulos sin textura
    graphics_engine.activeTexture = None  # Sin textura activa para mostrar wireframe/sólido
    print("Modo inicial: Triángulos sin textura")
    
    # --- EJEMPLO DE SISTEMA MULTI-TEXTURA (COMENTADO TEMPORALMENTE) ---
    # Cargar texturas adicionales para el modelo
    print("\n--- Sistema Multi-Textura (Deshabilitado temporalmente) ---")
    
    # Agregar texturas adicionales al modelo
    try:
        # Comentado temporalmente para evitar errores
        # model_data.addTexture("back", "textures/back.png") 
        # model_data.addTexture("shoes", "textures/shoes.png")  
        print("Multi-texturas deshabilitadas temporalmente.")
        print("  - Usando solo textura principal: textures/color_pallete.png")
        
        # Cargar las texturas en el renderizador también
        # graphics_engine.loadTexture("textures/shoes.png", "shoes")
        # graphics_engine.loadTexture("textures/back.png", "back")
        
        # Ejemplo de asignación de materiales por triángulos
        # (En un caso real, esto se haría por regiones del modelo)
        total_triangles = len(model_data.vertices) // 15  # Asumiendo 5 componentes por vértice
        # for i in range(min(10, total_triangles)):  # Primeros 10 triángulos
        #     if i < 3:
        #         model_data.setTriangleMaterial(i, "shoes")  # Zapatos
        #     elif i < 6:
        #         model_data.setTriangleMaterial(i, "back")   # Parte de atrás 
        #     else:
        #         model_data.setTriangleMaterial(i, "primary")  # Textura principal
        
        print(f"Modelo tiene {total_triangles} triángulos.")
        print("Nota: Sistema multi-textura estará disponible en futuras versiones.")
        
    except Exception as e:
        print(f"Advertencia: Error en configuración: {e}")
        print("Continuando con textura única...")
    
    print("-------------------------------------------\n")
    
    # Imprimir los controles
    print("\n--- Controles del programa ---")
    print("W / S: Mover la cámara adelante/atrás")
    print("UP / DOWN: Mover la cámara arriba/abajo")
    print("LEFT / RIGHT: Mover la cámara izquierda/derecha")
    print("A / D: Rotar la cámara (yaw)")
    print("Q / E: Ladear la cámara (roll)")
    print("R / F: Inclinar la cámara (pitch)")
    print("Clic Izquierdo + Mover Ratón: Girar la cámara libremente")
    print("Rueda del Ratón: Acercar y alejar")
    print("1 / 2 / 3: Cambiar primitiva (Puntos, Líneas, Triángulos SIN textura)")
    print("4: Rainbow | 5: Textura | 6: Toon + Textura | -: Sólido sin textura")
    print("M: MATH PATH FRAGMENT 🎨 - ¡Bandas de color matemáticas!")
    print("X: SLICE FRAGMENT ✂️ - ¡Cortes estáticos en coordenada X!")
    print("7: SHADER ONDULANTE 🌊 | 8: Vertex shader normal | 9: SHADER PULSANTE 💓")
    print("0: MATH PATH VERTEX 📐 - ¡Patrones matemáticos dinámicos!")
    print("ENTER: Guardar captura de pantalla (BMP)")
    print("ESC: Salir del programa")
    print("------------------------------\n")

    # Parámetros de control (ajustados para mejor respuesta)
    move_speed = 5.0           # Velocidad de movimiento aumentada
    mouse_sensitivity = 0.1    # Sensibilidad del mouse reducida para más precisión
    rotation_speed = 45.0      # Velocidad de rotación con teclado (grados por segundo)
    
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
        
        # No configurar textura automáticamente - mantener la selección del usuario
        
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
                    graphics_engine.activeTexture = None  # Triángulos sin textura
                    print("Primitiva: Triángulos sin textura")
                elif event.key == pygame.K_4:
                    model_data.fragmentShader = rainbowFragmentShader
                    print("Fragment shader cambiado a: Rainbow")
                elif event.key == pygame.K_5:
                    model_data.fragmentShader = textureFragmentShader
                    graphics_engine.activeTexture = graphics_engine.textures.get(id(model_data), None)
                    print("Fragment shader cambiado a: Textura")
                elif event.key == pygame.K_6:
                    model_data.fragmentShader = toonFragmentShader
                    print("Fragment shader cambiado a: Toon + Textura")
                elif event.key == pygame.K_7:
                    # Activar shader ondulante
                    model_data.vertexShader = waveVertexShader
                    print("Vertex shader cambiado a: ONDULANTE - El modelo ahora ondula!")
                elif event.key == pygame.K_8:
                    # Volver al vertex shader normal
                    model_data.vertexShader = vertexShader
                    print("Vertex shader cambiado a: Normal")
                elif event.key == pygame.K_9:
                    # Activar shader pulsante
                    model_data.vertexShader = pulseVertexShader
                    print("Vertex shader cambiado a: PULSANTE 💓 - El modelo ahora late como un corazón!")
                elif event.key == pygame.K_0:
                    # Activar shader de patrones matemáticos
                    model_data.vertexShader = mathPathVertexShader
                    print("Vertex shader cambiado a: MATH PATH 📐 - ¡Patrones matemáticos dinámicos!")
                elif event.key == pygame.K_MINUS:
                    model_data.fragmentShader = None
                    graphics_engine.activeTexture = None  # Sin textura para modo sólido
                    print("Modo: Triángulos sólidos sin textura ni shaders")
                elif event.key == pygame.K_m:
                    # Activar shader de patrones matemáticos
                    model_data.fragmentShader = mathPathFragmentShader
                    graphics_engine.activeTexture = None  # Sin textura para mejor efecto
                    print("Fragment shader cambiado a: MATH PATH 🎨 - ¡Bandas de color matemáticas!")
                elif event.key == pygame.K_x:
                    # Activar shader de cortes
                    model_data.fragmentShader = sliceFragmentShader
                    graphics_engine.activeTexture = graphics_engine.textures.get(id(model_data), None)  # Usar textura si está disponible
                    print("Fragment shader cambiado a: SLICE ✂️ - ¡Cortes estáticos en X!")
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
                if event.button == 4:  # Rueda hacia arriba - acercar
                    forward, _, _ = obtener_vectores_camara(yaw_angle, pitch_angle, roll_angle)
                    zoom_speed = move_speed * 0.3
                    graphics_engine.cameraPos[0] += forward[0] * zoom_speed
                    graphics_engine.cameraPos[1] += forward[1] * zoom_speed
                    graphics_engine.cameraPos[2] += forward[2] * zoom_speed
                elif event.button == 5:  # Rueda hacia abajo - alejar
                    forward, _, _ = obtener_vectores_camara(yaw_angle, pitch_angle, roll_angle)
                    zoom_speed = move_speed * 0.3
                    graphics_engine.cameraPos[0] -= forward[0] * zoom_speed
                    graphics_engine.cameraPos[1] -= forward[1] * zoom_speed
                    graphics_engine.cameraPos[2] -= forward[2] * zoom_speed
            elif event.type == pygame.MOUSEMOTION and mouse_dragging:
                current_mouse_pos = pygame.mouse.get_pos()
                rel_x = current_mouse_pos[0] - last_mouse_pos[0]
                rel_y = current_mouse_pos[1] - last_mouse_pos[1]
                
                # Aplicar sensibilidad del mouse
                yaw_angle -= rel_x * mouse_sensitivity
                pitch_angle -= rel_y * mouse_sensitivity  # Invertido para movimiento natural
                
                # Limitar pitch para evitar gimbal lock
                pitch_angle = max(-89, min(89, pitch_angle))
                
                # Mantener yaw en rango [-180, 180] para consistencia
                if yaw_angle > 180:
                    yaw_angle -= 360
                elif yaw_angle < -180:
                    yaw_angle += 360
                
                last_mouse_pos = current_mouse_pos

        # Control del teclado
        keys = pygame.key.get_pressed()
        
        # Obtener vectores de la cámara para movimiento relativo
        forward, right, up = obtener_vectores_camara(yaw_angle, pitch_angle, roll_angle)
        
        # Movimiento de posición de la cámara (relativo a la orientación de la cámara)
        # W / S: Mover la cámara adelante/atrás
        if keys[pygame.K_w]:
            graphics_engine.cameraPos[0] += forward[0] * move_speed * deltaTime
            graphics_engine.cameraPos[1] += forward[1] * move_speed * deltaTime
            graphics_engine.cameraPos[2] += forward[2] * move_speed * deltaTime
        if keys[pygame.K_s]:
            graphics_engine.cameraPos[0] -= forward[0] * move_speed * deltaTime
            graphics_engine.cameraPos[1] -= forward[1] * move_speed * deltaTime
            graphics_engine.cameraPos[2] -= forward[2] * move_speed * deltaTime
        
        # LEFT / RIGHT: Mover la cámara izquierda/derecha
        if keys[pygame.K_LEFT]:
            graphics_engine.cameraPos[0] -= right[0] * move_speed * deltaTime
            graphics_engine.cameraPos[1] -= right[1] * move_speed * deltaTime
            graphics_engine.cameraPos[2] -= right[2] * move_speed * deltaTime
        if keys[pygame.K_RIGHT]:
            graphics_engine.cameraPos[0] += right[0] * move_speed * deltaTime
            graphics_engine.cameraPos[1] += right[1] * move_speed * deltaTime
            graphics_engine.cameraPos[2] += right[2] * move_speed * deltaTime
        
        # UP / DOWN: Mover la cámara arriba/abajo
        if keys[pygame.K_UP]:
            graphics_engine.cameraPos[0] += up[0] * move_speed * deltaTime
            graphics_engine.cameraPos[1] += up[1] * move_speed * deltaTime
            graphics_engine.cameraPos[2] += up[2] * move_speed * deltaTime
        if keys[pygame.K_DOWN]:
            graphics_engine.cameraPos[0] -= up[0] * move_speed * deltaTime
            graphics_engine.cameraPos[1] -= up[1] * move_speed * deltaTime
            graphics_engine.cameraPos[2] -= up[2] * move_speed * deltaTime

        # Rotaciones de la cámara
        # A / D: Rotar la cámara (yaw)
        if keys[pygame.K_a]: yaw_angle += rotation_speed * deltaTime
        if keys[pygame.K_d]: yaw_angle -= rotation_speed * deltaTime
        
        # Q / E: Ladear la cámara (roll)
        if keys[pygame.K_q]: roll_angle += rotation_speed * deltaTime
        if keys[pygame.K_e]: roll_angle -= rotation_speed * deltaTime
        
        # R / F: Inclinar la cámara (pitch)
        if keys[pygame.K_r]: pitch_angle += rotation_speed * deltaTime
        if keys[pygame.K_f]: pitch_angle -= rotation_speed * deltaTime
        
        # Limitar ángulos para evitar problemas
        pitch_angle = max(-89, min(89, pitch_angle))
        
        # Mantener yaw y roll en rango [-180, 180]
        for angle_name, angle_value in [("yaw_angle", yaw_angle), ("roll_angle", roll_angle)]:
            if angle_value > 180:
                if angle_name == "yaw_angle":
                    yaw_angle -= 360
                else:
                    roll_angle -= 360
            elif angle_value < -180:
                if angle_name == "yaw_angle":
                    yaw_angle += 360
                else:
                    roll_angle += 360
        
        # --- Se calcula y se asigna la Matriz de Vista (dinámica) ---
        graphics_engine.viewMatrix = ViewMatrix(graphics_engine.cameraPos, [pitch_angle, yaw_angle, roll_angle])
        
        # Aplicar la rotación
        actualizar_orientacion_camara(graphics_engine, yaw_angle, pitch_angle, roll_angle)

        # Renderizado
        graphics_engine.glClear()
        graphics_engine.glRender()
        pygame.display.flip()
    pygame.quit()