import numpy as np
import math
import time

def normalize(vector):
    """Normaliza un vector 3D"""
    magnitude = math.sqrt(sum(comp**2 for comp in vector))
    if magnitude == 0:
        return [0, 0, 0]
    return [comp / magnitude for comp in vector]

def dot_product(a, b):
    """Calcula el producto punto entre dos vectores"""
    return sum(a[i] * b[i] for i in range(len(a)))

def hsv_to_rgb(h, s, v):
    """Convierte HSV a RGB"""
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    
    i = i % 6
    if i == 0: return [v, t, p]
    elif i == 1: return [q, v, p]
    elif i == 2: return [p, v, t]
    elif i == 3: return [p, q, v]
    elif i == 4: return [t, p, v]
    else: return [v, p, q]

# FRAGMENT SHADERS

def rainbowFragmentShader(fragment_data):
    """Fragment shader que crea un efecto rainbow animado"""
    x, y, z = fragment_data['position']
    current_time = time.time()
    
    # Crear efecto rainbow basado en posición y tiempo
    hue = ((x + y) * 0.01 + current_time * 0.5) % 1.0
    prev = fragment_data.get('prev_color')
    color = hsv_to_rgb(hue, 0.8, 0.9)
    if prev:
        # Mezcla aditiva suave
        color = [min(1, prev[i] + color[i]*0.6) for i in range(3)]
    
    # Asegurar que los valores estén en el rango [0, 1]
    return [max(0, min(1, c)) for c in color]

def textureFragmentShader(fragment_data):
    """Fragment shader para texturas con interpolación y soporte multi-textura"""
    uv_list = fragment_data.get('uv_coords')
    tex = fragment_data.get('texture')
    if uv_list and tex:
        try:
            w0, w1, w2 = fragment_data['barycentric']
            u = w0 * uv_list[0][0] + w1 * uv_list[1][0] + w2 * uv_list[2][0]
            v = w0 * uv_list[0][1] + w1 * uv_list[1][1] + w2 * uv_list[2][1]
            u = u % 1.0; v = v % 1.0
            tw, th = tex.get_width(), tex.get_height()
            tx = int(u * (tw - 1)); ty = int((1 - v) * (th - 1))
            tx = max(0, min(tw - 1, tx)); ty = max(0, min(th - 1, ty))
            c = tex.get_at((tx, ty))
            sampled = [c.r/255, c.g/255, c.b/255]
            prev = fragment_data.get('prev_color')
            if prev:
                # Mezcla multiplicativa ligera
                return [prev[i]*sampled[i] for i in range(3)]
            return sampled
        except Exception:
            pass
    # Fallback: usar material_color si se pasó, sino blanco
    extra = fragment_data.get('extra_maps') or {}
    return extra.get('material_color', [1,1,1])

def mathPathFragmentShader(fragment_data):
    """
    Fragment shader que crea patrones matemáticos con bandas de color
    """
    x, y, z = fragment_data['position']
    
    # Crear efecto de bandas de color
    intensity = (math.sin(x * 0.1) + math.sin(y * 0.1)) * 0.5 + 0.5
    
    # Cuantizar la intensidad para efecto
    if intensity > 0.8:
        return [1.0, 0.8, 0.2]  # Amarillo brillante
    palette = [
        (0.8, [1.0,0.8,0.2]),
        (0.6, [1.0,0.4,0.1]),
        (0.4, [0.8,0.2,0.2]),
        (0.2, [0.4,0.1,0.6])
    ]
    col = [0.1,0.1,0.4]
    for th,c in palette:
        if intensity>th:
            col=c; break
    prev = fragment_data.get('prev_color')
    if prev:
        # Overlay simple
        col = [min(1, col[i]*0.6 + prev[i]*0.7) for i in range(3)]
    return col
