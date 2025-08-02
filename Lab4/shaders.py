import numpy as np
import math
import time

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
    color = hsv_to_rgb(hue, 0.8, 0.9)
    
    # Asegurar que los valores estén en el rango [0, 1]
    return [max(0, min(1, c)) for c in color]

def textureFragmentShader(fragment_data):
    """Fragment shader para texturas con interpolación"""
    if fragment_data['uv_coords'] and fragment_data['texture']:
        w0, w1, w2 = fragment_data['barycentric']
        uv_coords = fragment_data['uv_coords']
        
        # Interpolar UV
        u = w0 * uv_coords[0][0] + w1 * uv_coords[1][0] + w2 * uv_coords[2][0]
        v = w0 * uv_coords[0][1] + w1 * uv_coords[1][1] + w2 * uv_coords[2][1]
        
        # Muestrear textura
        texture = fragment_data['texture']
        tex_x = int(u * (texture.get_width() - 1))
        tex_y = int((1 - v) * (texture.get_height() - 1))
        
        color = texture.get_at((tex_x, tex_y))
        return [color.r/255, color.g/255, color.b/255]
    
    return [1, 1, 1]  # Blanco por defecto

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
    """Fragment shader que crea un efecto toon/cartoon"""
    x, y, z = fragment_data['position']
    
    # Crear efecto de bandas de color
    intensity = (math.sin(x * 0.1) + math.sin(y * 0.1)) * 0.5 + 0.5
    
    # Cuantizar la intensidad para efecto toon
    if intensity > 0.8:
        return [1.0, 0.8, 0.2]  # Amarillo brillante
    elif intensity > 0.6:
        return [1.0, 0.4, 0.1]  # Naranja
    elif intensity > 0.4:
        return [0.8, 0.2, 0.2]  # Rojo
    elif intensity > 0.2:
        return [0.4, 0.1, 0.6]  # Purple
    else:
        return [0.1, 0.1, 0.4]  # Azul oscuro

# VERTEX SHADERS

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