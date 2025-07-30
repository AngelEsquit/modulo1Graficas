import numpy as np

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