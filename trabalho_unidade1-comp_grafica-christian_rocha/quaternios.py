import numpy as np


class Quaternion:
    """
    Quaternion da forma q = w + xi + yj + zk.
    Usado para representar rotacoes 3D sem gimbal lock.
    """

    def __init__(self, w, x, y, z):
        self.w = float(w)   # parte real
        self.x = float(x)   # componente i
        self.y = float(y)   # componente j
        self.z = float(z)   # componente k

    # ------------------------------------------------------------------
    # Operacoes basicas
    # ------------------------------------------------------------------

    def norm(self):
        """Retorna a norma (magnitude) do quaternion"""
        return np.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)

    def normalize(self):
        """Retorna um novo quaternion unitario (norma = 1)"""
        n = self.norm()
        if n < 1e-10:
            raise ValueError("Nao e possivel normalizar um quaternion com norma zero.")
        return Quaternion(self.w / n, self.x / n, self.y / n, self.z / n)

    def conjugate(self):
        """Retorna o conjugado q* = w - xi - yj - zk"""
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def inverse(self):
        """Retorna o inverso q^-1 = q* / ||q||^2"""
        n2 = self.norm() ** 2
        if n2 < 1e-10:
            raise ValueError("Quaternion com norma zero nao possui inverso.")
        conj = self.conjugate()
        return Quaternion(conj.w / n2, conj.x / n2, conj.y / n2, conj.z / n2)

    def __mul__(self, other):
        """
        Produto de Hamilton (Secao 2.9.2.4):
            q1*q2 = (w1w2 - x1x2 - y1y2 - z1z2)
                  + (w1x2 + x1w2 + y1z2 - z1y2) i
                  + (w1y2 - x1z2 + y1w2 + z1x2) j
                  + (w1z2 + x1y2 - y1x2 + z1w2) k
        """
        w1, x1, y1, z1 = self.w, self.x, self.y, self.z
        w2, x2, y2, z2 = other.w, other.x, other.y, other.z

        w = w1*w2 - x1*x2 - y1*y2 - z1*z2
        x = w1*x2 + x1*w2 + y1*z2 - z1*y2
        y = w1*y2 - x1*z2 + y1*w2 + z1*x2
        z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        return Quaternion(w, x, y, z)

    def __repr__(self):
        return f"Quaternion({self.w:.4f}, {self.x:.4f}i, {self.y:.4f}j, {self.z:.4f}k)"

    # ------------------------------------------------------------------
    # Construcao a partir de eixo/angulo (Secao 2.9.3)
    # ------------------------------------------------------------------

    @staticmethod
    def from_axis_angle(axis, angle):
        """
        Cria quaternion de rotacao a partir de eixo (vetor unitario) e angulo
        (em radianos).

        Formula (Secao 2.9.3):
            q = cos(angle/2) + sin(angle/2) * (ax*i + ay*j + az*k)
        """
        axis = np.array(axis, dtype=float)
        norm = np.linalg.norm(axis)
        if norm < 1e-10:
            raise ValueError("O eixo de rotacao nao pode ser o vetor zero.")
        axis = axis / norm  # garantir que e unitario

        half = angle / 2.0
        w = np.cos(half)
        s = np.sin(half)
        return Quaternion(w, s * axis[0], s * axis[1], s * axis[2])

    # ------------------------------------------------------------------
    # Rotacao de um ponto 3D
    # ------------------------------------------------------------------

    def rotate_point(self, point):
        """
        Aplica rotacao a um ponto 3D usando a formula sandwich:
            p' = q * p * q_conj
        onde p = 0 + px*i + py*j + pz*k (quaternion puro).
        Retorna numpy array [x, y, z].
        """
        p = Quaternion(0.0, point[0], point[1], point[2])
        q_norm = self.normalize()
        rotated = q_norm * p * q_norm.conjugate()
        return np.array([rotated.x, rotated.y, rotated.z])

    # ------------------------------------------------------------------
    # Conversao para matriz de rotacao 4x4
    # ------------------------------------------------------------------

    def to_rotation_matrix(self):
        """
        Converte o quaternion para uma matriz de rotacao 4x4 homogenea.

        Para quaternion unitario q = (w, x, y, z):
            R = [[1-2(y^2+z^2),  2(xy-wz),    2(xz+wy),  0],
                 [2(xy+wz),      1-2(x^2+z^2), 2(yz-wx), 0],
                 [2(xz-wy),      2(yz+wx),    1-2(x^2+y^2), 0],
                 [0,             0,            0,            1]]
        """
        q = self.normalize()
        w, x, y, z = q.w, q.x, q.y, q.z

        return np.array([
            [1 - 2*(y**2 + z**2),   2*(x*y - w*z),       2*(x*z + w*y),   0],
            [2*(x*y + w*z),         1 - 2*(x**2 + z**2), 2*(y*z - w*x),   0],
            [2*(x*z - w*y),         2*(y*z + w*x),       1 - 2*(x**2 + y**2), 0],
            [0,                     0,                    0,               1]
        ], dtype=float)

    # ------------------------------------------------------------------
    # SLERP - Spherical Linear Interpolation (Parte 5)
    # ------------------------------------------------------------------

    @staticmethod
    def slerp(q1, q2, t):
        """
        Interpolacao esferica linear entre dois quaternions.
        t in [0, 1]: t=0 retorna q1, t=1 retorna q2.
        """
        q1 = q1.normalize()
        q2 = q2.normalize()

        # Produto escalar dos quaternions como vetores 4D
        dot = q1.w*q2.w + q1.x*q2.x + q1.y*q2.y + q1.z*q2.z

        # Garantir caminho mais curto
        if dot < 0:
            q2 = Quaternion(-q2.w, -q2.x, -q2.y, -q2.z)
            dot = -dot

        dot = min(dot, 1.0)  # clamp para evitar acos fora do dominio

        if dot > 0.9995:
            # Quaternions muito proximos: usar interpolacao linear
            result = Quaternion(
                q1.w + t*(q2.w - q1.w),
                q1.x + t*(q2.x - q1.x),
                q1.y + t*(q2.y - q1.y),
                q1.z + t*(q2.z - q1.z)
            )
            return result.normalize()

        theta_0 = np.arccos(dot)
        theta   = theta_0 * t
        sin_t   = np.sin(theta)
        sin_0   = np.sin(theta_0)

        s1 = np.cos(theta) - dot * sin_t / sin_0
        s2 = sin_t / sin_0

        return Quaternion(
            s1*q1.w + s2*q2.w,
            s1*q1.x + s2*q2.x,
            s1*q1.y + s2*q2.y,
            s1*q1.z + s2*q2.z
        )
