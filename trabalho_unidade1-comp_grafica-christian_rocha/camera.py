import numpy as np


class Camera:
    """
    Camera virtual com projecao perspectiva.
    Implementada conforme Secao 2.10 do material didatico.
    """

    def __init__(self, eye, at, up, fov, aspect, near, far):
        """
        eye    : posicao da camera no mundo (x, y, z)
        at     : ponto para onde a camera aponta (look-at)
        up     : vetor "para cima" do mundo (normalmente [0,1,0])
        fov    : campo de visao vertical em graus
        aspect : razao largura / altura da janela
        near   : distancia do plano de corte proximo (> 0)
        far    : distancia do plano de corte distante (> near)
        """
        self.eye    = np.array(eye,    dtype=float)
        self.at     = np.array(at,     dtype=float)
        self.up     = np.array(up,     dtype=float)
        self.fov    = float(fov)
        self.aspect = float(aspect)
        self.near   = float(near)
        self.far    = float(far)
        self._compute_vectors()

    # ------------------------------------------------------------------
    # Sistema de coordenadas da camera (Secao 2.10.1)
    # ------------------------------------------------------------------

    def _compute_vectors(self):
        """
        Calcula a base ortonormal (u, v, n) da camera.

        n : aponta de 'at' para 'eye' (direcao oposta ao olhar)
        u : aponta para a direita da camera
        v : aponta para cima da camera (reortogonalizado)
        """
        # n = (eye - at) normalizado  →  eixo Z do espaco da camera
        n = self.eye - self.at
        self.n = n / np.linalg.norm(n)

        # u = up x n normalizado  →  eixo X (direita)
        u = np.cross(self.up, self.n)
        if np.linalg.norm(u) < 1e-10:
            # up e n sao paralelos – escolher outro vetor auxiliar
            aux = np.array([0.0, 0.0, 1.0]) if abs(self.n[1]) > 0.9 else np.array([0.0, 1.0, 0.0])
            u = np.cross(aux, self.n)
        self.u = u / np.linalg.norm(u)

        # v = n x u  →  eixo Y (cima, reortogonalizado)
        self.v = np.cross(self.n, self.u)
        # v ja e unitario pois n e u sao unitarios e ortogonais

    # ------------------------------------------------------------------
    # Matriz de View (Secao 2.10.1.2)
    # ------------------------------------------------------------------

    def get_view_matrix(self):
        """
        Transforma coordenadas do mundo para o espaco da camera.

        V = R * T
        onde T translada a origem para eye e R reorienta os eixos.

        Forma compacta (linha-por-linha da base ortonormal):
            | ux  uy  uz  -dot(u, eye) |
            | vx  vy  vz  -dot(v, eye) |
            | nx  ny  nz  -dot(n, eye) |
            | 0   0   0    1           |
        """
        u, v, n = self.u, self.v, self.n
        e = self.eye

        return np.array([
            [u[0], u[1], u[2], -np.dot(u, e)],
            [v[0], v[1], v[2], -np.dot(v, e)],
            [n[0], n[1], n[2], -np.dot(n, e)],
            [0,    0,    0,     1            ]
        ], dtype=float)

    # ------------------------------------------------------------------
    # Matriz de Projecao Perspectiva (Secao 2.10.2.2)
    # ------------------------------------------------------------------

    def get_projection_matrix(self):
        """
        Matriz de projecao perspectiva que mapeia o frustum para o
        cubo normalizado NDC [-1, 1]^3 (convencao OpenGL/numpy).

        f = 1 / tan(fov/2)

        P = | f/aspect  0   0                        0                      |
            | 0         f   0                        0                      |
            | 0         0  -(far+near)/(far-near)   -2*far*near/(far-near)  |
            | 0         0  -1                        0                      |
        """
        f     = 1.0 / np.tan(np.radians(self.fov) / 2.0)
        zn    = self.near
        zf    = self.far
        denom = zf - zn

        return np.array([
            [f / self.aspect, 0,  0,                      0                   ],
            [0,               f,  0,                      0                   ],
            [0,               0, -(zf + zn) / denom,     -2*zf*zn / denom    ],
            [0,               0, -1,                      0                   ]
        ], dtype=float)

    # ------------------------------------------------------------------
    # Controles interativos (Parte 5)
    # ------------------------------------------------------------------

    def move(self, dx, dy, dz):
        """Translada a camera no espaco do mundo."""
        delta = dx * self.u + dy * self.v + dz * self.n
        self.eye += delta
        self.at  += delta
        self._compute_vectors()

    def orbit(self, dyaw, dpitch):
        """
        Orbita a camera em torno do ponto 'at'.
        dyaw   : rotacao horizontal (graus)
        dpitch : rotacao vertical   (graus)
        """
        from quaternios import Quaternion

        # Vetor da camera ao alvo
        offset = self.eye - self.at

        # Rotacao horizontal em torno do eixo Y do mundo
        q_yaw = Quaternion.from_axis_angle([0, 1, 0], np.radians(dyaw))
        offset = q_yaw.rotate_point(offset)

        # Rotacao vertical em torno do eixo u da camera
        q_pitch = Quaternion.from_axis_angle(self.u, np.radians(dpitch))
        offset  = q_pitch.rotate_point(offset)

        self.eye = self.at + offset
        self._compute_vectors()

    def zoom(self, dfov):
        """Altera o campo de visao (zoom)."""
        self.fov = float(np.clip(self.fov + dfov, 5.0, 170.0))