def sliceFragmentShader(fragment_data):
    """
    Fragment shader que crea efecto de cortes/rebanadas estáticos en el modelo
    Pinta de negro ciertas secciones basadas en la coordenada X del mundo
    """
    # Obtener la posición del fragmento en coordenadas del mundo
    x, y, z = fragment_data['position']
    
    # Configuración del efecto de corte (estático)
    slice_width = 0.3        # Ancho de cada corte
    slice_spacing = 1.5      # Separación entre cortes
    
    # Crear patrón de cortes repetitivos basado solo en X
    # Normalizar X para crear el patrón
    normalized_x = (x % slice_spacing) / slice_spacing
    
    # Determinar si este fragmento está en una zona de corte
    # Crear múltiples cortes en el patrón
    in_slice = False
    
    # Primer corte
    if normalized_x < slice_width:
        in_slice = True
    
    # Segundo corte (opcional, para más densidad)
    slice_offset = 0.6  # Posición del segundo corte
    if normalized_x > slice_offset and normalized_x < (slice_offset + slice_width):
        in_slice = True
    
    if in_slice:
        # Zona de corte - pintar de negro
        prev = fragment_data.get('prev_color')
        if prev:
            return [prev[i]*0.2 for i in range(3)]
        return [0.0, 0.0, 0.0]
    else:
        # Zona normal - usar color base o textura si está disponible
        
        # Si hay textura, usarla como color base
        if fragment_data.get('uv_coords') and fragment_data.get('texture'):
            w0, w1, w2 = fragment_data['barycentric']
            uv_coords = fragment_data['uv_coords']
            
            # Interpolar UV
            u = w0 * uv_coords[0][0] + w1 * uv_coords[1][0] + w2 * uv_coords[2][0]
            v = w0 * uv_coords[0][1] + w1 * uv_coords[1][1] + w2 * uv_coords[2][1]
            
            # Wrapping UV
            u = u % 1.0
            v = v % 1.0
            
            # Muestrear textura
            texture = fragment_data['texture']
            tex_width = texture.get_width()
            tex_height = texture.get_height()
            tex_x = int(u * (tex_width - 1))
            tex_y = int((1 - v) * (tex_height - 1))
            
            # Validación de límites
            tex_x = max(0, min(tex_width - 1, tex_x))
            tex_y = max(0, min(tex_height - 1, tex_y))
            
            color = texture.get_at((tex_x, tex_y))
            sampled = [color.r/255, color.g/255, color.b/255]
            prev = fragment_data.get('prev_color')
            if prev:
                return [ (prev[i]+sampled[i])*0.5 for i in range(3)]
            return sampled
        
        else:
            # Sin textura - usar un color base claro para resaltar los cortes
            return [0.8, 0.8, 0.8]

def origamiFragmentShader(fragment_data):
    """Fragment shader estilo 'origami':
    - Caras planas blancas
    - Bordes/ aristas negras usando las coordenadas baricéntricas

    Estrategia: aprovechamos que en el raster se interpolan w0,w1,w2.
    En el borde de un triángulo uno de los pesos tiende a 0. Si min(w0,w1,w2)
    es menor que un umbral => píxel de arista.
    Usamos una transición suave (smoothstep) para anti‑aliasing básico.
    """
    w0, w1, w2 = fragment_data['barycentric']
    edge_min = min(w0, w1, w2)

    edge_width = 0.035  # grosor de línea en espacio baricéntrico (ajustable)
    feather = edge_width * 0.5  # zona de suavizado

    # Función smoothstep manual
    t = (edge_min - feather) / max(1e-6, (edge_width - feather))
    if t < 0: t = 0
    if t > 1: t = 1
    # t=0 borde puro, t=1 cara pura
    line_intensity = t  # 0 negro, 1 blanco

    base_face_color = [1.0, 1.0, 1.0]
    edge_color = [0.0, 0.0, 0.0]

    # Mezcla lineal edge -> face
    out_col = [edge_color[i] * (1 - line_intensity) + base_face_color[i] * line_intensity for i in range(3)]
    prev = fragment_data.get('prev_color')
    if prev:
        # Mantener líneas negras pero mezclar caras
        return [out_col[i]*0.8 + prev[i]*0.2 for i in range(3)]
    return out_col

