from MathLib import *


class Model(object):
    """
    Clase que representa un modelo 3D simple con transformaciones y vertices.
    Permite definir la posición, rotación, escala y un vertex shader opcional.
    """
    def __init__(self):
        # Lista de vértices del modelo (x, y, z, ...)
        self.vertices = [ ]

        # Transformaciones del modelo
        self.translation = [0,0,0]  # Traslación en x, y, z
        self.rotation = [0,0,0]     # Rotación en grados (pitch, yaw, roll)
        self.scale = [1,1,1]        # Escala en x, y, z

        # Shaders asociados al modelo
        self.vertexShader = None    # Función para transformar vértices
        self.fragmentShader = None  # Función para calcular color de fragmentos

    # Model
    def GetModelMatrix(self):
        """
        Calcula la matriz de transformación del modelo combinando traslación, rotación y escala.
        Retorna:
            Matriz 4x4 de transformación (numpy.matrix)
        """
        # Matriz de traslación
        translateMat = TranslationMatrix(self.translation[0],
                                         self.translation[1],
                                         self.translation[2])

        # Matriz de rotación
        rotateMat = RotationMatrix(self.rotation[0],
                                   self.rotation[1],
                                   self.rotation[2])

        # Matriz de escala
        scaleMat = ScaleMatrix(self.scale[0],
                               self.scale[1],
                               self.scale[2])

        # Multiplicación de matrices: traslación * rotación * escala
        return translateMat * rotateMat * scaleMat