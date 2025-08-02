import numpy as np
from math import pi, sin, cos, tan, isclose




def TranslationMatrix(x, y, z):
    """
    Genera una matriz de traslación 4x4 para mover un objeto en el espacio 3D.
    Parámetros:
        x, y, z: Desplazamiento en cada eje.
    Retorna:
        Matriz de traslación (numpy.matrix)
    """
    return np.matrix([[1, 0, 0, x],
                     [0, 1, 0, y],
                     [0, 0, 1, z],
                     [0, 0, 0, 1]])




def ScaleMatrix(x, y, z):
    """
    Genera una matriz de escalado 4x4 para cambiar el tamaño de un objeto en el espacio 3D.
    Parámetros:
        x, y, z: Factor de escala en cada eje.
    Retorna:
        Matriz de escalado (numpy.matrix)
    """
    return np.matrix([[x, 0, 0, 0],
                     [0, y, 0, 0],
                     [0, 0, z, 0],
                     [0, 0, 0, 1]])




def RotationMatrix(pitch, yaw, roll):
    """
    Genera una matriz de rotación 4x4 para rotar un objeto en el espacio 3D.
    Parámetros:
        pitch: Rotación sobre el eje X (en grados)
        yaw:   Rotación sobre el eje Y (en grados)
        roll:  Rotación sobre el eje Z (en grados)
    Retorna:
        Matriz de rotación combinada (numpy.matrix)
    """
    # Convertimos los ángulos de grados a radianes
    pitch *= pi/180
    yaw *= pi/180
    roll *= pi/180

    # Matriz de rotación sobre el eje X (pitch)
    pitchMat = np.matrix([[1,0,0,0],
                          [0,cos(pitch),-sin(pitch),0],
                          [0,sin(pitch),cos(pitch),0],
                          [0,0,0,1]])

    # Matriz de rotación sobre el eje Y (yaw)
    yawMat = np.matrix([[cos(yaw),0,sin(yaw),0],
                        [0,1,0,0],
                        [-sin(yaw),0,cos(yaw),0],
                        [0,0,0,1]])

    # Matriz de rotación sobre el eje Z (roll)
    rollMat = np.matrix([[cos(roll),-sin(roll),0,0],
                         [sin(roll),cos(roll),0,0],
                         [0,0,1,0],
                         [0,0,0,1]])

    # Multiplicamos las matrices en orden: pitch * yaw * roll
    return pitchMat * yawMat * rollMat


## Matrices para la tubería de rasterización

def ViewMatrix(position, rotation):
    """
    Genera la matriz de vista (View Matrix) para posicionar la cámara.
    Transforma coordenadas del espacio del mundo al espacio de la cámara.
    
    Parámetros:
        position: Lista de 3 elementos [x, y, z] de la posición de la cámara.
        rotation: Lista de 3 elementos [pitch, yaw, roll] de la rotación de la cámara.
    Retorna:
        Matriz de vista (numpy.matrix)
    """
    # La matriz de vista es la inversa de la matriz de transformación de la cámara
    T = TranslationMatrix(-position[0], -position[1], -position[2])
    R = RotationMatrix(-rotation[0], -rotation[1], -rotation[2])
    return R * T

def ProjectionMatrix(fov, aspect_ratio, near_plane, far_plane):
    """
    Genera la matriz de proyección (Projection Matrix) para la perspectiva.
    Transforma coordenadas del espacio de la cámara al espacio de clip.
    
    Parámetros:
        fov: Campo de visión en grados.
        aspect_ratio: Relación de aspecto de la pantalla (ancho / alto).
        near_plane: Distancia al plano cercano de recorte.
        far_plane: Distancia al plano lejano de recorte.
    Retorna:
        Matriz de proyección (numpy.matrix)
    """
    fov_rad = fov * pi / 180
    
    # Parámetros para la fórmula de perspectiva
    t = near_plane * tan(fov_rad / 2)  # Top
    b = -t                           # Bottom
    r = t * aspect_ratio             # Right
    l = -r                           # Left
    
    A = (far_plane + near_plane) / (near_plane - far_plane)
    B = (2 * far_plane * near_plane) / (near_plane - far_plane)
    
    return np.matrix([
        [2*near_plane/(r-l), 0, (r+l)/(r-l), 0],
        [0, 2*near_plane/(t-b), (t+b)/(t-b), 0],
        [0, 0, A, B],
        [0, 0, -1, 0]
    ])

def ViewportMatrix(width, height):
    """
    Genera la matriz de viewport (Viewport Matrix).
    Transforma coordenadas del espacio de clip (-1 a 1) al espacio de pantalla (píxeles).
    
    Parámetros:
        width: Ancho de la ventana de visualización en píxeles.
        height: Alto de la ventana de visualización en píxeles.
    Retorna:
        Matriz de viewport (numpy.matrix)
    """
    return np.matrix([
        [width/2, 0, 0, width/2],
        [0, height/2, 0, height/2],
        [0, 0, 0.5, 0.5],
        [0, 0, 0, 1]
    ])