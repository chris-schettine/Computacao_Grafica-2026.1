# Computação Gráfica 3D — Renderizador Interativo

**Universidade Estadual do Sudoeste da Bahia — UESB**
Curso: Ciência da Computação
Disciplina: Computação Gráfica
Professor: Roque Mendes Prado Trindade

**Aluno:** Christian Schettine Paiva Rocha
**Matrícula:** 202210159

---

Renderizador 3D wireframe escrito inteiramente em Python, sem dependências de OpenGL ou bibliotecas gráficas 3D. Todo o pipeline — transformações, câmera, projeção perspectiva e rasterização — é implementado manualmente usando numpy e exibido via pygame.

---

## Estrutura de arquivos

```
.
├── gera_cena.py       # Aplicação principal — interface interativa e loop de renderização
├── camera.py          # Câmera virtual com projeção perspectiva
├── quaternios.py      # Implementação de quaternions para rotação 3D
├── render3d.py        # Pipeline gráfico completo (MVP, rasterização de arestas)
├── transformacao.py   # Matrizes de transformação 4×4 (translação, escala, rotação)
└── README.md
```

---

## Requisitos

**Python:** 3.9 ou superior (testado em 3.11.9)

**Bibliotecas:**

| Biblioteca   | Uso no projeto                                      |
|--------------|-----------------------------------------------------|
| `numpy`      | Álgebra linear, matrizes, operações vetoriais       |
| `pygame`     | Janela, loop de eventos, desenho da interface       |
| `matplotlib` | Exportação de imagem estática em PNG (opcional)     |

### Instalação

```bash
python -m pip install numpy pygame matplotlib
```

> Use `python -m pip` (e não apenas `pip`) para garantir que a instalação ocorra no mesmo Python que executa o programa.

---

## Como executar

Coloque todos os arquivos `.py` na mesma pasta e execute:

```bash
python gera_cena.py
```

A janela abrirá com resolução **1150 × 800 px**: painel de controles à esquerda (290 px) e cena 3D à direita (860 × 800 px).

---

## Interface

### Painel lateral

O painel é dividido em seções:

**OBJETO** — seleciona a geometria exibida:

| Botão     | Descrição                              |
|-----------|----------------------------------------|
| Cubo      | 8 vértices, 12 arestas                 |
| Piramide  | 5 vértices, 8 arestas (base quadrada)  |
| Octaedro  | 6 vértices, 12 arestas                 |
| Prisma    | 6 vértices, 9 arestas (base triangular)|
| Icosaedro | 12 vértices, 30 arestas                |

**TRANSFORMAÇÕES** — sliders arrastáveis com mouse:

| Slider       | Intervalo     | Efeito                          |
|--------------|---------------|---------------------------------|
| Escala X/Y/Z | 0.1 × a 3.0 × | Estica ou comprime o objeto     |
| Translação X | −3.0 a 3.0    | Move o objeto horizontalmente   |
| Translação Y | −3.0 a 3.0    | Move o objeto verticalmente     |
| Translação Z | −3.0 a 3.0    | Move o objeto em profundidade   |

**COR DO WIREFRAME** — escolhe a cor das arestas: Ciano, Vermelho, Verde, Âmbar, Roxo ou Branco.

**CÂMERA / ANIMAÇÃO:**

| Slider       | Intervalo   | Efeito                                           |
|--------------|-------------|--------------------------------------------------|
| FOV          | 20° a 120°  | Campo de visão — valores baixos = zoom in        |
| Dist. câmera | 3 a 20      | Distância da câmera ao centro da cena            |
| Velocidade   | 0 a 200 °/s | Velocidade da rotação automática                 |

**EIXO DE ROTAÇÃO** — define o eixo em torno do qual o objeto gira:

| Botão  | Eixo                          |
|--------|-------------------------------|
| Y      | Vertical (padrão)             |
| X      | Horizontal                    |
| Z      | Profundidade                  |
| X+Y+Z  | Diagonal (eixo (1,1,1)/√3)   |

**Pausar / Continuar** — congela ou retoma a animação.

