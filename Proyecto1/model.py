from MathLib import *


class Model(object):
    """
    Clase que representa un modelo 3D simple con transformaciones y vertices.
    Permite definir la posición, rotación, escala y un vertex shader opcional.
    """
    def __init__(self):
        # Lista de vértices del modelo (x, y, z, ...)
        self.vertices = []

        # Normales por vértice
        self.normals = []

        # Tangentes y bitangentes (normal mapping)
        self.tangents = []
        self.bitangents = []

        # Multi-textura / materiales
        self.textures = {}
        self.materialIndices = []
        self.materials = {}

        # Transformaciones
        self.translation = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.scale = [1, 1, 1]

        # Shaders asociados
        self.vertexShader = None
        self.fragmentShader = None
        self.fragmentShaderChain = []  # lista de tuplas (key, func)

        # Nombre legible del modelo (para UI). Puede asignarse externamente.
        self.name = None

    # ---- Toggle helpers ----
    def toggle_fragment_shader(self, key, func):
        """Activa/desactiva un fragment shader identificado por key.
        Devuelve True si quedó activado, False si se desactivó."""
        for i,(k,f) in enumerate(self.fragmentShaderChain):
            if k == key:
                self.fragmentShaderChain.pop(i)
                return False
        self.fragmentShaderChain.append((key, func))
        self.fragmentShader = None
        return True

    def clear_fragment_chain(self):
        self.fragmentShaderChain.clear()

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
    
    def addMaterial(self, name, texture_name=None, color=None, normal_map=None, ao_map=None, roughness_map=None):
        """
        Agrega un material al modelo.
        Args:
            name: Nombre del material
            texture_name: Nombre de la textura asociada (opcional)
            color: Color por defecto del material [r, g, b] (opcional)
        """
        material = {
            'texture': texture_name,
            'color': color or [1.0, 1.0, 1.0],  # Blanco por defecto
            'normal_map': normal_map,          # nombre de textura de normal map
            'ao_map': ao_map,                  # opcional ambient occlusion
            'roughness_map': roughness_map     # opcional roughness
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

    def getNormalMapForTriangle(self, triangle_index):
        material_name = self.getTriangleMaterial(triangle_index)
        if material_name in self.materials:
            nm = self.materials[material_name].get('normal_map')
            if nm and nm in self.textures:
                return self.textures[nm]
        return None

    def getAuxTexture(self, triangle_index, key):
        material_name = self.getTriangleMaterial(triangle_index)
        if material_name in self.materials:
            tex_name = self.materials[material_name].get(key)
            if tex_name and tex_name in self.textures:
                return self.textures[tex_name]
        return None

    def calculateTangents(self):
        """Calcula tangentes y bitangentes por vértice basadas en posiciones y UV.
        Asume layout de 5 floats por vértice (x,y,z,u,v)."""
        if not self.vertices:
            return
        has_uv = len(self.vertices) % 5 == 0
        if not has_uv:
            return
        vertex_size = 5
        vcount = len(self.vertices) // vertex_size
        self.tangents = [[0.0,0.0,0.0] for _ in range(vcount)]
        self.bitangents = [[0.0,0.0,0.0] for _ in range(vcount)]
        for i in range(0, vcount - 2, 3):
            # índices de vértices del triángulo
            i0, i1, i2 = i, i+1, i+2
            # posiciones
            p0 = self.vertices[i0*vertex_size:i0*vertex_size+3]
            p1 = self.vertices[i1*vertex_size:i1*vertex_size+3]
            p2 = self.vertices[i2*vertex_size:i2*vertex_size+3]
            # uvs
            uv0 = self.vertices[i0*vertex_size+3:i0*vertex_size+5]
            uv1 = self.vertices[i1*vertex_size+3:i1*vertex_size+5]
            uv2 = self.vertices[i2*vertex_size+3:i2*vertex_size+5]
            # edges
            edge1 = [p1[j]-p0[j] for j in range(3)]
            edge2 = [p2[j]-p0[j] for j in range(3)]
            duv1 = [uv1[0]-uv0[0], uv1[1]-uv0[1]]
            duv2 = [uv2[0]-uv0[0], uv2[1]-uv0[1]]
            denom = duv1[0]*duv2[1] - duv2[0]*duv1[1]
            if abs(denom) < 1e-8:
                continue
            r = 1.0 / denom
            tx = (edge1[0]*duv2[1] - edge2[0]*duv1[1]) * r
            ty = (edge1[1]*duv2[1] - edge2[1]*duv1[1]) * r
            tz = (edge1[2]*duv2[1] - edge2[2]*duv1[1]) * r
            bx = (edge2[0]*duv1[0] - edge1[0]*duv2[0]) * r
            by = (edge2[1]*duv1[0] - edge1[1]*duv2[0]) * r
            bz = (edge2[2]*duv1[0] - edge1[2]*duv2[0]) * r
            tan = [tx,ty,tz]
            bit = [bx,by,bz]
            for vid in (i0,i1,i2):
                for j in range(3):
                    self.tangents[vid][j] += tan[j]
                    self.bitangents[vid][j] += bit[j]
        # Normalizar
        def norm(v):
            mag = (v[0]**2+v[1]**2+v[2]**2)**0.5
            if mag>0:
                v[0]/=mag; v[1]/=mag; v[2]/=mag
        for v in self.tangents: norm(v)
        for v in self.bitangents: norm(v)

    # ---------------------- UTILIDADES MULTI-TEXTURA ----------------------
    def ensure_complete_material_assignment(self, default_material):
        """Garantiza que cada triángulo tenga un material válido asignado.

        Reemplaza 'default', cadenas vacías o materiales inexistentes con 'default_material'
        si éste existe en self.materials. Si no existe, no realiza cambios.
        """
        if default_material not in self.materials:
            return
        for i, m in enumerate(self.materialIndices):
            if (not m) or (m == 'default') or (m not in self.materials):
                self.materialIndices[i] = default_material

    def material_coverage_report(self):
        """Genera un resumen de cobertura de materiales/texturas.

        Returns:
            dict con:
              total_triangles
              material_counts {material: count}
              textured_triangles (cuantos tienen textura asociada)
              untextured_triangles
              percent_textured (0-100)
        """
        total = len(self.materialIndices)
        counts = {}
        textured = 0
        for idx, mname in enumerate(self.materialIndices):
            counts[mname] = counts.get(mname, 0) + 1
            # Determinar si tiene textura
            tex_present = False
            if mname in self.materials:
                tex_name = self.materials[mname].get('texture')
                if tex_name and tex_name in self.textures:
                    tex_present = True
            if tex_present:
                textured += 1
        percent = (textured / total * 100) if total > 0 else 0
        return {
            'total_triangles': total,
            'material_counts': counts,
            'textured_triangles': textured,
            'untextured_triangles': total - textured,
            'percent_textured': percent
        }