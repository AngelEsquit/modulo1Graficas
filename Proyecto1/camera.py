import math
from MathLib import RotationMatrix

class Camera:
    """Cámara simple con posición y rotación (pitch, yaw, roll) en grados.
    Provee utilidades para mover en ejes locales y normalizar ángulos.
    """
    __slots__ = ("position", "rotation")

    def __init__(self, position=(0,0,0), rotation=(0,0,0)):
        self.position = [float(position[0]), float(position[1]), float(position[2])]
        # rotation = (pitch, yaw, roll)
        self.rotation = [float(rotation[0]), float(rotation[1]), float(rotation[2])]

    # --- Rotación ---
    @property
    def pitch(self): return self.rotation[0]
    @property
    def yaw(self): return self.rotation[1]
    @property
    def roll(self): return self.rotation[2]

    def set_rotation(self, pitch=None, yaw=None, roll=None):
        if pitch is not None: self.rotation[0] = pitch
        if yaw is not None: self.rotation[1] = yaw
        if roll is not None: self.rotation[2] = roll

    def normalize_angles(self):
        # Limitar pitch y envolver yaw/roll
        self.rotation[0] = max(-89, min(89, self.rotation[0]))
        for i in (1,2):
            if self.rotation[i] > 180:
                self.rotation[i] -= 360
            elif self.rotation[i] < -180:
                self.rotation[i] += 360

    # --- Vectores locales ---
    def _basis_vectors(self):
        """Devuelve forward, right, up normalizados usando mismo orden que ViewMatrix (pitch * yaw * roll)."""
        R = RotationMatrix(self.pitch, self.yaw, self.roll)
        r = [[R[i,j] for j in range(3)] for i in range(3)]
        base_forward = [0,0,-1]
        base_right = [1,0,0]
        base_up = [0,1,0]
        def transform(v):
            return [
                r[0][0]*v[0] + r[0][1]*v[1] + r[0][2]*v[2],
                r[1][0]*v[0] + r[1][1]*v[1] + r[1][2]*v[2],
                r[2][0]*v[0] + r[2][1]*v[1] + r[2][2]*v[2],
            ]
        def norm(v):
            l = math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]) or 1
            return [v[0]/l, v[1]/l, v[2]/l]
        f = norm(transform(base_forward))
        rt = norm(transform(base_right))
        u = norm(transform(base_up))
        return f, rt, u

    def local_axes(self):
        return self._basis_vectors()

    # --- Movimiento ---
    def move(self, dx=0, dy=0, dz=0):
        self.position[0] += dx
        self.position[1] += dy
        self.position[2] += dz

    def move_local(self, forward=0, right=0, up=0):
        f, r, u = self._basis_vectors()
        self.position[0] += f[0]*forward + r[0]*right + u[0]*up
        self.position[1] += f[1]*forward + r[1]*right + u[1]*up
        self.position[2] += f[2]*forward + r[2]*right + u[2]*up

    # --- Utilidades ---
    def sync_renderer(self, renderer):
        renderer.cameraPos = self.position[:]
        renderer.cameraRotation = self.rotation[:]