def dotFragmentShader(fragment_data):
    """Halftone en espacio de pantalla (screen‑space) para evitar estiramiento por UV.
    Grilla de celdas en (x,y) de pixel y círculos isotrópicos.
    Hotkey: 'p'
    """
    # 1. Color base (preferir textura, fallback a material)
    base_color = [1,1,1]
    uv_list = fragment_data.get('uv_coords')
    tex = fragment_data.get('texture')
    if uv_list and tex:
        try:
            w0,w1,w2 = fragment_data['barycentric']
            u = (w0*uv_list[0][0] + w1*uv_list[1][0] + w2*uv_list[2][0]) % 1.0
            v = (w0*uv_list[0][1] + w1*uv_list[1][1] + w2*uv_list[2][1]) % 1.0
            tw,th = tex.get_width(), tex.get_height()
            tx = int(u*(tw-1)); ty = int((1-v)*(th-1))
            tx = max(0,min(tw-1,tx)); ty = max(0,min(th-1,ty))
            c = tex.get_at((tx,ty))
            base_color = [c.r/255, c.g/255, c.b/255]
        except Exception:
            pass
    else:
        base_color = (fragment_data.get('extra_maps') or {}).get('material_color', base_color)

    # 2. Luma para controlar tamaño
    luma = 0.299*base_color[0] + 0.587*base_color[1] + 0.114*base_color[2]

    # 3. Parámetros del patrón
    cell_px = 5
    min_r = 0.35
    max_r = 1.6
    soften = 0.6
    invert = True

    x, y, _ = fragment_data['position']
    # 4. Coordenadas locales
    lx = (x % cell_px) / cell_px
    ly = (y % cell_px) / cell_px
    dx = lx - 0.5
    dy = ly - 0.5
    dist = (dx*dx + dy*dy) ** 0.5 * cell_px

    # 5. Radio según luma
    t = 1 - (luma ** soften)
    radius = min_r + t * (max_r - min_r)

    # 6. Colores punto / fondo
    if invert:
        dot_col = [base_color[i]*0.15 for i in range(3)]
        bg_col  = base_color
    else:
        dot_col = base_color
        bg_col  = [1,1,1]

    # 7. Feather
    feather = max(0.75, radius*0.35)
    if dist < radius - feather:
        prev = fragment_data.get('prev_color')
        if prev:
            return [dot_col[i]*0.5 + prev[i]*0.5 for i in range(3)]
        return dot_col
    elif dist < radius + feather:
        k = (dist - (radius - feather)) / (2*feather)
        k = max(0,min(1,k))
        mixed = [dot_col[i]*(1-k) + bg_col[i]*k for i in range(3)]
        prev = fragment_data.get('prev_color')
        if prev:
            return [ (mixed[i]+prev[i])*0.5 for i in range(3)]
        return mixed
    else:
        prev = fragment_data.get('prev_color')
        if prev:
            return [ (bg_col[i]+prev[i])*0.5 for i in range(3)]
        return bg_col

def vertexColorFragmentShader(fragment_data):
    """Fragment shader que interpola colores de vértices"""
    if fragment_data['vertex_colors'] and len(fragment_data['vertex_colors']) >= 3:
        w0, w1, w2 = fragment_data['barycentric']
        vertex_colors = fragment_data['vertex_colors']
        
        # Interpolar colores
        color = [
            w0 * vertex_colors[0][0] + w1 * vertex_colors[1][0] + w2 * vertex_colors[2][0],
            w0 * vertex_colors[0][1] + w1 * vertex_colors[1][1] + w2 * vertex_colors[2][1],
            w0 * vertex_colors[0][2] + w1 * vertex_colors[1][2] + w2 * vertex_colors[2][2]
        ]
        return color
    
    return [1, 1, 1]  # Blanco por defecto

