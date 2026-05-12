# Computação Gráfica — Curvas, Superfícies e Cores

**Universidade Estadual do Sudoeste da Bahia — UESB**
Curso: Ciência da Computação
Disciplina: Computação Gráfica
Professor: Roque Mendes Prado Trindade

**Aluno:** Caíque Santos Santana
**Matrícula:** 202010643

**Aluno:** Christian Schettine Paiva Rocha
**Matrícula:** 202210159

---

Sistema interativo de visualização geométrica 3D escrito inteiramente em Python, sem dependências de OpenGL ou bibliotecas prontas de modelagem. Todo o pipeline — geração de curvas paramétricas, superfícies de revolução, deslocamento, extrusão e curvas de Bézier — é implementado manualmente usando numpy e exibido via matplotlib com interface tkinter.

---

## Estrutura de arquivos

```
.
├── main.py                            # Aplicação principal — interface interativa
└── modulos/
    ├── curvas_superficies.py          # Parte 1 — curvas e superfícies paramétricas + retalho
    ├── bezier.py                      # Parte 2 — curvas de Bézier (polinômios de Bernstein)
    ├── revolucao.py                   # Parte 3 — superfícies e sólidos de revolução
    ├── deslocamento_extrusao.py       # Parte 4 — superfícies por deslocamento e extrusão
    └── cores.py                       # Parte 5 — palheta de cores RGB normalizado
```

---

## Requisitos

**Python:** 3.8 ou superior (testado em 3.11)

**Bibliotecas:**

| Biblioteca   | Uso no projeto                                            |
|--------------|-----------------------------------------------------------|
| `numpy`      | Álgebra linear, malhas de parâmetros, operações vetoriais |
| `matplotlib` | Visualização 3D interativa (Axes3D)                       |
| `tkinter`    | Interface gráfica — painel de controles e janela          |

### Instalação

```bash
python -m pip install numpy matplotlib
```

> O `tkinter` já está incluído por padrão no Python para Windows e na maioria das distribuições Linux. No Ubuntu/Debian, caso necessário: `sudo apt install python3-tk`.

---

## Como executar

Execute:

```bash
python main.py
```

A janela abrirá com resolução **1240 × 760 px**: painel de controles à esquerda (310 px) e visualização 3D à direita.

---

## Interface

### Painel lateral

O painel é dividido em seções com scroll:

**OBJETO** — seleciona o modo de visualização:

| Botão          | Descrição                                            |
|----------------|------------------------------------------------------|
| Curva Param.   | Curva paramétrica 3D (hélice, senoidal ou Lissajous) |
| Superfície     | Superfície paramétrica (toroide, ondulada ou esfera) |
| Retalho        | Retalho de superfície em intervalo restrito de u, v  |
| Bézier         | Curva de Bézier grau 5 com polígono de controle      |
| Revolução      | Sólido de revolução (taça, vaso ou garrafa)          |
| Deslocamento   | Superfície gerada por deslocamento de curva          |
| Extrusão       | Sólido por extrusão de perfil 2D                     |
| Cena Completa  | Todos os elementos reunidos em uma única cena        |

**VARIANTE** — sub-tipo do objeto selecionado:

| Modo           | Opções disponíveis               |
|----------------|----------------------------------|
| Curva Param.   | Hélice · Senoidal · Lissajous    |
| Superfície     | Toroide · Ondulada · Esfera      |
| Revolução      | Taça · Vaso · Garrafa            |
| Extrusão       | Estrela 5 · Estrela 7 · Círculo  |
| Deslocamento   | Senoidal · Circular · Quadrado   |

**COR DA GEOMETRIA** — 12 botões de cor com palheta RGB normalizado:

Cinza, Vermelho, Verde, Azul, Amarelo, Laranja, Ciano, Magenta, Branco, Rosa, Violeta, Dourado.

**TRANSFORMAÇÕES** — sliders arrastáveis:

| Slider         | Intervalo       | Efeito                          |
|----------------|-----------------|---------------------------------|
| Escala X/Y/Z   | 0.1 × a 3.0 ×   | Estica ou comprime o objeto     |
| Translação X   | −4.0 a 4.0      | Move o objeto horizontalmente   |
| Translação Y   | −4.0 a 4.0      | Move o objeto verticalmente     |
| Translação Z   | −4.0 a 4.0      | Move o objeto em profundidade   |

**VISUALIZAÇÃO:**

| Slider/Opção     | Intervalo  | Efeito                                      |
|------------------|------------|---------------------------------------------|
| Alpha            | 0.1 a 1.0  | Transparência das superfícies               |
| Resolução        | 10 a 120   | Densidade da malha / amostragem da curva    |
| Wireframe apenas | checkbox   | Alterna entre superfície sólida e aramada   |
| Mostrar eixos    | checkbox   | Exibe setas dos eixos X, Y, Z na cena       |

**▶ RENDERIZAR** — redesenha o objeto com os parâmetros atuais.  
**↺ Resetar** — devolve todos os controles ao valor padrão.

### Barra de status

Exibe em tempo real o nome do objeto ativo, a cor selecionada com seu valor hexadecimal e os fatores de escala e translação aplicados.

---

## Partes implementadas

### Parte 1 — Plotagem de Curvas e Superfícies Paramétricas (0,6 pt)

**`curvas_superficies.py`**

