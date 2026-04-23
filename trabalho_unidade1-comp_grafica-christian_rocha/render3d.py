import numpy as np


class Objeto3D:
    """
    Representacao de um objeto 3D por meio de vertices e arestas
    (modelo de arame / wireframe).
    """

    def __init__(self, vertices, arestas, cor=(0, 0, 1)):
        """
        vertices : lista de pontos 3D [(x,y,z), ...]
        arestas  : lista de pares de indices [(i,j), ...]
        cor      : tupla RGB em [0, 1]
        """
        self.vertices     = np.array(vertices, dtype=float)
        self.arestas      = arestas
        self.cor          = cor
        self.model_matrix = np.eye(4)   # transformacao acumulada do modelo

    def apply_transform(self, matrix):
        """
        Pre-multiplica a matriz do modelo pela transformacao fornecida.
        Permite encadear translacoes, rotacoes e escalas.
        """
        self.model_matrix = matrix @ self.model_matrix

    def get_transformed_vertices(self):
        """
        Retorna os vertices ja transformados pela model_matrix.
        Converte para coordenadas homogeneas, aplica a transformacao
        e retorna apenas x, y, z (descarta w).
        """
        n = len(self.vertices)
        # Adicionar coluna de 1s para coordenadas homogeneas (n x 4)
        ones = np.ones((n, 1))
        v_hom = np.hstack([self.vertices, ones])   # shape (n, 4)

        # Multiplicar: cada vertice e uma coluna
        # model_matrix (4x4) @ v_hom.T (4xn) -> resultado (4xn)
        v_transformed = (self.model_matrix @ v_hom.T).T  # shape (n, 4)

        # Retornar apenas x, y, z
        return v_transformed[:, :3]


# ---------------------------------------------------------------------------

class Renderizador:
    """
    Pipeline grafico completo (CPU / software renderer) usando numpy.
    Produz imagem RGB via rasterizacao de arestas com algoritmo de Bresenham.
    """

    def __init__(self, width, height):
        self.width  = width
        self.height = height
        self.image  = np.zeros((height, width, 3), dtype=float)

    # ------------------------------------------------------------------
    # Pipeline principal
    # ------------------------------------------------------------------

    def render(self, objetos, camera):
        """
        Pipeline completo de renderizacao:
          1. Obter matrizes View e Projection da camera
          2. Calcular MVP (Model-View-Projection) por objeto
          3. Transformar vertices para clip space
          4. Divisao perspectiva (w) → NDC
          5. Recorte no cubo normalizado [-1, 1]^3
          6. Mapeamento viewport → coordenadas de tela
          7. Rasterizacao das arestas (Bresenham)
        """
        self.image[:] = 0  # limpar buffer

        V = camera.get_view_matrix()
        P = camera.get_projection_matrix()

        for obj in objetos:
            # ---- MVP ----
            mvp = P @ V @ obj.model_matrix

            # ---- Transformar todos os vertices ----
            vertices_clip = self._transform_vertices(obj.vertices, mvp)  # (n, 4)

            # ---- Para cada aresta ----
            for (i, j) in obj.arestas:
                v0 = vertices_clip[i]   # [x, y, z, w]
                v1 = vertices_clip[j]

                # Recorte simples: descartar aresta se ambos os pontos
                # estiverem fora do mesmo plano do frustum
                if not self._visible(v0) and not self._visible(v1):
                    continue

                # Divisao perspectiva: NDC [-1, 1]^3
                ndc0 = self._to_ndc(v0)
                ndc1 = self._to_ndc(v1)

                if ndc0 is None or ndc1 is None:
                    continue

                # Mapeamento viewport
                p0 = self._viewport(ndc0)
                p1 = self._viewport(ndc1)

                # Rasterizacao
                self._draw_line(p0, p1, obj.cor)

    # ------------------------------------------------------------------
    # Etapas auxiliares
    # ------------------------------------------------------------------

    def _transform_vertices(self, vertices, matrix):
        """
        Aplica a matriz 4x4 a todos os vertices.
        Entrada : vertices (n x 3), matrix (4 x 4)
        Saida   : vertices em clip space (n x 4)
        """
        n     = len(vertices)
        ones  = np.ones((n, 1))
        v_hom = np.hstack([vertices, ones])          # (n, 4)
        v_clip = (matrix @ v_hom.T).T                # (n, 4)
        return v_clip

    def _visible(self, v):
        """
        Verifica se um vertice em clip space esta (pelo menos parcialmente)
        dentro do frustum.  Condicao: -w <= x,y,z <= w e w > 0.
        """
        w = v[3]
        if w <= 0:
            return False
        return (abs(v[0]) <= w) and (abs(v[1]) <= w) and (abs(v[2]) <= w)

    def _to_ndc(self, v):
        """
        Divisao perspectiva: converte clip space para NDC.
        Retorna None se w <= 0 (ponto atras da camera).
        """
        w = v[3]
        if abs(w) < 1e-7:
            return None
        return v[:3] / w    # [x/w, y/w, z/w]

    def _viewport(self, ndc):
        """
        Mapeia coordenadas NDC [-1,1]^2 para pixels da tela.
        x_screen = (x_ndc + 1) / 2 * (width  - 1)
        y_screen = (1 - y_ndc) / 2 * (height - 1)   (Y invertido)
        """
        xs = int((ndc[0] + 1.0) / 2.0 * (self.width  - 1))
        ys = int((1.0 - ndc[1]) / 2.0 * (self.height - 1))
        return (xs, ys)

    # ------------------------------------------------------------------
    # Rasterizacao de linha (Bresenham)
    # ------------------------------------------------------------------

    def _draw_line(self, p1, p2, cor):
        """
        Desenha um segmento de reta entre p1 e p2 (coordenadas inteiras de
        tela) usando o algoritmo de Bresenham.
        cor : tupla RGB em [0, 1]
        """
        x0, y0 = p1
        x1, y1 = p2

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            # Escrever pixel se dentro da imagem
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                self.image[y0, x0] = cor

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0  += sx
            if e2 < dx:
                err += dx
                y0  += sy

    # ------------------------------------------------------------------
    # Exportacao
    # ------------------------------------------------------------------

    def get_image_uint8(self):
        """Retorna o buffer de imagem como array uint8 (0-255)."""
        return (np.clip(self.image, 0, 1) * 255).astype(np.uint8)

    def save_png(self, filename):
        """Salva a imagem renderizada como PNG (requer matplotlib)."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.imsave(filename, self.get_image_uint8())
        print(f"Imagem salva em: {filename}")

    def show(self):
        """Exibe a imagem usando matplotlib."""
        import matplotlib.pyplot as plt
        plt.figure(figsize=(self.width / 100, self.height / 100))
        plt.imshow(self.get_image_uint8())
        plt.axis("off")
        plt.tight_layout()
        plt.show()