def toonFragmentShader(fragment_data):
    """Fragment shader que crea un efecto toon/cartoon con iluminación, textura y soporte multi-textura"""
    extra = fragment_data.get('extra_maps') or {}
    base_color = extra.get('material_color', [0.6, 0.8, 0.9])
    tex = fragment_data.get('texture')
    uv_list = fragment_data.get('uv_coords')
    if tex and uv_list:
        try:
            w0, w1, w2 = fragment_data['barycentric']
            u = w0 * uv_list[0][0] + w1 * uv_list[1][0] + w2 * uv_list[2][0]
            v = w0 * uv_list[0][1] + w1 * uv_list[1][1] + w2 * uv_list[2][1]
            u = u % 1.0; v = v % 1.0
            tw, th = tex.get_width(), tex.get_height()
            tx = int(u * (tw - 1)); ty = int((1 - v) * (th - 1))
            tx = max(0, min(tw - 1, tx)); ty = max(0, min(th - 1, ty))
            c = tex.get_at((tx, ty))
            # Mezclar multiplicando con color de material para permitir tinte
            sampled = [c.r/255, c.g/255, c.b/255]
            base_color = [sampled[i] * base_color[i] for i in range(3)]
        except Exception:
            pass
    
    # Si hay normales, calcular iluminación toon
    if fragment_data.get('normals') and len(fragment_data['normals']) >= 3:
        # Interpolar normal usando coordenadas baricéntricas
        w0, w1, w2 = fragment_data['barycentric']
        normals = fragment_data['normals']
        
        interpolated_normal = [
            w0 * normals[0][0] + w1 * normals[1][0] + w2 * normals[2][0],
            w0 * normals[0][1] + w1 * normals[1][1] + w2 * normals[2][1],
            w0 * normals[0][2] + w1 * normals[1][2] + w2 * normals[2][2]
        ]
        
        # Normalizar la normal interpolada
        normal = normalize(interpolated_normal)
        
        # Configuración de luz direccional
        light_direction = normalize([1, 1, 1])  # Luz desde arriba-derecha
        
        # Calcular factor de iluminación difusa
        light_intensity = max(0, dot_product(normal, light_direction))
        
        # **CUANTIZACIÓN TOON**: Dividir la intensidad en bandas discretas
        if light_intensity > 0.8:
            toon_intensity = 1.0      # Zona más brillante
        elif light_intensity > 0.5:
            toon_intensity = 0.7      # Zona media-brillante
        elif light_intensity > 0.25:
            toon_intensity = 0.4      # Zona media-oscura
        else:
            toon_intensity = 0.1      # Zona de sombra
        
        # Aplicar la intensidad cuantizada al color base (textura o color sólido)
        final_color = [base_color[i] * toon_intensity for i in range(3)]
        
        # Agregar un poco de luz ambiente
        ambient_strength = 0.15
        for i in range(3):
            final_color[i] += ambient_strength * base_color[i]
            final_color[i] = max(0, min(1, final_color[i]))  # Clampear
        
        prev = fragment_data.get('prev_color')
        if prev:
            # Lighten blend
            return [min(1, (final_color[i]*0.6 + prev[i]*0.6)) for i in range(3)]
        return final_color
    
    else:
        # Si no hay normales, devolver el color base (textura o color sólido)
        prev = fragment_data.get('prev_color')
        if prev:
            return [ (base_color[i]+prev[i])*0.5 for i in range(3)]
        return base_color

# VERTEX SHADERS

def rainbowVertexShader(vertex, **kwargs):
    """Rainbow shader que genera colores por coordenadas UV"""
    x, y, z = vertex[0], vertex[1], vertex[2]
    
    # Aplicar transformaciones normales
    modelMatrix = kwargs["modelMatrix"]
    viewMatrix = kwargs["viewMatrix"]
    
    vt = np.matrix([[x], [y], [z], [1]])
    vt = modelMatrix @ vt
    vt = viewMatrix @ vt
    
    vt = vt.tolist()
    w = vt[3][0] if vt[3][0] != 0 else 1
    result = [vt[0][0] / w, vt[1][0] / w, vt[2][0] / w]
    
    # Si hay coordenadas UV, generar color rainbow
    if len(vertex) >= 5:
        u, v = vertex[3], vertex[4]
        current_time = time.time()
        
        # Generar hue basado en UV y tiempo
        hue = (u + v * 0.3 + current_time * 0.5) % 1.0
        rainbow_color = hsv_to_rgb(hue, 0.9, 0.8)
        
        # Asegurar que los colores estén en el rango [0, 1]
        rainbow_color = [max(0, min(1, c)) for c in rainbow_color]
        
        # Añadir UV y color al resultado
        result.extend([u, v])
        result.extend(rainbow_color)  # R, G, B
    elif len(vertex) > 3:
        result.extend(vertex[3:])
    
    return result

