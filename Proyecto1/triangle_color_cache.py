import random

class TriangleColorCache:
    """Cache externo de colores por triángulo.
    key = (model_id, tri_index) -> (r,g,b)
    """
    def __init__(self, strategy=None):
        self._colors = {}
        self.strategy = strategy or RandomBrightStrategy()

    def get(self, model, tri_index):
        key = (id(model), tri_index)
        if key not in self._colors:
            self._colors[key] = self.strategy.generate(model, tri_index)
        return self._colors[key]

    def invalidate_model(self, model):
        mid = id(model)
        to_delete = [k for k in self._colors if k[0] == mid]
        for k in to_delete:
            del self._colors[k]

    def clear(self):
        self._colors.clear()

    def set_strategy(self, strategy, regenerate=False):
        self.strategy = strategy
        if regenerate:
            self._colors = {}

class RandomBrightStrategy:
    def __init__(self, min_v=0.15, max_v=1.0):
        self.min_v = min_v
        self.max_v = max_v
    def generate(self, model, tri_index):
        return (
            random.uniform(self.min_v, self.max_v),
            random.uniform(self.min_v, self.max_v),
            random.uniform(self.min_v, self.max_v)
        )

class HashMaterialStrategy:
    """Genera colores deterministas basados en el nombre de material del triángulo."""
    def __init__(self, saturation=0.65, value=0.9):
        self.s = saturation
        self.v = value
    def generate(self, model, tri_index):
        import colorsys
        mat_name = None
        if hasattr(model, 'materialIndices') and tri_index < len(model.materialIndices):
            mat_name = model.materialIndices[tri_index]
        base = mat_name or 'default'
        h = (hash(base) % 1000) / 1000.0
        r,g,b = colorsys.hsv_to_rgb(h, self.s, self.v)
        return (r,g,b)
