class Renderer(object):
    def __init__(self, screen):
        self.screen = screen
        _, _, self.width, self.height = screen.get_rect()

        self.glColor(1, 1, 1) # Color del pincel
        self.glClearColor(0, 0, 0) # Color de fondo
        self.glClear() # Limpia la pantalla

    def glClearColor(self, r, g, b): # Establece el color de fondo
        r = min(1, max(0, r))
        g = min(1, max(0, g))
        b = min(1, max(0, b))
        self.clearColor = [r, g, b]

    def glColor(self, r, g, b): # Establece el color del pincel
        r = min(1, max(0, r))
        g = min(1, max(0, g))
        b = min(1, max(0, b))

        self.currentColor = [r, g, b]

    def glClear(self): # Limpia la pantalla con el color de fondo
        color = [int(c * 255) for c in self.clearColor]
        self.screen.fill(color)

        self.framebuffer = [[color[:] for y in range(self.height)] for x in range(self.width)]

    def glPoint(self, x, y, color = None): # Dibuja un punto en la pantalla
        x = round(x)
        y = round(y)

        if (0 <= x < self.width) and (0 <= y < self.height):
            color = [int(i * 255) for i in (color or self.currentColor)]
            self.screen.set_at((x, self.height - 1 - y), color)
            self.framebuffer[x][y] = color

    def glLine(self, p0, p1, color = None): # Dibuja una línea entre dos puntos
        x0, y0 = p0
        x1, y1 = p1

        # Algoritmo de Bresenham para dibujar líneas
        if x0 == x1 and y0 == y1:
            self.glPoint(x0, y0, color)
            return
        
        dy = y1 - y0
        dx = x1 - x0
        steep = abs(dy) > abs(dx)

        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1

        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        
        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        offset = 0
        limit = 0.75

        m = dy / dx
        y = y0

        for x in range(round(x0), round(x1) + 1):
            if steep:
                self.glPoint(y, x, color or self.currentColor)
            else:
                self.glPoint(x, y, color or self.currentColor)
            
            offset += m

            if offset >= limit:
                if y1 > y0:
                    y += 1
                else:
                    y -= 1
                
                limit += 1

    def glFillPolygon(self, vertices, color=None): # Rellena un polígono con el color actual
        if not vertices:
            return

        # Encuentra el rango de Y
        minY = min(v[1] for v in vertices)
        maxY = max(v[1] for v in vertices)

        for y in range(int(minY), int(maxY) + 1):
            # Encuentra intersecciones con las líneas del polígono
            intersections = []
            for i in range(len(vertices)):
                v1 = vertices[i]
                v2 = vertices[(i + 1) % len(vertices)]
                if v1[1] == v2[1]:
                    continue  # Línea horizontal
                if v1[1] < v2[1]:
                    y0, x0, y1, x1 = v1[1], v1[0], v2[1], v2[0]
                else:
                    y0, x0, y1, x1 = v2[1], v2[0], v1[1], v1[0]
                if y0 <= y < y1:
                    # Intersección de la scanline con el borde
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    intersections.append(x)
            intersections.sort()
            # Dibuja líneas entre pares de intersecciones
            for i in range(0, len(intersections), 2):
                if i+1 < len(intersections):
                    x_start = int(round(intersections[i]))
                    x_end = int(round(intersections[i+1]))
                    for x in range(x_start, x_end + 1):
                        self.glPoint(x, y, color or self.currentColor)