def waveVertexShader(vertex, **kwargs):
    """
    Vertex shader que hace ondular el modelo usando funciones seno.
    Crea ondas que se propagan a través del modelo en tiempo real.
    """
    # Obtener las coordenadas del vértice
    x, y, z = vertex[0], vertex[1], vertex[2]
    
    # Obtener el tiempo actual para animación
    current_time = time.time()
    
    # Parámetros de las ondas (AMPLITUD AUMENTADA)
    wave_amplitude = 3.0      # Amplitud de las ondas (aumentada de 0.5 a 1.2)
    wave_frequency = 4.0      # Frecuencia espacial
    wave_speed = 3.0          # Velocidad de propagación
    
    # Calcular múltiples ondas para efecto más complejo
    # Onda principal en X (más pronunciada)
    wave1 = math.sin(x * wave_frequency + current_time * wave_speed) * wave_amplitude
    # Onda secundaria en Z (amplitud relativa aumentada)
    wave2 = math.cos(z * wave_frequency * 0.7 + current_time * wave_speed * 1.3) * wave_amplitude * 0.8
    # Onda combinada en diagonal (amplitud relativa aumentada)
    wave3 = math.sin((x + z) * wave_frequency * 0.5 + current_time * wave_speed * 0.8) * wave_amplitude * 0.6
    
    # Aplicar las ondas principalmente al eje Y (vertical)
    y_modified = y + wave1 + wave2 + wave3
    
    # Ondulación aumentada en X y Z para efecto más orgánico y dramático
    x_modified = x + wave2 * 0.4  # Aumentado de 0.2 a 0.4
    z_modified = z + wave1 * 0.4  # Aumentado de 0.2 a 0.4
    
    # Crear vértice modificado
    modified_vertex = [x_modified, y_modified, z_modified]
    
    # Mantener las coordenadas UV si existen
    if len(vertex) > 3:
        modified_vertex.extend(vertex[3:])
    
    # Aplicar transformaciones normales con el vértice ondulado
    modelMatrix = kwargs["modelMatrix"]
    viewMatrix = kwargs["viewMatrix"]

    # Preparar el vector de transformación
    vt = np.matrix([
        [modified_vertex[0]],
        [modified_vertex[1]],
        [modified_vertex[2]],
        [1]
    ])

    # Aplicar transformaciones
    vt = modelMatrix @ vt    # Transformación del modelo
    vt = viewMatrix @ vt     # Transformación de la vista

    # Convertir a lista
    vt = vt.tolist()
    vt = [vt[0][0], vt[1][0], vt[2][0], vt[3][0]]

    # Perspectiva: dividir por w
    w = vt[3] if vt[3] != 0 else 1
    result = [
        vt[0] / w,
        vt[1] / w,
        vt[2] / w
    ]

    # Mantener coordenadas UV si existían
    if len(vertex) > 3:
        result.extend(vertex[3:])

    return result

