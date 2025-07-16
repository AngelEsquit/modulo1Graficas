def load_obj(filename):
    vertices = []
    faces = []

    with open(filename, 'r') as file:
        for line in file:
            if line.startswith('v '):
                # Procesar línea de vértice
                parts = line.strip().split()
                x, y, z = map(float, parts[1:4])
                vertices.append((x, y, z))
            elif line.startswith('f '):
                # Procesar línea de cara
                parts = line.strip().split()[1:]
                face = []
                for part in parts:
                    # Soporta formatos f v/vt/vn o f v//vn o f v
                    idx = part.split('/')[0]
                    face.append(int(idx) - 1)  # -1 porque OBJ indexa desde 1
                faces.append(face)

    return vertices, faces


# Función de prueba (opcional)
def test_load_obj(name):
    """Función para probar la carga de archivos OBJ"""
    try:
        vertices, faces = load_obj("models/" + name + ".obj")
        print(f"Archivo cargado exitosamente:")
        print(f"Número de vértices: {len(vertices)}")
        print(f"Número de caras: {len(faces)}")
        if vertices:
            print(f"Primer vértice: {vertices[0]}")
        if faces:
            print(f"Primera cara: {faces[0]}")
        return True
    except FileNotFoundError:
        print("Archivo no encontrado")
        return False
    except Exception as e:
        print(f"Error al cargar archivo: {e}")
        return False


# Descomenta las siguientes líneas para probar la función
if __name__ == "__main__":
    name = "Male"
    test_load_obj(name)
