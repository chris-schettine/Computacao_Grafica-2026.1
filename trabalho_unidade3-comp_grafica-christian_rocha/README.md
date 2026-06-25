# Computação Gráfica — Animação 3D de um Icosaedro (d20)

**Universidade Estadual do Sudoeste da Bahia — UESB**
Curso: Ciência da Computação
Disciplina: Computação Gráfica
Professor: Roque Mendes Prado Trindade

**Aluno:** Christian Schettine Paiva Rocha
**Matrícula:** 202210159

---

Animação 3D de um dado de 20 faces (icosaedro) escrita inteiramente em Python, sem dependências de OpenGL ou motores de jogo. Toda a geometria — vértices, faces, normais, numeração estilo d20, rotação por quatérnios, sombreamento e trajetória — é implementada manualmente com numpy e renderizada quadro a quadro via matplotlib (`mplot3d`), exportando o resultado como GIF animado.

---

## Estrutura de arquivos

```
.
└── d20_animation.py     # Script único — geometria, animação e renderização
```

---

## Requisitos

**Python:** 3.8 ou superior (testado em 3.11)

**Bibliotecas:**

| Biblioteca   | Uso no projeto                                                  |
|--------------|------------------------------------------------------------------|
| `numpy`      | Álgebra linear, quatérnios, geometria do icosaedro                |
| `matplotlib` | Visualização 3D (Axes3D), animação (`FuncAnimation`)               |
| `pillow`     | Exportação da animação como GIF (`PillowWriter`)                   |

### Instalação

```bash
python -m pip install numpy matplotlib pillow
```

> Não é necessário `ffmpeg`. Caso queira exportar em MP4 em vez de GIF, é preciso instalar o `ffmpeg` no sistema e trocar o writer para `animation.FFMpegWriter` no script.

---

## Como executar

Execute:

```bash
python d20_animation.py
```

O script roda a simulação completa, renderiza todos os quadros e salva o resultado como `d20_animation.gif` na mesma pasta do script (ajustável na variável `out_path`). Ao final, imprime no terminal o número em que o dado estabilizou e o índice da face correspondente.

---

## Geometria e numeração

O icosaedro é construído a partir da razão áurea (`PHI`), gerando os 12 vértices e as 20 faces triangulares clássicas do sólido. Para cada face é calculado o centro e a normal (direção para fora do sólido).

A numeração das faces segue a convenção real de um d20: cada face é pareada com sua **face antípoda** (aquela cuja normal é a mais oposta) e os números são distribuídos de forma que **faces opostas somem 21** — exatamente como em um dado físico.

---

## Rotação e quatérnios

Toda a orientação do dado é representada por **quatérnios** (mais estáveis que ângulos de Euler, sem gimbal lock):

- `quat_from_axis_angle` — cria um quatérnio a partir de eixo e ângulo
- `quat_mult` — composição de rotações
- `quat_to_matrix` — converte quatérnio em matriz de rotação 3×3
- `quat_slerp` — interpolação esférica entre duas orientações
- `quat_align_vectors` — calcula o quatérnio que alinha um vetor a outro (usado para apontar a face final para +Z)

---

## Fases da animação

| Fase     | Quadros          | Comportamento                                                                 |
|----------|------------------|--------------------------------------------------------------------------------|
| Parado   | `0` a `F_IDLE`   | Dado em repouso no chão, com leve "respiração" rotacional em torno de Z        |
| Lançado  | `F_IDLE` a `F_IDLE+F_THROW` | Giro caótico (soma de rotações senoidais com eixos/frequências aleatórios) combinado com trajetória parabólica no ar |
| Pouso    | `F_IDLE+F_THROW` a `TOTAL` | `slerp` com easing da orientação caótica final até a orientação alvo, com quique amortecido em Z até estabilizar |