def pulseVertexShader(vertex, **kwargs):
    """
    Vertex shader que hace que el modelo pulse como un corazón latiendo.
    Escala el modelo desde un punto central usando funciones trigonométricas.
    """
    # Obtener las coordenadas del vértice
    x, y, z = vertex[0], vertex[1], vertex[2]
    
    # Obtener el tiempo actual para animación
    current_time = time.time()
    
    # Parámetros del pulso
    pulse_frequency = 2.0     # Frecuencia del latido (latidos por segundo)
    pulse_intensity = 0.5     # Intensidad del pulso (0.0 a 1.0)
    base_scale = 1.0          # Escala base del modelo
    
    # Calcular el factor de pulso usando múltiples ondas para efecto más orgánico
    # Pulso principal (latido fuerte)
    pulse_main = math.sin(current_time * pulse_frequency * math.pi * 2) * pulse_intensity
    
    # Pulso secundario (latido suave entre latidos principales)
    pulse_secondary = math.sin(current_time * pulse_frequency * math.pi * 4) * pulse_intensity * 0.3
    
    # Combinar pulsos para crear patrón de latido realista
    pulse_factor = base_scale + pulse_main + pulse_secondary
    
    # Asegurar que el factor de escala no sea negativo
    pulse_factor = max(0.1, pulse_factor)
    
    # Calcular el centro del modelo (punto desde el cual pulse)
    # Asumimos que el centro está en el origen, pero se puede ajustar
    center_x, center_y, center_z = 0.0, 0.0, 0.0
    
    # Calcular la distancia desde el centro
    distance_from_center = math.sqrt((x - center_x)**2 + (y - center_y)**2 + (z - center_z)**2)
    
    # Aplicar pulso no uniforme (más intenso en el centro, menos en los extremos)
    distance_factor = max(0.1, 1.0 - distance_from_center * 0.1)  # Factor basado en distancia
    local_pulse_factor = base_scale + (pulse_main + pulse_secondary) * distance_factor
    local_pulse_factor = max(0.1, local_pulse_factor)
    
    # Escalar el vértice desde el centro
    x_pulsed = center_x + (x - center_x) * local_pulse_factor
    y_pulsed = center_y + (y - center_y) * local_pulse_factor
    z_pulsed = center_z + (z - center_z) * local_pulse_factor
    
    # Agregar una ligera variación en Y para simular "respiración"
    breathing_offset = math.sin(current_time * pulse_frequency * 0.5) * 0.1
    y_pulsed += breathing_offset
    
    # Crear vértice modificado
    modified_vertex = [x_pulsed, y_pulsed, z_pulsed]
    
    # Mantener las coordenadas UV si existen
    if len(vertex) > 3:
        modified_vertex.extend(vertex[3:])
    
    # Aplicar transformaciones normales con el vértice pulsante
    modelMatrix = kwargs["modelMatrix"]
    viewMatrix = kwargs["viewMatrix"]

    # Preparar el vector de transformación
    vt = np.matrix([
        [modified_vertex[0]],
        [modified_vertex[1]],
        [modified_vertex[2]],
        [1]
    ])

    # Aplicar transformaciones
    vt = modelMatrix @ vt    # Transformación del modelo
    vt = viewMatrix @ vt     # Transformación de la vista

    # Convertir a lista
    vt = vt.tolist()
    vt = [vt[0][0], vt[1][0], vt[2][0], vt[3][0]]

    # Perspectiva: dividir por w
    w = vt[3] if vt[3] != 0 else 1
    result = [
        vt[0] / w,
        vt[1] / w,
        vt[2] / w
    ]

    # Mantener coordenadas UV si existían
    if len(vertex) > 3:
        result.extend(vertex[3:])

    return result

def vertexShader(vertex, **kwargs):
    """
    Vertex shader que transforma los vértices y mantiene las coordenadas UV si existen.
    Parámetros:
        vertex: Lista con las coordenadas del vértice [x, y, z] o [x, y, z, u, v]
        kwargs: Diccionario con matrices de transformación
    Retorna:
        Lista con vértice transformado [x, y, z] o [x, y, z, u, v]
    """
    # Obtener las coordenadas del vértice
    x, y, z = vertex[0], vertex[1], vertex[2]
    
    # Matrices de transformación
    modelMatrix = kwargs["modelMatrix"]
    viewMatrix = kwargs["viewMatrix"]

    # Preparar el vector de transformación
    vt = np.matrix([
        [x],
        [y],
        [z],
        [1]
    ])

    # Aplicar transformaciones en el orden correcto
    vt = modelMatrix @ vt    # Primero transformación del modelo
    vt = viewMatrix @ vt     # Luego transformación de la vista

    # Convertir a lista plana
    vt = vt.tolist()
    vt = [vt[0][0], vt[1][0], vt[2][0], vt[3][0]]

    # Perspectiva: dividir x,y,z por w (último componente)
    w = vt[3] if vt[3] != 0 else 1  # Evitar división por cero
    vt = [
        vt[0] / w,
        vt[1] / w,
        vt[2] / w
    ]

    # Si el vértice incluía coordenadas UV (u, v), mantenerlas
    if len(vertex) > 3:
        # Asegurarse de que hay al menos 5 componentes (x,y,z,u,v)
        if len(vertex) >= 5:
            u = vertex[3]
            v = vertex[4]
            vt.extend([u, v])  # Añadir las coordenadas UV al resultado

    return vt


