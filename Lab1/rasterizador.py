import pygame
from gl import Renderer
from BMP_Writer import GenerateBMP

width = 900
height = 450

screen = pygame.display.set_mode((width, height), pygame.SCALED)
clock = pygame.time.Clock()

rend = Renderer(screen)

rend.glClearColor(1, 1, 1)
rend.glColor(0, 0, 0)

poligono1 = [(165, 380), (185, 360), (180, 330), (207, 345), (233, 330), (230, 360), (250, 380), (220, 385), (205, 410), (193, 383)]
poligono2 = [(321, 335), (288, 286), (339, 251), (374, 302)]
poligono3 = [(377, 249), (411, 197), (436, 249)]
poligono4 = [
    (413, 177), (448, 159), (502, 88), (553, 53), (535, 36), (676, 37), (660, 52),
    (750, 145), (761, 179), (672, 192), (659, 214), (615, 214), (632, 230), (580, 230),
    (597, 215), (552, 214), (517, 144), (466, 180)
]
poligono5 = [(682, 175), (708, 120), (735, 148), (739, 170)]


isRunning = True

while isRunning:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            isRunning = False

    rend.glClear()

    # Rellenar polígonos
    rend.glColor(1, 1, 0)  # Amarillo
    rend.glFillPolygon(poligono1)
    rend.glColor(0, 1, 1)  # Cyan
    rend.glFillPolygon(poligono2)
    rend.glColor(1, 0, 1)  # Magenta
    rend.glFillPolygon(poligono3)
    rend.glColor(0.5, 0.5, 0.5)  # Gris
    rend.glFillPolygon(poligono4)
    rend.glColor(1, 1, 1)  # Negro para el agujero
    rend.glFillPolygon(poligono5)

    # Dibuja los bordes para visualización
    for poly in [poligono1, poligono2, poligono3, poligono4]:
        for i in range(len(poly)):
            rend.glLine(poly[i], poly[(i+1)%len(poly)], [0,0,0])
    # Agujero
    for i in range(len(poligono5)):
        rend.glLine(poligono5[i], poligono5[(i+1)%len(poligono5)], [0,0,0])

    pygame.display.flip()
    clock.tick(60)

GenerateBMP("output.bmp", width, height, 3, rend.framebuffer)
pygame.quit()
exit(0)