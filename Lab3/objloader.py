class OBJ:
    def __init__(self, filename):
        self.vertices = []
        self.tex_coords = []  # Coordenadas de textura
        self.faces = []       # Ahora almacenará vértices y coordenadas UV

        with open(filename, "r") as file:
            for line in file.readlines():
                if line.startswith("v "):
                    parts = line.strip().split()
                    x, y, z = map(float, parts[1:4])
                    self.vertices.append((x, y, z))
                    
                elif line.startswith("vt "):
                    parts = line.strip().split()
                    u, v = map(float, parts[1:3])
                    self.tex_coords.append((u, v))
                    
                elif line.startswith("f "):
                    parts = line.strip().split()
                    face = []
                    tex_face = []
                    
                    for p in parts[1:]:
                        vertex_info = p.split('/')
                        # Índice de vértice
                        vertex_idx = int(vertex_info[0]) - 1
                        # Índice de coordenada de textura (si existe)
                        tex_idx = int(vertex_info[1]) - 1 if len(vertex_info) > 1 and vertex_info[1] else None
                        
                        face.append(vertex_idx)
                        if tex_idx is not None:
                            tex_face.append(tex_idx)
                    
                    if len(face) == 3:
                        self.faces.append((face, tex_face if tex_face else None))
                    elif len(face) == 4:
                        # Dividir cuadrilátero en dos triángulos
                        self.faces.append(([face[0], face[1], face[2]], 
                                          [tex_face[0], tex_face[1], tex_face[2]] if tex_face else None))
                        self.faces.append(([face[0], face[2], face[3]], 
                                          [tex_face[0], tex_face[2], tex_face[3]] if tex_face else None))