def mathPathVertexShader(vertex, **kwargs):
    """
    Vertex shader que crea deformaciones matemáticas dinámicas
    Complementa el mathPathFragmentShader con movimientos geométricos
    """
    import time
    
    # Obtener el tiempo actual
    t = time.time()
    
    # Coordenadas originales
    x, y, z = vertex[0], vertex[1], vertex[2]
    
    # Crear patrones matemáticos complejos
    # Espiral matemática en el tiempo
    spiral_factor = 0.3
    spiral_x = math.cos(y * 0.5 + t) * spiral_factor
    spiral_z = math.sin(y * 0.5 + t) * spiral_factor
    
    # Ondas sinusoidales cruzadas
    wave_amplitude = 0.4
    wave1 = math.sin(x * 2.0 + t * 2.0) * wave_amplitude
    wave2 = math.cos(z * 1.5 + t * 1.5) * wave_amplitude
    
    # Función matemática de torsión basada en distancia
    distance_from_origin = math.sqrt(x*x + z*z)
    twist_angle = distance_from_origin * 0.5 + t
    twist_x = x * math.cos(twist_angle) - z * math.sin(twist_angle)
    twist_z = x * math.sin(twist_angle) + z * math.cos(twist_angle)
    
    # Combinar todos los efectos
    nueva_x = twist_x + spiral_x + wave1 * 0.3
    nueva_y = y + wave1 + wave2
    nueva_z = twist_z + spiral_z + wave2 * 0.3
    
    # Aplicar las transformaciones de matriz
    modelMatrix = kwargs["modelMatrix"]
    viewMatrix = kwargs["viewMatrix"]

    # Preparar el vector de transformación con las nuevas coordenadas
    vt = np.matrix([
        [nueva_x],
        [nueva_y],
        [nueva_z],
        [1]
    ])

    # Aplicar transformaciones en el orden correcto
    vt = modelMatrix @ vt    # Primero transformación del modelo
    vt = viewMatrix @ vt     # Luego transformación de la vista

    # Convertir a lista plana
    vt = vt.tolist()
    vt = [vt[0][0], vt[1][0], vt[2][0], vt[3][0]]

    # Perspectiva: dividir x,y,z por w (último componente)
    w = vt[3] if vt[3] != 0 else 1  # Evitar división por cero
    vt = [
        vt[0] / w,
        vt[1] / w,
        vt[2] / w
    ]

    # Si el vértice incluía coordenadas UV (u, v), mantenerlas
    if len(vertex) > 3:
        # Asegurarse de que hay al menos 5 componentes (x,y,z,u,v)
        if len(vertex) >= 5:
            u = vertex[3]
            v = vertex[4]
            vt.extend([u, v])  # Añadir las coordenadas UV al resultado

    return vt

