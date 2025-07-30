from model import Model

def objToModel(obj, texture_file=None):
    model = Model()
    model.texture_file = texture_file
    
    for face, tex_face in obj.faces:
        # Si hay coordenadas de textura disponibles
        if tex_face and len(tex_face) == len(face): # Asumimos que tex_face es una lista de índices de coordenadas UV
            for i, vertex_idx in enumerate(face):
                # Añadir vértices (x, y, z)
                vertex = obj.vertices[vertex_idx]
                model.vertices.extend(vertex)
                # Añadir coordenadas de textura (u, v)
                uv = obj.tex_coords[tex_face[i]]
                model.vertices.extend(uv)
        else:
            # Sin coordenadas de textura, solo vértices
            for vertex_idx in face:
                vertex = obj.vertices[vertex_idx]
                model.vertices.extend(vertex)
    
    return model