- `chaotic_quat(u)` — gera a rotação caótica do lançamento combinando 6 eixos aleatórios fixos (seed `42`) com frequências e fases distintas
- `ease_out_cubic(t)` — suaviza a desaceleração da rotação no pouso
- `get_position(frame)` — define a trajetória (x, y, altura) em cada quadro: arco parabólico no lançamento, quique exponencialmente amortecido no pouso

A face final (`FINAL_NUMBER`, padrão `20`) é escolhida antes da simulação; `quat_align_vectors` calcula a orientação necessária para que a normal dessa face aponte para `+Z` (voltada para cima) ao final do pouso.

---

## Sombreamento e textura

Não há OpenGL nem texturas de imagem — o efeito de material/faceta é obtido por:

- **Shading direcional**: cada face tem seu brilho calculado pelo produto escalar entre a normal (já rotacionada no quadro atual) e um vetor de luz fixo (`light_dir`), simulando uma fonte de luz direcional
- **Jitter por face**: cada uma das 20 faces recebe uma pequena variação fixa de cor (`face_jitter`, gerada uma única vez com seed `42`), simulando irregularidades de uma faceta real
- A cor final de cada face é `BASE_COLOR * (0.45 + 0.65 * brilho) + jitter`, recalculada a cada quadro conforme a face muda de orientação em relação à luz

---

## Renderização dos números

A cada quadro, o centro de cada face é rotacionado e projetado no espaço 3D. O número da face só é desenhado (`ax.text3D`) quando sua normal está voltada para a câmera (produto escalar com a direção de visão positivo), evitando poluir a cena com números das faces ocultas no lado oposto do dado.

---

## Estrutura do script

```
d20_animation.py
    │
    ├── Geometria do icosaedro            # verts, faces, face_normals
    ├── Numeração estilo d20              # pares antipodais somando 21
    ├── Quatérnios                        # quat_from_axis_angle, quat_mult,
    │                                      # quat_to_matrix, quat_slerp,
    │                                      # quat_align_vectors
    ├── Linha do tempo da animação        # get_orientation(), get_position()
    ├── Renderização                      # render(frame) — shading, posição,
    │                                      # rótulos numéricos
    └── Exportação                        # FuncAnimation + PillowWriter → GIF
```

---

## Parâmetros ajustáveis

| Parâmetro           | Onde                          | Efeito                                          |
|----------------------|-------------------------------|--------------------------------------------------|
| `FINAL_NUMBER`       | topo do script                | Número em que o dado estabiliza ao final          |
| `F_IDLE / F_THROW / F_LAND` | linha do tempo          | Duração (em quadros) de cada fase                  |
| `light_dir`          | seção de renderização         | Direção da luz usada no sombreamento               |
| `BASE_COLOR`         | seção de renderização         | Cor base do dado                                   |
| `fps` (em `PillowWriter`) | exportação                | Quadros por segundo do GIF final                   |
| `rng = np.random.default_rng(42)` | topo do script    | Seed do giro caótico e do jitter das faces         |

---

## Limitações conhecidas

- O renderizador é inteiramente de CPU via matplotlib — não há aceleração por GPU, OpenGL ou motor de jogo.
- A exportação padrão é em GIF (via Pillow); MP4 requer `ffmpeg` instalado separadamente no sistema.
- A numeração das faces segue a regra "opostas somam 21", mas não corresponde necessariamente ao layout exato de um d20 comercial específico (a triangulação de partida é a clássica do icosaedro, não uma matriz de moldes de fábrica).
- Não há interação do usuário durante a execução — a câmera e os parâmetros são fixos por execução; ajustes são feitos editando o script.
- A iluminação é um modelo direcional simplificado (sem sombras projetadas ou iluminação ambiente realista).

---

## Referência

AZEVEDO, Eduardo; CONCI, Aura; VASCONCELOS, Cristina.
*Computação Gráfica: Teoria e Prática — Geração de Imagens.* Vol. 1. Rio de Janeiro: Alta Books, 2021.
