"""
Animação 3D de um d20 (icosaedro) em Python/Matplotlib.

Fases:
  1. PARADO   - o dado descansa no "chão", leve respiração/wobble.
  2. LANÇADO  - giro caótico no ar (trajetória parabólica + rotação aleatória).
  3. POUSO    - desacelera, "quica" (bounce) e estabiliza mostrando um número.

Saída: GIF animado em /mnt/user-data/outputs/d20_animation.gif
       (também pode salvar em MP4 se houver ffmpeg instalado)
"""

import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt
import matplotlib.animation as animation

rng = np.random.default_rng(42)

# ----------------------------------------------------------------------
# 1) GEOMETRIA DO ICOSAEDRO (d20)
# ----------------------------------------------------------------------
PHI = (1 + np.sqrt(5)) / 2

verts = np.array([
    [-1,  PHI, 0], [ 1,  PHI, 0], [-1, -PHI, 0], [ 1, -PHI, 0],
    [ 0, -1,  PHI], [ 0,  1,  PHI], [ 0, -1, -PHI], [ 0,  1, -PHI],
    [ PHI, 0, -1], [ PHI, 0,  1], [-PHI, 0, -1], [-PHI, 0,  1],
], dtype=float)
verts /= np.linalg.norm(verts[0])          # normaliza para a esfera unitária
R_DIE = 1.0                                # "raio" do dado

faces = np.array([
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
])

face_centers = verts[faces].mean(axis=1)
face_normals = face_centers / np.linalg.norm(face_centers, axis=1, keepdims=True)

# --- Numeração estilo d20 de verdade: faces opostas somam 21 -----------
numbers = np.zeros(20, dtype=int)
used = set()
pairs = []
for i in range(20):
    if i in used:
        continue
    dots = face_normals @ face_normals[i]
    j = int(np.argmin(dots))           # face "antipodal" (normal quase oposta)
    pairs.append((i, j))
    used.add(i)
    used.add(j)
for k, (i, j) in enumerate(pairs):
    numbers[i] = k + 1
    numbers[j] = 21 - (k + 1)

FINAL_NUMBER = 20                       # número em que o dado vai estabilizar
target_face = int(np.where(numbers == FINAL_NUMBER)[0][0])

# Jitter por face para simular textura/faceta irregular (pequena variação de brilho)
face_jitter = rng.uniform(-0.06, 0.06, size=20)

# ----------------------------------------------------------------------
# 2) QUATÉRNIOS (rotação)
# ----------------------------------------------------------------------
def quat_from_axis_angle(axis, angle):
    axis = axis / np.linalg.norm(axis)
    s = np.sin(angle / 2)
    return np.array([np.cos(angle / 2), axis[0]*s, axis[1]*s, axis[2]*s])

def quat_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    ])

def quat_to_matrix(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1-2*(y*y+z*z),   2*(x*y-z*w),     2*(x*z+y*w)],
        [2*(x*y+z*w),     1-2*(x*x+z*z),   2*(y*z-x*w)],
        [2*(x*z-y*w),     2*(y*z+x*w),     1-2*(x*x+y*y)],
    ])

def quat_slerp(q0, q1, t):
    q0 = q0 / np.linalg.norm(q0)
    q1 = q1 / np.linalg.norm(q1)
    dot = np.dot(q0, q1)
    if dot < 0:
        q1, dot = -q1, -dot
    if dot > 0.9995:
        result = q0 + t*(q1 - q0)
        return result / np.linalg.norm(result)
    theta0 = np.arccos(np.clip(dot, -1, 1))
    theta = theta0 * t
    s0 = np.sin(theta0 - theta) / np.sin(theta0)
    s1 = np.sin(theta) / np.sin(theta0)
    return s0*q0 + s1*q1

def quat_align_vectors(v_from, v_to):
    """Quaternio que leva v_from até v_to."""
    v_from = v_from / np.linalg.norm(v_from)
    v_to = v_to / np.linalg.norm(v_to)
    c = np.dot(v_from, v_to)
    if c < -0.9999:
        axis = np.cross(v_from, [1, 0, 0])
        if np.linalg.norm(axis) < 1e-6:
            axis = np.cross(v_from, [0, 1, 0])
        return quat_from_axis_angle(axis, np.pi)
    axis = np.cross(v_from, v_to)
    angle = np.arccos(np.clip(c, -1, 1))
    if np.linalg.norm(axis) < 1e-8:
        return np.array([1.0, 0, 0, 0])
    return quat_from_axis_angle(axis, angle)

# Orientação alvo: normal da face escolhida deve apontar para +Z (face para cima)
q_target = quat_align_vectors(face_normals[target_face], np.array([0, 0, 1]))
# pequena rotação extra em torno de Z para variar a pose final
q_target = quat_mult(quat_from_axis_angle([0, 0, 1], rng.uniform(0, 2*np.pi)), q_target)

# ----------------------------------------------------------------------
# 3) LINHA DO TEMPO DA ANIMAÇÃO
# ----------------------------------------------------------------------
F_IDLE, F_THROW, F_LAND = 25, 55, 55
TOTAL = F_IDLE + F_THROW + F_LAND