def normalMapFragmentShader(fragment_data):
    """Fragment shader básico que aplica normal mapping si hay normal_map en extra_maps.
    Iluminación: luz direccional fija + ambiente, usando normal perturbada.
    Requiere: uv_coords, normals, extra_maps['normal_map'].
    """
    # Fallback color
    base = [1,1,1]
    if fragment_data.get('uv_coords') and fragment_data.get('texture'):
        # Sample base diffuse
        w0,w1,w2 = fragment_data['barycentric']
        uv = fragment_data['uv_coords']
        u = w0*uv[0][0] + w1*uv[1][0] + w2*uv[2][0]
        v = w0*uv[0][1] + w1*uv[1][1] + w2*uv[2][1]
        u = max(0,min(1,u)); v = max(0,min(1,v))
        tex = fragment_data['texture']
        tw,th = tex.get_width(), tex.get_height()
        tx = int(u*(tw-1)); ty = int((1-v)*(th-1))
        tx = max(0,min(tw-1,tx)); ty = max(0,min(th-1,ty))
        pc = tex.get_at((tx,ty))
        base = [pc.r/255, pc.g/255, pc.b/255]
    N = [0,0,1]
    if fragment_data.get('normals'):
        w0,w1,w2 = fragment_data['barycentric']
        nv = fragment_data['normals']
        N = [
            w0*nv[0][0] + w1*nv[1][0] + w2*nv[2][0],
            w0*nv[0][1] + w1*nv[1][1] + w2*nv[2][1],
            w0*nv[0][2] + w1*nv[1][2] + w2*nv[2][2],
        ]
    # Normal map
    nm_tex = None
    extra = fragment_data.get('extra_maps') or {}
    nm_tex = extra.get('normal_map')
    if nm_tex and fragment_data.get('uv_coords'):
        # Sample normal map (tangent space)
        w0,w1,w2 = fragment_data['barycentric']
        uv = fragment_data['uv_coords']
        u = w0*uv[0][0] + w1*uv[1][0] + w2*uv[2][0]
        v = w0*uv[0][1] + w1*uv[1][1] + w2*uv[2][1]
        u = max(0,min(1,u)); v = max(0,min(1,v))
        tw,th = nm_tex.get_width(), nm_tex.get_height()
        tx = int(u*(tw-1)); ty = int((1-v)*(th-1))
        tx = max(0,min(tw-1,tx)); ty = max(0,min(th-1,ty))
        ncol = nm_tex.get_at((tx,ty))
        # Convertir de [0,255] a [-1,1]
        nx = ncol.r/255*2-1
        ny = ncol.g/255*2-1
        nz = ncol.b/255*2-1
        # Si hay tangentes y bitangentes interpoladas, construir TBN
        t_list = fragment_data.get('tangents')
        b_list = fragment_data.get('bitangents')
        if t_list and b_list and len(t_list) >=3 and len(b_list) >=3 and fragment_data.get('normals'):
            # Interpolar T, B, N
            T = [
                w0*t_list[0][0] + w1*t_list[1][0] + w2*t_list[2][0],
                w0*t_list[0][1] + w1*t_list[1][1] + w2*t_list[2][1],
                w0*t_list[0][2] + w1*t_list[1][2] + w2*t_list[2][2],
            ]
            B = [
                w0*b_list[0][0] + w1*b_list[1][0] + w2*b_list[2][0],
                w0*b_list[0][1] + w1*b_list[1][1] + w2*b_list[2][1],
                w0*b_list[0][2] + w1*b_list[1][2] + w2*b_list[2][2],
            ]
            # Re-normalizar T,B,N
            def nrm(v):
                m=(v[0]**2+v[1]**2+v[2]**2)**0.5 or 1
                v[0]/=m; v[1]/=m; v[2]/=m
            nrm(T); nrm(B); nrm(N)
            # Construir matriz TBN (columnas)
            # Tangent-space normal
            Nt = [nx, ny, max(0.0, nz)]  # asegurar componente Z positiva
            # Transformar: worldN = T*Nt.x + B*Nt.y + N*Nt.z
            N = [
                T[0]*Nt[0] + B[0]*Nt[1] + N[0]*Nt[2],
                T[1]*Nt[0] + B[1]*Nt[1] + N[1]*Nt[2],
                T[2]*Nt[0] + B[2]*Nt[1] + N[2]*Nt[2],
            ]
        else:
            # Fallback: mezcla simple
            N = [
                0.5*N[0] + 0.5*nx,
                0.5*N[1] + 0.5*ny,
                0.5*N[2] + 0.5*nz,
            ]
    # Normalizar
    mag = (N[0]**2+N[1]**2+N[2]**2)**0.5 or 1
    N = [N[0]/mag, N[1]/mag, N[2]/mag]
    # Luz direccional
    L = [0.5,0.7,0.5]
    lm = (L[0]**2+L[1]**2+L[2]**2)**0.5 or 1
    L = [L[0]/lm, L[1]/lm, L[2]/lm]
    diff = max(0, N[0]*L[0]+N[1]*L[1]+N[2]*L[2])
    ambient = 0.2
    outc = [min(1, base[i]*(ambient+diff)) for i in range(3)]
    prev = fragment_data.get('prev_color')
    if prev:
        return [min(1, outc[i]*0.7 + prev[i]*0.7) for i in range(3)]
    return outc