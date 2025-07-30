import pygame
import numpy as np
from math import pi, sin, cos, tan, radians
from MathLib import TranslationMatrix, RotationMatrix, ViewMatrix, ProjectionMatrix, ViewportMatrix

# Constantes para los tipos de primitivas
POINTS = 0      # Dibuja puntos
LINES = 1       # Dibuja líneas
TRIANGLES = 2   # Dibuja triángulos

class Renderer(object):
    def __init__(self, screen):
        """
        Inicializa el renderizador con la pantalla de Pygame.
        Establece el estado inicial, colores, buffers y matrices.
        """
        self.screen = screen
        _, _, self.width, self.height = self.screen.get_rect()

        # Propiedades de color y estado
        self.glColor(1, 1, 1)          # Color de dibujo (blanco)
        self.glClearColor(0, 0, 0)     # Color de fondo (negro)
        self.primitiveType = TRIANGLES # Tipo de primitiva (triángulos)
        
        # Buffers y renderizado
        self.frameBuffer = None
        self.zBuffer = None
        self.glClear()

        # Atributos de la escena
        self.models = []              # Lista de modelos a renderizar
        self.textures = {}            # Almacenamiento de texturas
        self.activeTexture = None     # Textura actualmente activa
        
        # Parámetros de la cámara
        self.cameraPos = [0, 0, 5]
        self.cameraRotation = [0, 0, 0]
        
        # Matrices de la tubería de renderizado
        self.modelMatrix = np.identity(4)
        self.viewMatrix = None
        self.projectionMatrix = None
        self.viewportMatrix = None

    def glClearColor(self, r, g, b):
        """Define el color de fondo (0-1)."""
        self.clearColor = [max(0, min(1, c)) for c in (r, g, b)]

    def glColor(self, r, g, b):
        """Define el color actual de dibujo (0-1)."""
        self.currColor = [max(0, min(1, c)) for c in (r, g, b)]

    def glClear(self):
        """Limpia la pantalla y los buffers con el color de fondo."""
        color = [int(i * 255) for i in self.clearColor]
        self.screen.fill(color)
        
        self.frameBuffer = [[color[:] for _ in range(self.height)] for _ in range(self.width)]
        self.zBuffer = [[float('inf') for _ in range(self.height)] for _ in range(self.width)]

    def glPoint(self, x, y, z=0, color=None):
        """
        Dibuja un punto en las coordenadas de pantalla (x, y) con z-buffer.
        """
        x, y = round(x), round(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            if z < self.zBuffer[x][y]:
                self.zBuffer[x][y] = z
                draw_color = [int(i * 255) for i in (color or self.currColor)]
                self.screen.set_at((x, self.height - 1 - y), draw_color)
                self.frameBuffer[x][y] = draw_color

    def glLine(self, p0, p1, color=None):
        """
        Algoritmo de línea de Bresenham con interpolación de Z.
        """
        x0, y0, z0 = p0
        x1, y1, z1 = p1
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        steep = dy > dx

        if steep:
            x0, y0, z0, x1, y1, z1 = y0, x0, z0, y1, x1, z1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
            z0, z1 = z1, z0

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        offset = 0
        limit = 0.5
        m = dy / dx if dx != 0 else 0
        y = y0
        
        for x in range(int(round(x0)), int(round(x1)) + 1):
            t = (x - x0) / (x1 - x0) if (x1 - x0) != 0 else 0
            z = z0 + (z1 - z0) * t
            
            if steep:
                self.glPoint(y, x, z, color)
            else:
                self.glPoint(x, y, z, color)

            offset += m
            if offset >= limit:
                y += 1 if y0 < y1 else -1
                limit += 1

    def glTriangle(self, A, B, C, uv_coords=None):
        """
        Rasteriza un triángulo utilizando el método de bounding box y coordenadas baricéntricas.
        """
        minX = max(0, int(min(A[0], B[0], C[0])))
        maxX = min(self.width - 1, int(max(A[0], B[0], C[0])))
        minY = max(0, int(min(A[1], B[1], C[1])))
        maxY = min(self.height - 1, int(max(A[1], B[1], C[1])))

        def edge(p1, p2, p):
            return (p[0] - p1[0]) * (p2[1] - p1[1]) - (p[1] - p1[1]) * (p2[0] - p1[0])

        area = edge(A, B, C)
        if area == 0:
            return

        for x in range(minX, maxX + 1):
            for y in range(minY, maxY + 1):
                P = (x + 0.5, y + 0.5)
                w0 = edge(B, C, P) / area
                w1 = edge(C, A, P) / area
                w2 = edge(A, B, P) / area
                if w0 >= 0 and w1 >= 0 and w2 >= 0:
                    z = w0 * A[2] + w1 * B[2] + w2 * C[2]
                    
                    if uv_coords and self.activeTexture:
                        u = w0 * uv_coords[0][0] + w1 * uv_coords[1][0] + w2 * uv_coords[2][0]
                        v = w0 * uv_coords[0][1] + w1 * uv_coords[1][1] + w2 * uv_coords[2][1]
                        
                        tex_x = int(u * (self.activeTexture.get_width() - 1))
                        tex_y = int((1 - v) * (self.activeTexture.get_height() - 1))
                        
                        color = self.activeTexture.get_at((tex_x, tex_y))
                        color = [color.r/255, color.g/255, color.b/255]
                    else:
                        color = self.currColor
                    
                    self.glPoint(x, y, z, color)

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
        """Aplica transformaciones, shaders y dibuja un solo modelo."""
        self.modelMatrix = model.GetModelMatrix()
        self.activeTexture = self.textures.get(id(model), None)
        self.activeVertexShader = model.vertexShader
        
        processed_vertices = []
        uv_coords = []
        
        has_uv = len(model.vertices) > 0 and len(model.vertices) % 5 == 0
        vertex_size = 5 if has_uv else 3
        
        for i in range(0, len(model.vertices), vertex_size):
            vertex = model.vertices[i:i + 3]
            if has_uv:
                uv = model.vertices[i + 3:i + 5]
                uv_coords.append(uv)

            # 1. Aplicar el vertex shader
            if self.activeVertexShader:
                v_transformed = self.activeVertexShader(
                    vertex,
                    modelMatrix=self.modelMatrix,
                    viewMatrix=self.viewMatrix
                )
            else:
                # Si no hay shader, solo aplicar matrices
                v_transformed = np.array([*vertex, 1]) @ (self.viewMatrix @ self.modelMatrix).T

            # 2. Aplicar la matriz de proyección
            v4 = np.matrix([[v_transformed[0]], [v_transformed[1]], [v_transformed[2]], [1]])
            v_proj = self.projectionMatrix @ v4
            
            # 3. Normalizar por W (dividir por el 4to componente)
            v_proj = v_proj.tolist()
            w = v_proj[3][0] if v_proj[3][0] != 0 else 1
            x_norm = v_proj[0][0] / w
            y_norm = v_proj[1][0] / w
            z_norm = v_proj[2][0] / w

            # 4. Aplicar la matriz de viewport
            x_screen = int((x_norm + 1) * 0.5 * self.width)
            y_screen = int((y_norm + 1) * 0.5 * self.height)
            
            processed_vertices.extend([x_screen, y_screen, z_norm])
            
        self.glDrawPrimitives(processed_vertices, 3, uv_coords if has_uv else None)


    def glDrawPrimitives(self, buffer, vertexOffset, uvBuffer=None):
        """Dibuja las primitivas basadas en el tipo actual."""
        if self.primitiveType == POINTS:
            for i in range(0, len(buffer), vertexOffset):
                self.glPoint(buffer[i], buffer[i+1], buffer[i+2])
        elif self.primitiveType == LINES:
            for i in range(0, len(buffer), vertexOffset * 3):
                p0 = [buffer[i], buffer[i+1], buffer[i+2]]
                p1 = [buffer[i+3], buffer[i+4], buffer[i+5]]
                p2 = [buffer[i+6], buffer[i+7], buffer[i+8]]
                self.glLine(p0, p1)
                self.glLine(p1, p2)
                self.glLine(p2, p0)
        elif self.primitiveType == TRIANGLES:
            for i in range(0, len(buffer), vertexOffset * 3):
                A = buffer[i:i + vertexOffset]
                B = buffer[i + vertexOffset:i + 2 * vertexOffset]
                C = buffer[i + 2 * vertexOffset:i + 3 * vertexOffset]
                
                uv_coords_triangle = None
                if uvBuffer:
                    uv_coords_triangle = [uvBuffer[j] for j in range(i//vertexOffset, i//vertexOffset + 3)]

                self.glTriangle(A, B, C, uv_coords_triangle)

    def glRender(self):
        """El método principal de renderizado que orquesta todo el proceso."""
        self._setup_rendering_pipeline()
        self._draw_all_models()