# eixos de rotação caótica fixos (sementes) para o giro no ar
chaos_axes = rng.normal(size=(6, 3))
chaos_freqs = rng.uniform(2.0, 5.0, size=6)
chaos_phases = rng.uniform(0, 2*np.pi, size=6)

def chaotic_quat(u):  # u in [0,1] dentro da fase de lançamento
    q = np.array([1.0, 0, 0, 0])
    for axis, freq, phase in zip(chaos_axes, chaos_freqs, chaos_phases):
        ang = np.sin(u*freq*2*np.pi + phase) * 1.3
        q = quat_mult(quat_from_axis_angle(axis, ang), q)
    return q / np.linalg.norm(q)

q_chaos_end = chaotic_quat(1.0)

def ease_out_cubic(t):
    return 1 - (1 - t)**3

def get_orientation(frame):
    if frame < F_IDLE:
        u = frame / F_IDLE
        wob = 0.05 * np.sin(u * 4*np.pi)
        return quat_from_axis_angle([0, 0, 1], wob)
    elif frame < F_IDLE + F_THROW:
        u = (frame - F_IDLE) / F_THROW
        return chaotic_quat(u)
    else:
        u = (frame - F_IDLE - F_THROW) / F_LAND
        return quat_slerp(q_chaos_end, q_target, ease_out_cubic(min(u*1.4, 1.0)))

def get_position(frame):
    """Retorna (x, y, z_offset_do_centro_acima_do_chao)."""
    if frame < F_IDLE:
        breathing = 0.015 * np.sin(frame*0.5)
        return 0.0, 0.0, breathing
    elif frame < F_IDLE + F_THROW:
        u = (frame - F_IDLE) / F_THROW
        height = 2.6 * np.sin(np.pi * u)         # arco parabólico no ar
        x = 0.9 * u
        return x, 0.0, height
    else:
        u = (frame - F_IDLE - F_THROW) / F_LAND
        # quique amortecido decaindo a zero
        bounce = 0.55 * np.exp(-4.5*u) * np.abs(np.cos(5.5*u))
        x = 0.9 + 0.15*(1 - np.exp(-4*u))
        return x, 0.0, bounce

# ----------------------------------------------------------------------
# 4) RENDERIZAÇÃO
# ----------------------------------------------------------------------
fig = plt.figure(figsize=(6.5, 6.5))
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect((1, 1, 1))
LIM = 3.2
ax.set_xlim(-LIM, LIM); ax.set_ylim(-LIM, LIM); ax.set_zlim(-0.2, LIM*1.4)
ax.set_axis_off()
ax.view_init(elev=22, azim=-60)
fig.patch.set_facecolor('#0c0e14')
ax.set_facecolor('#0c0e14')

light_dir = np.array([0.45, -0.35, 0.85])
light_dir /= np.linalg.norm(light_dir)
BASE_COLOR = np.array([0.78, 0.18, 0.16])   # vermelho "vinho" do dado

# chão
xx, yy = np.meshgrid(np.linspace(-LIM, LIM, 2), np.linspace(-LIM, LIM, 2))
zz = np.zeros_like(xx)
ground = ax.plot_surface(xx, yy, zz, color='#1a1d27', alpha=0.9, zorder=0)

poly = Poly3DCollection([], edgecolor='#2a1010', linewidths=0.6)
ax.add_collection3d(poly)
text_artists = []

GROUND_OFFSET = R_DIE * 1.02  # eleva o dado para não cruzar o chão

def render(frame):
    global text_artists
    for t in text_artists:
        t.remove()
    text_artists = []

    q = get_orientation(frame)
    x, y, zlift = get_position(frame)
    M = quat_to_matrix(q)

    v_rot = verts @ M.T
    n_rot = face_normals @ M.T

    pos = np.array([x, y, GROUND_OFFSET + zlift])
    v_world = v_rot + pos

    shade = np.clip(n_rot @ light_dir, 0.12, 1.0)
    colors = []
    for i in range(20):
        c = np.clip(BASE_COLOR * (0.45 + 0.65*shade[i]) + face_jitter[i], 0, 1)
        colors.append((c[0], c[1], c[2], 1.0))

    poly.set_verts([v_world[f] for f in faces])
    poly.set_facecolor(colors)

    cam_dir = np.array([np.cos(np.radians(-60)), np.sin(np.radians(-60)), 0.6])
    cam_dir /= np.linalg.norm(cam_dir)
    centers_world = (face_centers @ M.T) * 1.05 + pos
    for i in range(20):
        if n_rot[i] @ cam_dir > 0.05:
            cx, cy, cz = centers_world[i]
            t = ax.text(cx, cy, cz, str(numbers[i]),
                        color='white', fontsize=10, fontweight='bold',
                        ha='center', va='center', zorder=10)
            text_artists.append(t)

    phase = "PARADO" if frame < F_IDLE else ("LANÇADO" if frame < F_IDLE+F_THROW else "POUSO")
    ax.set_title(f"d20  —  {phase}", color='white', fontsize=13)
    return [poly] + text_artists

anim = animation.FuncAnimation(fig, render, frames=TOTAL, interval=60, blit=False)

out_path = "d20_animation.gif"
anim.save(out_path, writer=animation.PillowWriter(fps=16))
print("Salvo em:", out_path)
print("Número final:", FINAL_NUMBER, "-> face", target_face)
