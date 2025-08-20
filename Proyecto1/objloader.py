import os


class OBJ:
    """Simple OBJ + MTL loader (parcial) para posiciones, UVs y materiales básicos.

    Soporta:
      v, vt, f, usemtl, mtllib (carga primera librería; multiples se concatenan)
      En MTL: newmtl, Kd, Ka, Ks, Ns, map_Kd (difusa)
    Guarda:
      self.materials: { nombre: {'Kd':[r,g,b], 'map_Kd': 'ruta_rel'} }
      self.face_materials: nombre de material por triángulo
    """
    def __init__(self, filename):
        self.path = filename
        self.base_dir = os.path.dirname(filename)
        self.vertices = []
        self.tex_coords = []
        self.faces = []
        self.face_materials = []
        self.currentMaterial = None
        self.materials = {}  # nombre -> props
        self._mtl_files = []

        # Primera pasada: leer OBJ y recopilar posibles mtllib
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            for raw in file:
                line = raw.strip()
                if not line or line.startswith('#'): continue
                if line.startswith('mtllib '):
                    parts = line.split()
                    # puede listar varias librerías
                    for m in parts[1:]:
                        self._mtl_files.append(m)
                elif line.startswith('v '):
                    parts = line.split()
                    x,y,z = map(float, parts[1:4])
                    self.vertices.append((x,y,z))
                elif line.startswith('vt '):
                    parts = line.split()
                    u,v = map(float, parts[1:3])
                    self.tex_coords.append((u,v))
                elif line.startswith('usemtl '):
                    parts = line.split()
                    if len(parts) > 1:
                        self.currentMaterial = parts[1]
                elif line.startswith('f '):
                    parts = line.split()
                    face=[]; tex_face=[]
                    for token in parts[1:]:
                        vertex_info = token.split('/')
                        v_idx = int(vertex_info[0]) - 1
                        t_idx = int(vertex_info[1]) - 1 if len(vertex_info) > 1 and vertex_info[1] else None
                        face.append(v_idx)
                        if t_idx is not None: tex_face.append(t_idx)
                    # Triangulizar cualquier polígono con fan (v0, vi, vi+1)
                    # Soporta n-gonos (>=3). Si hay coords UV para todos, se triangulan igual.
                    n = len(face)
                    if n >= 3:
                        full_tex = (len(tex_face) == n)
                        for i in range(1, n - 1):
                            tri = [face[0], face[i], face[i+1]]
                            if full_tex:
                                tri_tex = [tex_face[0], tex_face[i], tex_face[i+1]]
                            else:
                                tri_tex = tex_face[:3] if len(tex_face) >= 3 else None
                            self.faces.append((tri, tri_tex))
                            self.face_materials.append(self.currentMaterial)

        # Cargar MTL(s)
        for mtl_name in self._mtl_files:
            self._parse_mtl_file(mtl_name)

    def _parse_mtl_file(self, mtl_filename):
        full_path = os.path.join(self.base_dir, mtl_filename)
        if not os.path.isfile(full_path):
            return
        current = None
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith('#'): continue
                    if line.startswith('newmtl '):
                        name = line.split(None,1)[1].strip()
                        current = {'name': name}
                        self.materials[name] = current
                    elif current is None:
                        continue
                    elif line.startswith('Kd '):
                        parts = line.split()
                        if len(parts) >= 4:
                            current['Kd'] = list(map(float, parts[1:4]))
                    elif line.startswith('Ka '):
                        parts = line.split()
                        if len(parts) >= 4:
                            current['Ka'] = list(map(float, parts[1:4]))
                    elif line.startswith('Ks '):
                        parts = line.split()
                        if len(parts) >= 4:
                            current['Ks'] = list(map(float, parts[1:4]))
                    elif line.startswith('Ns '):
                        parts = line.split()
                        if len(parts) >= 2:
                            current['Ns'] = float(parts[1])
                    elif line.startswith('map_Kd '):
                        tex = line.split(None,1)[1].strip()
                        current['map_Kd'] = tex
                    elif line.startswith('map_Ka '):
                        tex = line.split(None,1)[1].strip()
                        current['map_Ka'] = tex
                    elif line.startswith('map_Bump') or line.startswith('bump'):
                        tex = line.split(None,1)[1].strip()
                        current['map_Bump'] = tex
        except Exception:
            pass