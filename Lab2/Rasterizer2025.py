import pygame
from gl import *
from BMP_Writer import GenerateBMP
from model import Model
from shaders import *
from obj import load_obj

def load_obj_to_model(filename, model):
	# Carga un archivo OBJ y convierte las caras en vértices para el modelo
	vertices, faces = load_obj(filename)
	model.vertices = []
	
	# Convertir caras a lista de vértices para triángulos
	for face in faces:
		# Solo procesar triángulos (caras con 3 vértices)
		if len(face) >= 3:
			# Tomar los primeros 3 vértices para formar un triángulo
			for i in range(3):
				vertex_idx = face[i]
				if vertex_idx < len(vertices):
					vertex = vertices[vertex_idx]
					model.vertices.extend([vertex[0], vertex[1], vertex[2]])
	
	model.faces = faces
	return len(vertices), len(faces)

width = 256
height = 256

screen = pygame.display.set_mode((width, height), pygame.SCALED)
clock = pygame.time.Clock()

rend = Renderer(screen)

# Cargar modelo OBJ
objModel = Model()

# Cargar datos del archivo OBJ usando la función auxiliar para leer el archivo
num_vertices, num_faces = load_obj_to_model("models/sphere.obj", objModel)

objModel.vertexShader = vertexShader

# Escalar el modelo para que sea visible en pantalla
objModel.scale = [60, 60, 60]  # Aumentar el tamaño
objModel.translation = [128, 128, -100]  # Centrar en pantalla y alejar en Z

print(f"Modelo cargado: {num_vertices} vértices, {num_faces} caras")

rend.models.append(objModel)


isRunning = True
while isRunning:

	deltaTime = clock.tick(60) / 1000.0


	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			isRunning = False

		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_1:
				rend.primitiveType = POINTS

			elif event.key == pygame.K_2:
				rend.primitiveType = LINES

			elif event.key == pygame.K_3:
				rend.primitiveType = TRIANGLES

			elif event.key == pygame.K_4:
				# Cargar modelo face.obj
				try:
					num_vertices, num_faces = load_obj_to_model("models/face.obj", objModel)
					objModel.scale = [10, 10, 10]
					objModel.translation = [128, 128, 0]
					print(f"Cargado face.obj: {num_vertices} vértices, {num_faces} caras")
				except Exception as e:
					print(f"Error cargando face.obj: {e}")

			elif event.key == pygame.K_5:
				# Cargar modelo model.obj
				try:
					num_vertices, num_faces = load_obj_to_model("models/model.obj", objModel)
					objModel.scale = [50, 50, 50]  # Diferente escala
					objModel.translation = [128, 128, 0]
					print(f"Cargado model.obj: {num_vertices} vértices, {num_faces} caras")
				except Exception as e:
					print(f"Error cargando model.obj: {e}")



	keys = pygame.key.get_pressed()

	if keys[pygame.K_RIGHT]:
		objModel.translation[0] += 10 * deltaTime
	if keys[pygame.K_LEFT]:
		objModel.translation[0] -= 10 * deltaTime
	if keys[pygame.K_UP]:
		objModel.translation[1] += 10 * deltaTime
	if keys[pygame.K_DOWN]:
		objModel.translation[1] -= 10 * deltaTime

	# Controles para el eje Z (profundidad)
	if keys[pygame.K_r]:
		objModel.translation[2] += 10 * deltaTime  # Alejar
	if keys[pygame.K_f]:
		objModel.translation[2] -= 10 * deltaTime  # Acercar


	if keys[pygame.K_d]:
		objModel.rotation[1] += 20 * deltaTime  # Rotar en eje Y (izquierda a derecha)
	if keys[pygame.K_a]:
		objModel.rotation[1] -= 20 * deltaTime  # Rotar en eje Y (izquierda a derecha)

	# Rotación adicional en otros ejes
	if keys[pygame.K_q]:
		objModel.rotation[0] += 20 * deltaTime  # Rotar en eje X (arriba y abajo)
	if keys[pygame.K_e]:
		objModel.rotation[0] -= 20 * deltaTime  # Rotar en eje X (arriba y abajo)
	
	if keys[pygame.K_z]:
		objModel.rotation[2] += 20 * deltaTime  # Rotar en eje Z (como una rueda)
	if keys[pygame.K_c]:
		objModel.rotation[2] -= 20 * deltaTime  # Rotar en eje Z (como una rueda)

	if keys[pygame.K_w]:
		objModel.scale =  [(i + deltaTime) for i in objModel.scale]
	if keys[pygame.K_s]:
		objModel.scale = [(i - deltaTime) for i in objModel.scale ]

	rend.glClear()

	# Escribir lo que se va a dibujar aqui

	rend.glRender()

	#########################################

	pygame.display.flip()


GenerateBMP("output.bmp", width, height, 3, rend.frameBuffer)

pygame.quit()