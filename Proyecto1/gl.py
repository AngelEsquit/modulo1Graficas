import pygame
import numpy as np
import random
from math import pi, sin, cos, tan, radians
from MathLib import TranslationMatrix, RotationMatrix, ViewMatrix, ProjectionMatrix, ViewportMatrix
from raster_ops import put_pixel, draw_point, draw_line, raster_triangle

# Constantes para los tipos de primitivas
POINTS = 0      # Dibuja puntos
LINES = 1       # Dibuja líneas
TRIANGLES = 2   # Dibuja triángulos

class Renderer(object):
    def __init__(self, screen):
        """Inicializa el renderizador con la pantalla y el estado inicial."""
        self.screen = screen
        _, _, self.width, self.height = self.screen.get_rect()

        # Propiedades de color y estado
        self.glColor(1, 1, 1)          # Color de dibujo (blanco)
        self.glClearColor(0, 0, 0)     # Color de fondo (negro)
        self.primitiveType = TRIANGLES # Tipo de primitiva por defecto

        # Buffers y renderizado
        self.frameBuffer = None
        self.zBuffer = None

        # Atributos de la escena
        self.models = []               # Lista de modelos a renderizar
        self.textures = {}             # Almacenamiento de texturas por modelo
        self.activeTexture = None      # Textura actualmente activa

        # Parámetros de la cámara
        self.cameraPos = [0, 0, 5]
        self.cameraRotation = [0, 0, 0]  # pitch, yaw, roll

        # Control para forzar desactivar texturas (modo triángulos sin textura)
        self.forceNoTexture = False

        # Cache persistente de colores por triángulo
        self.triangleColorCache = {}
        self.externalColorCache = None
        self.triColorCurrent = None
        # Cadena de fragment shaders (lista de funciones) opcional
        self.activeFragmentShaderChain = None

        # Matrices de la tubería de renderizado
        self.modelMatrix = np.identity(4)
        self.viewMatrix = None
        self.projectionMatrix = None
        self.viewportMatrix = None

        # Fondo
        self.backgroundSurface = None

        # Inicializar buffers
        self.glClear()

    def glClearColor(self, r, g, b):
        """Define el color de fondo (0-1)."""
        self.clearColor = [max(0, min(1, c)) for c in (r, g, b)]

    def glColor(self, r, g, b):
        """Define el color actual de dibujo (0-1)."""
        self.currColor = [max(0, min(1, c)) for c in (r, g, b)]

    def glClear(self):
        """Limpia la pantalla y los buffers con el color de fondo."""
        if self.backgroundSurface is not None:
            # Escalar si es necesario
            bg = self.backgroundSurface
            if bg.get_width() != self.width or bg.get_height() != self.height:
                bg = pygame.transform.smoothscale(bg, (self.width, self.height))
            # Blit sobre screen y también inicializar frameBuffer con los pixeles del fondo
            self.screen.blit(bg, (0,0))
            # Convertir a arreglo rápido
            px = pygame.surfarray.pixels3d(self.screen).copy()
            # frameBuffer indexado [x][y]
            self.frameBuffer = [[list(px[x, self.height-1-y]) for y in range(self.height)] for x in range(self.width)]
        else:
            color = [int(i * 255) for i in self.clearColor]
            self.screen.fill(color)
            self.frameBuffer = [[color[:] for _ in range(self.height)] for _ in range(self.width)]
        self.zBuffer = [[float('inf') for _ in range(self.height)] for _ in range(self.width)]

    # glPoint, glLine, glTriangle delegadas a raster_ops
    def glPoint(self, x, y, z=0, color=None):
        put_pixel(self, x, y, z, color or self.currColor)

    def glLine(self, p0, p1, color=None):
        draw_line(self, p0, p1, color or self.currColor)

    def glTriangle(self, A, B, C, uv_coords=None, vertex_colors=None, normals=None, triangle_index=None, tangents=None, bitangents=None):
        raster_triangle(self, A, B, C, uv_coords, vertex_colors, normals, triangle_index, tangents=tangents, bitangents=bitangents)

    # ---- Fragment chain application helper ----
    def apply_fragment_chain(self, fragment_data):
        chain = getattr(self.activeModel, 'fragmentShaderChain', []) if self.activeModel else []
        if chain:
            prev = fragment_data.get('in_color')
            for key, func in chain:
                fragment_data['prev_color'] = prev
                c = func(fragment_data)
                if c is None:
                    return prev or [1,1,1]
                prev = c
            return prev
        if self.activeFragmentShader:
            fragment_data['prev_color'] = None
            return self.activeFragmentShader(fragment_data)
        return fragment_data.get('in_color') or [1,1,1]

    def loadTexture(self, filename, model_id):
        """Carga una textura desde un archivo y la asocia a un modelo."""
        try:
            texture = pygame.image.load(filename)
            self.textures[model_id] = texture
            return True
        except Exception as e:
            print(f"Error al cargar la textura {filename}: {e}")
            return False

    def _setup_rendering_pipeline(self):
        """Prepara las matrices de la tubería de renderizado para el cuadro actual."""
        # Se asume que estos atributos ya están establecidos por el programa principal
        # self.cameraPos, self.cameraRotation, self.projectionMatrix, self.viewportMatrix
        
        # Calcular la matriz de vista
        self.viewMatrix = ViewMatrix(self.cameraPos, self.cameraRotation)

    def _draw_all_models(self):
        """Itera sobre todos los modelos y los dibuja."""
        for model in self.models:
            self._process_model(model)
            
    def _process_model(self, model):
        """Procesa un modelo con soporte para fragment shader simple o cadena, normales y multi-texturas."""
        self.modelMatrix = model.GetModelMatrix()
        # Textura base según modo
        if not getattr(self, 'forceNoTexture', False):
            self.activeTexture = self.textures.get(id(model), None)
        else:
            self.activeTexture = None
        self.activeModel = model
        self.activeVertexShader = model.vertexShader
        self.activeFragmentShader = model.fragmentShader
        chain = getattr(model, 'fragmentShaderChain', []) or []
        self.activeFragmentShaderChain = chain if len(chain) > 0 else None

        processed_vertices = []
        uv_coords = []
        vertex_colors = []
        normals = []
        tangents = []
        bitangents = []
        cam_z_list = []

        has_uv = len(model.vertices) > 0 and len(model.vertices) % 5 == 0
        vertex_size = 5 if has_uv else 3

        for i in range(0, len(model.vertices), vertex_size):
            vertex = model.vertices[i:i+3]
            uv = None
            if has_uv:
                uv = model.vertices[i+3:i+5]
                uv_coords.append(uv)

            if self.activeVertexShader:
                full_vertex = [*vertex, *(uv if uv else [])]
                v_transformed = self.activeVertexShader(full_vertex, modelMatrix=self.modelMatrix, viewMatrix=self.viewMatrix)
                if len(v_transformed) > 5:
                    vertex_colors.append(v_transformed[5:8])
            else:
                v_transformed = np.array([*vertex, 1]) @ (self.viewMatrix @ self.modelMatrix).T

            cam_z = v_transformed[2]
            cam_z_list.append(cam_z)
            if cam_z >= 0:
                processed_vertices.extend([0,0,1])
                continue

            v4 = np.matrix([[v_transformed[0]],[v_transformed[1]],[v_transformed[2]],[1]])
            v_proj = self.projectionMatrix @ v4
            v_proj = v_proj.tolist()
            w = v_proj[3][0] if v_proj[3][0] != 0 else 1
            x_norm = v_proj[0][0] / w
            y_norm = v_proj[1][0] / w
            z_norm = v_proj[2][0] / w
            x_screen = int((x_norm + 1)*0.5*self.width)
            y_screen = int((y_norm + 1)*0.5*self.height)
            processed_vertices.extend([x_screen, y_screen, z_norm])

            normal_idx = i // vertex_size
            if hasattr(model, 'normals') and normal_idx < len(model.normals):
                normals.append(model.normals[normal_idx])
            if hasattr(model, 'tangents') and normal_idx < len(model.tangents):
                tangents.append(model.tangents[normal_idx])
            if hasattr(model, 'bitangents') and normal_idx < len(model.bitangents):
                bitangents.append(model.bitangents[normal_idx])

        self.glDrawPrimitives(
            processed_vertices, 3,
            uv_coords if has_uv else None,
            vertex_colors if vertex_colors else None,
            normals if normals else None,
            camZBuffer=cam_z_list,
            tangentBuffer=tangents if tangents else None,
            bitangentBuffer=bitangents if bitangents else None
        )

    def glDrawPrimitives(self, buffer, vertexOffset, uvBuffer=None, colorBuffer=None, normalBuffer=None, camZBuffer=None, tangentBuffer=None, bitangentBuffer=None):
        """Dibuja primitivas con soporte para colores por vértice, normales y multi-texturas."""
        vertex_size = 3
        vertex_count = len(buffer) // vertex_size
        
        if self.primitiveType == TRIANGLES:
            triangle_index = 0  # NUEVO: Contador de triángulos
            
            for i in range(0, vertex_count - 2, 3):
                A = [buffer[i * vertex_size + j] for j in range(vertex_size)]
                B = [buffer[(i + 1) * vertex_size + j] for j in range(vertex_size)]
                C = [buffer[(i + 2) * vertex_size + j] for j in range(vertex_size)]

                # Clipping simple: si alguno de los tres vértices está detrás de la cámara (z_cam >= 0) saltar triángulo
                if camZBuffer:
                    if i + 2 < len(camZBuffer):
                        if camZBuffer[i] >= 0 or camZBuffer[i+1] >= 0 or camZBuffer[i+2] >= 0:
                            triangle_index += 1
                            continue
                
                uv_coords_triangle = None
                if uvBuffer and len(uvBuffer) > i + 2:
                    uv_coords_triangle = [uvBuffer[i], uvBuffer[i + 1], uvBuffer[i + 2]]
                
                color_coords_triangle = None
                if colorBuffer and len(colorBuffer) > i + 2:
                    color_coords_triangle = [colorBuffer[i], colorBuffer[i + 1], colorBuffer[i + 2]]

                normal_coords_triangle = None
                if normalBuffer and len(normalBuffer) > i + 2:
                    normal_coords_triangle = [normalBuffer[i], normalBuffer[i + 1], normalBuffer[i + 2]]
                tangent_coords_triangle = None
                bitangent_coords_triangle = None
                if tangentBuffer and len(tangentBuffer) > i + 2:
                    tangent_coords_triangle = [tangentBuffer[i], tangentBuffer[i+1], tangentBuffer[i+2]]
                if bitangentBuffer and len(bitangentBuffer) > i + 2:
                    bitangent_coords_triangle = [bitangentBuffer[i], bitangentBuffer[i+1], bitangentBuffer[i+2]]

                # Color RGB persistente si no hay fragment shader
                if (getattr(self, 'activeFragmentShader', None) is None) or self.activeFragmentShader is None:
                    if self.externalColorCache is not None:
                        # Usar cache externo
                        self.triColorCurrent = self.externalColorCache.get(self.activeModel, triangle_index)
                    else:
                        # Fallback interno
                        cache_key = (id(self.activeModel), triangle_index)
                        if cache_key not in self.triangleColorCache:
                            r = random.uniform(0.15, 1.0)
                            g = random.uniform(0.15, 1.0)
                            b = random.uniform(0.15, 1.0)
                            self.triangleColorCache[cache_key] = [r, g, b]
                        self.triColorCurrent = self.triangleColorCache[cache_key]
                else:
                    self.triColorCurrent = None

                # Multi-textura por triángulo (si el modelo define materiales)
                if not getattr(self, 'forceNoTexture', False) and self.activeFragmentShader is not None:
                    try:
                        tex_for_tri = getattr(self.activeModel, 'getTextureForTriangle', lambda idx: None)(triangle_index)
                        if tex_for_tri is not None:
                            self.activeTexture = tex_for_tri
                        else:
                            # Si no hay textura específica, mantener la previa o None
                            pass
                    except Exception:
                        # En caso de error, no interrumpir el render
                        pass
                else:
                    if getattr(self, 'forceNoTexture', False):
                        self.activeTexture = None

                # Pre-capturar normal/ao/roughness maps si el modelo los soporta
                extra_maps = {}
                if hasattr(self.activeModel, 'getNormalMapForTriangle'):
                    try:
                        extra_maps['normal_map'] = self.activeModel.getNormalMapForTriangle(triangle_index)
                    except Exception:
                        extra_maps['normal_map'] = None
                if hasattr(self.activeModel, 'getAuxTexture'):
                    for key in ('ao_map','roughness_map'):
                        try:
                            extra_maps[key] = self.activeModel.getAuxTexture(triangle_index, key.replace('_map',''))
                        except Exception:
                            extra_maps[key] = None
                # Color del material (aunque no haya textura)
                if hasattr(self.activeModel, 'getMaterialColorForTriangle'):
                    try:
                        extra_maps['material_color'] = self.activeModel.getMaterialColorForTriangle(triangle_index)
                    except Exception:
                        extra_maps['material_color'] = [1,1,1]
                # Guardar en renderer para que raster_triangle pueda acceder vía activeFragmentShader
                self._current_extra_maps = extra_maps
                self.glTriangle(A, B, C, uv_coords_triangle, color_coords_triangle, normal_coords_triangle, triangle_index, tangents=tangent_coords_triangle, bitangents=bitangent_coords_triangle)
                triangle_index += 1  # NUEVO: Incrementar contador
        
        elif self.primitiveType == LINES:
            # Para mostrar las aristas de los triángulos como líneas
            for i in range(0, vertex_count - 2, 3):
                # Obtener los tres vértices del triángulo
                A = [buffer[i * vertex_size + j] for j in range(vertex_size)]
                B = [buffer[(i + 1) * vertex_size + j] for j in range(vertex_size)]
                C = [buffer[(i + 2) * vertex_size + j] for j in range(vertex_size)]
                
                # Dibujar las tres aristas del triángulo
                self.glLine(A, B, self.currColor)  # Arista A-B
                self.glLine(B, C, self.currColor)  # Arista B-C
                self.glLine(C, A, self.currColor)  # Arista C-A
        
        elif self.primitiveType == POINTS:
            for i in range(vertex_count):
                point = [buffer[i * vertex_size + j] for j in range(vertex_size)]
                self.glPoint(point[0], point[1], point[2] if len(point) > 2 else 0, self.currColor)

    def glRender(self):
        """El método principal de renderizado que orquesta todo el proceso."""
        self._setup_rendering_pipeline()
        self._draw_all_models()