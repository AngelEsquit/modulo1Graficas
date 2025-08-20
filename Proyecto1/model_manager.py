from objloader import OBJ
from objToModel import objToModel
from shaders import vertexShader

class ModelManager:
    """Administra la colección de modelos y el modelo activo.
    Se encarga de cargarlos, almacenarlos y cambiar la selección activa.
    """
    def __init__(self, renderer):
        self.renderer = renderer
        self.models = []  # espejo de renderer.models
        self.active_index = -1

    def load_model(self, path, texture_path=None, scale=0.05, rotation=(0,0,0), translation=(0,0,0), name=None):
        mesh_data = OBJ(path)
        model = objToModel(mesh_data, texture_path)
        model.vertexShader = vertexShader
        model.fragmentShader = None
        model.scale = [scale, scale, scale]
        model.rotation = list(rotation)
        model.translation = list(translation)
        # Asignar nombre legible: prioridad a parámetro, luego nombre de archivo base
        if not name:
            import os
            name = os.path.splitext(os.path.basename(path))[0]
        model.name = name
        if hasattr(model, 'calculateNormals'):
            try:
                model.calculateNormals()
            except Exception:
                pass
        # Calcular tangentes si el modelo soporta UV (para normal mapping)
        if hasattr(model, 'calculateTangents'):
            try:
                model.calculateTangents()
            except Exception:
                pass
        self.add_model(model)
        return model

    def add_model(self, model):
        self.models.append(model)
        self.renderer.models.append(model)
        if self.active_index == -1:
            self.active_index = 0

    @property
    def active(self):
        if 0 <= self.active_index < len(self.models):
            return self.models[self.active_index]
        return None

    def next(self):
        if self.models:
            self.active_index = (self.active_index + 1) % len(self.models)
            return self.active
        return None

    def prev(self):
        if self.models:
            self.active_index = (self.active_index - 1) % len(self.models)
            return self.active
        return None

    def remove(self, model):
        if model in self.models:
            idx = self.models.index(model)
            self.models.remove(model)
            if model in self.renderer.models:
                self.renderer.models.remove(model)
            # ajustar índice activo
            if not self.models:
                self.active_index = -1
            else:
                if idx <= self.active_index:
                    self.active_index = (self.active_index - 1) % len(self.models)

    def set_active(self, index):
        if 0 <= index < len(self.models):
            self.active_index = index
            return True
        return False
