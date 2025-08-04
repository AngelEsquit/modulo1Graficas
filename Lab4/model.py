from MathLib import *


class Model(object):
    """
    Clase que representa un modelo 3D simple con transformaciones y vertices.
    Permite definir la posición, rotación, escala y un vertex shader opcional.
    """
    def __init__(self):
        # Lista de vértices del modelo (x, y, z, ...)
        self.vertices = [ ]
        
        # NUEVO: Lista de normales por vértice
        self.normals = [ ]
        
        # NUEVO: Soporte para múltiples texturas
        self.textures = {}  # Diccionario de texturas {nombre: textura}
        self.materialIndices = []  # Índice de material por triángulo/cara
        self.materials = {}  # Diccionario de materiales {nombre: info_material}

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
    
    def calculateNormals(self):
        """
        Calcula las normales por vértice basándose en la geometría.
        Asume que los vértices están organizados en triángulos.
        """
        if len(self.vertices) < 9:  # Necesitamos al menos 3 vértices (un triángulo)
            return
        
        # Determinar el tamaño de cada vértice (3 para xyz, 5 para xyz+uv)
        vertex_size = 5 if len(self.vertices) % 5 == 0 else 3
        vertex_count = len(self.vertices) // vertex_size
        
        # Inicializar normales con ceros
        self.normals = [[0, 0, 0] for _ in range(vertex_count)]
        normal_counts = [0] * vertex_count
        
        # Calcular normales por cara y acumular
        for i in range(0, len(self.vertices) - vertex_size * 2, vertex_size * 3):
            # Obtener los tres vértices del triángulo
            v0 = self.vertices[i:i+3]
            v1 = self.vertices[i+vertex_size:i+vertex_size+3]
            v2 = self.vertices[i+vertex_size*2:i+vertex_size*2+3]
            
            # Calcular vectores del triángulo
            edge1 = [v1[j] - v0[j] for j in range(3)]
            edge2 = [v2[j] - v0[j] for j in range(3)]
            
            # Producto cruzado para obtener la normal
            normal = [
                edge1[1] * edge2[2] - edge1[2] * edge2[1],
                edge1[2] * edge2[0] - edge1[0] * edge2[2],
                edge1[0] * edge2[1] - edge1[1] * edge2[0]
            ]
            
            # Normalizar
            magnitude = (normal[0]**2 + normal[1]**2 + normal[2]**2)**0.5
            if magnitude > 0:
                normal = [normal[j] / magnitude for j in range(3)]
            
            # Acumular normales en los vértices correspondientes
            for vertex_idx in range(3):
                idx = (i // vertex_size) + vertex_idx
                if idx < len(self.normals):
                    for j in range(3):
                        self.normals[idx][j] += normal[j]
                    normal_counts[idx] += 1
        
        # Promediar las normales acumuladas
        for i in range(len(self.normals)):
            if normal_counts[i] > 0:
                for j in range(3):
                    self.normals[i][j] /= normal_counts[i]
                
                # Renormalizar
                magnitude = (self.normals[i][0]**2 + self.normals[i][1]**2 + self.normals[i][2]**2)**0.5
                if magnitude > 0:
                    for j in range(3):
                        self.normals[i][j] /= magnitude
    
    def addTexture(self, name, texture_path_or_surface):
        """
        Agrega una textura al modelo.
        Args:
            name: Nombre identificador de la textura
            texture_path_or_surface: Ruta del archivo o superficie de pygame ya cargada
        """
        if isinstance(texture_path_or_surface, str):
            # Si es una ruta, cargar la textura
            import pygame
            try:
                texture = pygame.image.load(texture_path_or_surface)
                self.textures[name] = texture
                print(f"Textura '{name}' cargada desde {texture_path_or_surface}")
                return True
            except Exception as e:
                print(f"Error al cargar textura '{name}': {e}")
                return False
        else:
            # Si ya es una superficie de pygame
            self.textures[name] = texture_path_or_surface
            print(f"Textura '{name}' agregada")
            return True
    
    def addMaterial(self, name, texture_name=None, color=None):
        """
        Agrega un material al modelo.
        Args:
            name: Nombre del material
            texture_name: Nombre de la textura asociada (opcional)
            color: Color por defecto del material [r, g, b] (opcional)
        """
        material = {
            'texture': texture_name,
            'color': color or [1.0, 1.0, 1.0]  # Blanco por defecto
        }
        self.materials[name] = material
        print(f"Material '{name}' agregado")
    
    def setTriangleMaterial(self, triangle_index, material_name):
        """
        Asigna un material a un triángulo específico.
        Args:
            triangle_index: Índice del triángulo (0, 1, 2, ...)
            material_name: Nombre del material a asignar
        """
        # Asegurar que la lista sea lo suficientemente grande
        while len(self.materialIndices) <= triangle_index:
            self.materialIndices.append("default")
        
        self.materialIndices[triangle_index] = material_name
    
    def getTriangleMaterial(self, triangle_index):
        """
        Obtiene el material de un triángulo específico.
        Args:
            triangle_index: Índice del triángulo
        Returns:
            Nombre del material o "default"
        """
        if triangle_index < len(self.materialIndices):
            return self.materialIndices[triangle_index]
        return "default"
    
    def getTextureForTriangle(self, triangle_index):
        """
        Obtiene la textura correspondiente a un triángulo específico.
        Args:
            triangle_index: Índice del triángulo
        Returns:
            Superficie de pygame de la textura o None
        """
        material_name = self.getTriangleMaterial(triangle_index)
        if material_name in self.materials:
            material = self.materials[material_name]
            texture_name = material.get('texture')
            if texture_name and texture_name in self.textures:
                return self.textures[texture_name]
        return None
    
    def getMaterialColorForTriangle(self, triangle_index):
        """
        Obtiene el color del material para un triángulo específico.
        Args:
            triangle_index: Índice del triángulo
        Returns:
            Color [r, g, b] del material
        """
        material_name = self.getTriangleMaterial(triangle_index)
        if material_name in self.materials:
            return self.materials[material_name]['color']
        return [1.0, 1.0, 1.0]  # Blanco por defecto