- `curva_parametrica(t, tipo)` — retorna array (N, 3) para os tipos `helice`, `senoidal` e `lissajous`
- `superficie_parametrica(u, v, tipo)` — retorna matrizes X, Y, Z para `toroide`, `ondulada` e `esfera`
- `retalho_superficie(u_min, u_max, v_min, v_max, nu, nv)` — retalho bicúbico `sin·cos·exp` em intervalo restrito

### Parte 2 — Curvas de Bézier (0,8 pt)

**`bezier.py`**

Implementação manual da fórmula de Bernstein, sem bibliotecas externas de Bézier:

```
B(t) = Σ C(n,i) · (1−t)^(n−i) · t^i · Pᵢ
```

- `bernstein(n, i, t)` — calcula o polinômio de Bernstein B_{i,n}(t)
- `curva_bezier(pontos_controle, num_pontos)` — retorna array (num_pontos, dim)

A interface exibe a curva de grau 5 (6 pontos de controle) com o polígono de controle tracejado e os pontos P0–P5 rotulados.

**Como os pontos de controle influenciam a forma:**
- A curva sempre passa pelo **primeiro (P0) e pelo último ponto (P5)**
- Os pontos intermediários **atraem** a curva sem que ela passe por eles
- Mover P1 ou P4 controla a **tangente inicial e final** da curva
- Pontos centrais mais próximos fazem a curva se **dobrar mais** nessa região
- Aumentar o grau (mais pontos) adiciona mais graus de liberdade à forma

### Parte 3 — Superfícies e Sólidos de Revolução (0,7 pt)

**`revolucao.py`**

- `superficie_revolucao(raios, alturas, num_fatias)` — rotaciona a curva geratriz 360° em torno do eixo Z gerando as matrizes X, Y, Z
- `perfil_taca()`, `perfil_vaso()`, `perfil_garrafa()` — perfis geratores definidos por equações analíticas

### Parte 4 — Superfícies por Deslocamento e Extrusão (0,8 pt)

**`deslocamento_extrusao.py`**

- `superficie_deslocamento(curva, vetor, passos)` — move a curva ao longo do vetor em `passos` etapas, gerando a superfície varrida
- `extrusao(perfil_2d, altura)` — prolonga o perfil 2D no eixo Z, retornando `(base, topo)`
- `extrusao_lados(base, topo)` — gera as faces laterais do sólido extrudado
- `perfil_estrela(n_pontas, r_ext, r_int)` — perfil 2D de estrela com n pontas

### Parte 5 — Palheta de Cores (0,6 pt)

**`cores.py`**

**Sobre a representação RGB normalizado:**  
O modelo RGB representa cores como combinação aditiva de três canais — R (Vermelho), G (Verde) e B (Azul) — cada um no intervalo [0.0, 1.0]. A ausência total dos três canais produz preto `(0,0,0)` e a presença máxima produz branco `(1,1,1)`.

| Cor       | R    | G    | B    |
|-----------|------|------|------|
| Vermelho  | 1.00 | 0.00 | 0.00 |
| Verde     | 0.00 | 1.00 | 0.00 |
| Azul      | 0.00 | 0.00 | 1.00 |
| Amarelo   | 1.00 | 1.00 | 0.00 |
| Ciano     | 0.00 | 1.00 | 1.00 |
| Magenta   | 1.00 | 0.00 | 1.00 |

Funções disponíveis: `criar_palheta()`, `rgb_para_hex(r, g, b)`, `esquema_padrao()`.

A cor selecionada é aplicada interativamente a qualquer geometria via os botões **COR DA GEOMETRIA** no painel lateral.

### Parte 6 — Aplicação Principal e Cena Completa (0,5 pt)

O modo **"Cena Completa"** reúne todos os elementos em uma única visualização 3D:

- Hélice paramétrica (Parte 1)
- Curva de Bézier com polígono de controle (Parte 2)
- Retalho de superfície (Parte 1)
- Taça por revolução (Parte 3)
- Superfície por deslocamento (Parte 4)
- Estrela extrudada (Parte 4)

---

## Arquitetura dos módulos

```
main.py  (interface tkinter + matplotlib)
    │
    ├── modulos/curvas_superficies.py   ← Parte 1
    │       curva_parametrica()
    │       superficie_parametrica()
    │       retalho_superficie()
    │
    ├── modulos/bezier.py               ← Parte 2
    │       bernstein()
    │       curva_bezier()
    │
    ├── modulos/revolucao.py            ← Parte 3
    │       superficie_revolucao()
    │       perfil_taca / perfil_vaso / perfil_garrafa
    │
    ├── modulos/deslocamento_extrusao.py  ← Parte 4
    │       superficie_deslocamento()
    │       extrusao()
    │       extrusao_lados()
    │       perfil_estrela()
    │
    └── modulos/cores.py                ← Parte 5
            criar_palheta()
            rgb_para_hex()
            esquema_padrao()
```

---

## Limitações conhecidas

- O renderizador é inteiramente de CPU — cenas com alta resolução (> 100) podem apresentar lentidão.
- A navegação 3D (rotação, zoom, pan) é fornecida pela barra de ferramentas do matplotlib; não há animação automática contínua.
- A extrusão gera apenas faces laterais e tampa superior/inferior trianguladas — sem sólido fechado perfeito para perfis côncavos.
- Não há iluminação ou sombreamento — as superfícies são exibidas com cor plana.

---

## Referência

AZEVEDO, Eduardo; CONCI, Aura; VASCONCELOS, Cristina.
*Computação Gráfica: Teoria e Prática — Geração de Imagens.* Vol. 1. Rio de Janeiro: Alta Books, 2021.
