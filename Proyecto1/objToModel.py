from model import Model

def objToModel(obj, texture_file=None):
    model = Model()
    model.texture_file = texture_file

    # Procesar caras y opcionalmente UVs
    for face_index, (face, tex_face) in enumerate(obj.faces):
        # Determinar material de la cara si está disponible
        material_name = None
        if hasattr(obj, 'face_materials') and obj.face_materials:
            if face_index < len(obj.face_materials):
                material_name = obj.face_materials[face_index]

        # Si hay coordenadas de textura disponibles
        if tex_face and len(tex_face) == len(face):
            for i, vertex_idx in enumerate(face):
                vertex = obj.vertices[vertex_idx]
                model.vertices.extend(vertex)
                uv = obj.tex_coords[tex_face[i]]
                model.vertices.extend(uv)
        else:
            for vertex_idx in face:
                vertex = obj.vertices[vertex_idx]
                model.vertices.extend(vertex)

        # Registrar material por triángulo si existe
        if material_name is not None:
            model.materialIndices.append(material_name)
        else:
            model.materialIndices.append("default")

    # Crear materiales desde obj.materials (si existen)
    if hasattr(obj, 'materials') and obj.materials:
        for mname, mdata in obj.materials.items():
            # Textura difusa map_Kd
            tex_name = None
            if 'map_Kd' in mdata:
                tex_rel = mdata['map_Kd']
                import os
                full_path = os.path.join(os.path.dirname(obj.path), tex_rel)
                if os.path.isfile(full_path):
                    tex_name = f"mtl_{mname}_diffuse"
                    model.addTexture(tex_name, full_path)
            # Color difuso Kd
            color = None
            if 'Kd' in mdata:
                kd = mdata['Kd']
                if len(kd) == 3:
                    color = kd
            model.addMaterial(mname, texture_name=tex_name, color=color)

    # Si el modelo NO tiene UVs (len % 5 != 0) pero queremos aplicar una textura
    # generamos coordenadas UV procedurales (proyección caja en ejes de mayor extensión).
    if texture_file and model.vertices and (len(model.vertices) % 5 != 0):
        verts = model.vertices
        # Extraer posiciones
        positions = []
        for i in range(0, len(verts), 3):
            positions.append(verts[i:i+3])
        # Calcular bounding box
        xs = [p[0] for p in positions]; ys = [p[1] for p in positions]; zs = [p[2] for p in positions]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        extent_x = max_x - min_x or 1.0
        extent_y = max_y - min_y or 1.0
        extent_z = max_z - min_z or 1.0
        # Elegir par de ejes con mayor área para proyección (simple heurística)
        area_xy = extent_x * extent_y
        area_xz = extent_x * extent_z
        area_yz = extent_y * extent_z
        if area_xy >= area_xz and area_xy >= area_yz:
            # Usar X,Y
            def uv_from(p):
                u = (p[0]-min_x)/extent_x
                v = (p[1]-min_y)/extent_y
                return u, v
        elif area_xz >= area_yz:
            # Usar X,Z
            def uv_from(p):
                u = (p[0]-min_x)/extent_x
                v = (p[2]-min_z)/extent_z
                return u, v
        else:
            # Usar Y,Z
            def uv_from(p):
                u = (p[1]-min_y)/extent_y
                v = (p[2]-min_z)/extent_z
                return u, v
        new_vertices = []
        for p in positions:
            u,v = uv_from(p)
            new_vertices.extend([p[0], p[1], p[2], u, v])
        model.vertices = new_vertices
        print(f"UVs procedurales generadas ({len(positions)} vértices) para textura '{texture_file}'")

    return model

    # Nota: código posterior a return no se ejecutará; la inserción de materiales debe ir antes.