### Controles de teclado

| Tecla        | Ação                        |
|--------------|-----------------------------|
| `W` / `S`    | Mover câmera frente / trás  |
| `A` / `D`    | Mover câmera esq. / dir.    |
| `Q` / `E`    | Mover câmera cima / baixo   |
| `↑` / `↓`    | Orbitar câmera (pitch)      |
| `←` / `→`    | Orbitar câmera (yaw)        |
| `+` / `-`    | Zoom (altera FOV)           |
| `ESC`        | Encerrar o programa         |

### HUD (rodapé da cena)

Exibe em tempo real o nome do objeto ativo, a cor selecionada, os componentes do quaternion de rotação acumulado e a posição da câmera com o FOV atual.

---

## Arquitetura do pipeline gráfico

O renderizador implementa um pipeline de software completo, sem aceleração de hardware:

```
Vértices 3D (espaço do objeto)
        │  Matriz de Modelo (escala → rotação → translação)
        ▼
Espaço do mundo
        │  Matriz de View  (lookAt: eye, at, up)
        ▼
Espaço da câmera
        │  Matriz de Projeção (frustum perspectiva)
        ▼
Clip space (coordenadas homogêneas)
        │  Divisão por w  →  NDC [-1, 1]³
        ▼
NDC
        │  Mapeamento de viewport
        ▼
Coordenadas de tela (pixels)
        │  Algoritmo de Bresenham
        ▼
Buffer de imagem  →  pygame Surface  →  janela
```

### Módulos

**`quaternios.py` — classe `Quaternion`**

Representa rotações 3D sem gimbal lock. Operações implementadas:

- Produto de Hamilton (`__mul__`)
- Normalização, conjugado e inverso
- Construção a partir de eixo + ângulo (`from_axis_angle`)
- Rotação de ponto via fórmula sanduíche: `p' = q p q*`
- Conversão para matriz de rotação 4×4 homogênea
- Interpolação esférica SLERP (`slerp`)

**`camera.py` — classe `Camera`**

Implementa a câmera virtual com base ortonormal (u, v, n):

- `n` aponta de `at` para `eye` (oposto ao olhar, eixo Z da câmera)
- `u` aponta para a direita (`up × n`)
- `v` aponta para cima (reortogonalizado: `n × u`)

Métodos de controle: `move`, `orbit` (usa quaternions internamente) e `zoom`.

**`render3d.py` — classes `Objeto3D` e `Renderizador`**

`Objeto3D` armazena vértices, arestas, cor e uma `model_matrix` 4×4 acumulada via `apply_transform`.

`Renderizador` executa o pipeline completo: monta a matriz MVP, transforma os vértices para clip space, descarta arestas fora do frustum, converte para NDC, mapeia ao viewport e rasteriza cada aresta com o algoritmo de Bresenham.

**`transformacao.py`**

Funções que retornam matrizes 4×4 numpy:

| Função              | Descrição                       |
|---------------------|---------------------------------|
| `translacao(tx,ty,tz)` | Matriz de translação         |
| `escala(sx,sy,sz)`     | Matriz de escala             |
| `rotacao_x(theta)`     | Rotação em torno de X (rad)  |
| `rotacao_y(theta)`     | Rotação em torno de Y (rad)  |
| `rotacao_z(theta)`     | Rotação em torno de Z (rad)  |
| `cisalhamento_xy(a,b)` | Cisalhamento em XY           |

---

## Exportar imagem estática (sem pygame)

Se pygame não estiver instalado, o programa gera automaticamente um arquivo `cena_estatica.png` com uma frame única usando matplotlib:

```bash
python gera_cena.py   # detecta ausência do pygame e salva o PNG
```

---

## Limitações conhecidas

- O renderizador é puramente de CPU — cenas com muitos vértices rodam mais devagar.
- O recorte de arestas é simplificado: arestas com ambos os extremos fora do frustum são descartadas inteiramente, sem recorte parcial.
- Não há remoção de superfícies ocultas (back-face culling ou z-buffer) — trata-se de um modelo wireframe transparente.
