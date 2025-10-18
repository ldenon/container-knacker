# Animated real-time packing with simulated annealing
# - Circles and axis-aligned rectangles
# - Real-time animation using matplotlib FuncAnimation
# - Adjustable params at top
#
# To run: execute this cell in a Python environment with matplotlib installed.
# In a standard Jupyter/Thonny/VS Code run the animation window should appear.
# This code is self-contained and uses only the Python standard library + matplotlib + numpy.
import random, math, time
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Circle, Rectangle
import numpy as np

# -------------------- PARAMETERS --------------------
AREA_W, AREA_H = 50.0, 80.0     # main rectangle size
NUM_OBJECTS = 40                 # total objects to pack
CIRCLE_RATIO = 0.5               # fraction of objects that are circles
R_MIN, R_MAX = 2.0, 6.0          # circle radii range
RECT_W_MIN, RECT_W_MAX = 4.0, 10.0
RECT_H_MIN, RECT_H_MAX = 3.0, 8.0
MAX_INITIAL_TRIES = 1000         # attempts to place each object initially
STEPS_PER_FRAME = 200            # how many SA attempts per animation frame
INITIAL_TEMP = 1.0               # starting temperature for SA
COOLING_RATE = 0.9995            # per attempt cooling multiplier (slow cooling)
ITER_LIMIT = 200000              # hard cap on attempts
SHOW_BEST = True                 # draws best-so-far arrangement in green border

random.seed(1)

# -------------------- GEOMETRY HELPERS --------------------
# -----------------------------------------------------------
# Pre-Packing: Sortiere und platziere Objekte reihenweise
# -----------------------------------------------------------
# -----------------------------------------------------------
# Greedy Local Packing: schiebt Objekte dichter aneinander
# -----------------------------------------------------------

def greedy_local_packing(objects, step=0.5, max_iterations=200):
    """
    Versucht, Objekte lokal dichter zusammenzuschieben, 
    ohne Überschneidungen zu erzeugen.
    """
    moved = True
    iteration = 0
    while moved and iteration < max_iterations:
        moved = False
        iteration += 1
        for i, obj in enumerate(objects):
            best_pos = (obj['x'], obj['y'])
            # Probiere Bewegungen nach links/unten
            for dx, dy in [(-step, 0), (0, -step), (-step, -step)]:
                new_x = obj['x'] + dx
                new_y = obj['y'] + dy

                # Begrenzungen prüfen
                if obj['type'] == 'circle':
                    if not (obj['r'] <= new_x <= AREA_W - obj['r'] and obj['r'] <= new_y <= AREA_H - obj['r']):
                        continue
                    candidate = {'type': 'circle', 'x': new_x, 'y': new_y, 'r': obj['r']}
                else:
                    if not (obj['w']/2 <= new_x <= AREA_W - obj['w']/2 and obj['h']/2 <= new_y <= AREA_H - obj['h']/2):
                        continue
                    candidate = {'type': 'rect', 'x': new_x, 'y': new_y, 'w': obj['w'], 'h': obj['h']}

                # Überschneidungsprüfung
                if not any(overlap(candidate, o) for j, o in enumerate(objects) if j != i):
                    obj['x'], obj['y'] = new_x, new_y
                    moved = True
        # Schrittweite reduzieren für feinere Verdichtung
        step *= 0.95
    return objects

def prepack_layout(shapes):
    """Gibt eine erste, geordnete Anordnung ohne Überschneidung zurück"""
    # 1️⃣ Sortieren nach Fläche (größte zuerst)
    shapes_sorted = sorted(shapes, key=lambda s: (area_of({'type': 'circle', 'r': s['r']})
                          if s['type']=='circle' else area_of({'type': 'rect','w':s['w'],'h':s['h']})), reverse=True)

    placed = []
    x_cursor = 0.0
    y_cursor = 0.0
    row_height = 0.0

    # 2️⃣ Durch alle Objekte iterieren
    while shapes_sorted:
        obj = shapes_sorted.pop(0)

        # Objektbreite und -höhe bestimmen
        if obj['type'] == 'circle':
            w = h = obj['r'] * 2
        else:
            w, h = obj['w'], obj['h']

        # Passt das Objekt noch in die aktuelle Reihe?
        if x_cursor + w <= AREA_W:
            x = x_cursor + w/2
            y = y_cursor + h/2
            placed.append({'type': obj['type'], 'x': x, 'y': y, **{k: v for k,v in obj.items() if k not in ['type']}})
            x_cursor += w + 0.5  # kleiner Abstand
            row_height = max(row_height, h)
        else:
            # Neue Reihe
            x_cursor = 0.0
            y_cursor += row_height + 0.5
            row_height = h
            # Prüfen, ob es noch in den Bereich passt
            if y_cursor + h > AREA_H:
                # Kein Platz mehr – abbrechen
                break
            x = x_cursor + w/2
            y = y_cursor + h/2
            placed.append({'type': obj['type'], 'x': x, 'y': y, **{k: v for k,v in obj.items() if k not in ['type']}})
            x_cursor += w + 0.5
    return placed

def rect_bbox(rect):
    # rect: (x_center, y_center, w, h)
    x, y, w, h = rect
    return (x - w/2, y - h/2, x + w/2, y + h/2)

def overlap_circle_circle(c1, c2):
    x1, y1, r1 = c1
    x2, y2, r2 = c2
    return (x1 - x2)**2 + (y1 - y2)**2 < (r1 + r2)**2 - 1e-9

def overlap_rect_rect(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    # separating axis test for axis-aligned rectangles
    return not (x1 + w1/2 <= x2 - w2/2 or x1 - w1/2 >= x2 + w2/2 or
                y1 + h1/2 <= y2 - h2/2 or y1 - h1/2 >= y2 + h2/2)

def overlap_circle_rect(circle, rect):
    cx, cy, r = circle
    rx, ry, w, h = rect
    closest_x = max(rx - w/2, min(cx, rx + w/2))
    closest_y = max(ry - h/2, min(cy, ry + h/2))
    dx, dy = cx - closest_x, cy - closest_y
    return dx*dx + dy*dy < r*r - 1e-9

def overlap(o1, o2):
    if o1['type'] == 'circle' and o2['type'] == 'circle':
        return overlap_circle_circle((o1['x'], o1['y'], o1['r']), (o2['x'], o2['y'], o2['r']))
    if o1['type'] == 'rect' and o2['type'] == 'rect':
        return overlap_rect_rect((o1['x'], o1['y'], o1['w'], o1['h']), (o2['x'], o2['y'], o2['w'], o2['h']))
    if o1['type'] == 'circle' and o2['type'] == 'rect':
        return overlap_circle_rect((o1['x'], o1['y'], o1['r']), (o2['x'], o2['y'], o2['w'], o2['h']))
    if o1['type'] == 'rect' and o2['type'] == 'circle':
        return overlap_circle_rect((o2['x'], o2['y'], o2['r']), (o1['x'], o1['y'], o1['w'], o1['h']))
    return False

def inside_area(o):
    if o['type'] == 'circle':
        return (o['r'] <= o['x'] <= AREA_W - o['r']) and (o['r'] <= o['y'] <= AREA_H - o['r'])
    else:
        return (o['w']/2 <= o['x'] <= AREA_W - o['w']/2) and (o['h']/2 <= o['y'] <= AREA_H - o['h']/2)

def random_shape():
    if random.random() < CIRCLE_RATIO:
        return {'type':'circle', 'r': random.uniform(R_MIN, R_MAX)}
    else:
        return {'type':'rect', 'w': random.uniform(RECT_W_MIN, RECT_W_MAX), 'h': random.uniform(RECT_H_MIN, RECT_H_MAX)}

def area_of(o):
    if o['type']=='circle':
        return math.pi * o['r']**2
    else:
        return o['w'] * o['h']

# -------------------- CREATE INITIAL NON-OVERLAPPING CONFIG --------------------
shapes = [random_shape() for _ in range(NUM_OBJECTS)]
placed = prepack_layout(shapes)
placed = greedy_local_packing(placed)
for s in shapes:
    placed_ok = False
    for _ in range(MAX_INITIAL_TRIES):
        # sample uniformly inside the area (respecting margins)
        if s['type']=='circle':
            x = random.uniform(s['r'], AREA_W - s['r'])
            y = random.uniform(s['r'], AREA_H - s['r'])
            cand = {'type':'circle','x':x,'y':y,'r':s['r']}
        else:
            x = random.uniform(s['w']/2, AREA_W - s['w']/2)
            y = random.uniform(s['h']/2, AREA_H - s['h']/2)
            cand = {'type':'rect','x':x,'y':y,'w':s['w'],'h':s['h']}
        if not any(overlap(cand, p) for p in placed):
            placed.append(cand)
            placed_ok = True
            break
    if not placed_ok:
        # if we cannot place it, reduce the size a bit and retry a few times (simple fallback)
        if s['type']=='circle':
            s['r'] *= 0.8
        else:
            s['w'] *= 0.9; s['h'] *= 0.9
        # try one more time greedily (could still fail)
        for _ in range(200):
            if s['type']=='circle':
                x = random.uniform(s['r'], AREA_W - s['r'])
                y = random.uniform(s['r'], AREA_H - s['r'])
                cand = {'type':'circle','x':x,'y':y,'r':s['r']}
            else:
                x = random.uniform(s['w']/2, AREA_W - s['w']/2)
                y = random.uniform(s['h']/2, AREA_H - s['h']/2)
                cand = {'type':'rect','x':x,'y':y,'w':s['w'],'h':s['h']}
            if not any(overlap(cand, p) for p in placed):
                placed.append(cand); placed_ok=True; break
        if not placed_ok:
            # last resort: skip this shape (rare)
            pass

# compute initial density
total_area = AREA_W * AREA_H
def packing_density(config):
    s = 0.0
    for o in config:
        s += area_of(o)
    return s / total_area

current = placed
best = [dict(o) for o in current]
best_score = packing_density(best)
current_score = best_score
temperature = INITIAL_TEMP
attempts_done = 0

# -------------------- MATPLOTLIB SETUP --------------------
fig, ax = plt.subplots(figsize=(10,8))
ax.set_xlim(0, AREA_W); ax.set_ylim(0, AREA_H); ax.set_aspect('equal')
ax.set_title(f"Real-time packing (density {best_score:.3f})")
# draw container rectangle
container = Rectangle((0,0), AREA_W, AREA_H, linewidth=1.2, edgecolor='black', facecolor='none')
ax.add_patch(container)

patches = []
best_patches = []

def draw_config(conf, patches_list, alpha=0.7, edgecolor='black'):
    # clear existing patches
    for p in patches_list:
        p.remove()
    patches_list.clear()
    for o in conf:
        if o['type']=='circle':
            p = Circle((o['x'], o['y']), o['r'], alpha=alpha, ec=edgecolor)
        else:
            p = Rectangle((o['x'] - o['w']/2, o['y'] - o['h']/2), o['w'], o['h'], alpha=alpha, ec=edgecolor)
        ax.add_patch(p)
        patches_list.append(p)

draw_config(current, patches, alpha=0.7, edgecolor='black')
if SHOW_BEST:
    draw_config(best, best_patches, alpha=0.0, edgecolor='green')  # best is drawn only as edge

# -------------------- SIMULATED ANNEALING STEP --------------------
def try_mutation(conf):
    # returns (new_conf, new_score, accepted_bool)
    global attempts_done, temperature
    attempts_done += 1
    new_conf = [dict(o) for o in conf]
    i = random.randrange(len(new_conf))
    o = new_conf[i]
    # propose small move
    max_move = 4.0 * (0.8 + 0.2*random.random())
    dx = random.uniform(-max_move, max_move)
    dy = random.uniform(-max_move, max_move)
    o['x'] += dx; o['y'] += dy
    # clamp to area
    if o['type']=='circle':
        o['x'] = min(max(o['r'], o['x']), AREA_W - o['r'])
        o['y'] = min(max(o['r'], o['y']), AREA_H - o['r'])
    else:
        o['x'] = min(max(o['w']/2, o['x']), AREA_W - o['w']/2)
        o['y'] = min(max(o['h']/2, o['y']), AREA_H - o['h']/2)
    # quick overlap check (only check against others)
    for j, other in enumerate(new_conf):
        if j==i: continue
        if overlap(o, other):
            return conf, None, False  # invalid move, reject immediately
    # valid non-overlapping; evaluate density (area is fixed, so density is identical) -> we keep score as same
    # however, we can use "compactness" metric to encourage packing: sum of squared distances to container center (minimize spreads)
    # compute compactness for both configs
    def compactness(cfg):
        cx, cy = AREA_W/2, AREA_H/2
        s = 0.0
        for it in cfg:
            dx = it['x'] - cx; dy = it['y'] - cy
            s += dx*dx + dy*dy
        return s
    old_comp = compactness(conf)
    new_comp = compactness(new_conf)
    # lower compactness is better (objects closer to center)
    delta = old_comp - new_comp
    # acceptance rule: accept if new is better, else with prob e^(delta/temp)
    if delta > 0 or random.random() < math.exp(delta / max(1e-8, temperature)):
        # accept
        temperature *= COOLING_RATE  # cool a bit every accepted move too
        return new_conf, -new_comp, True
    else:
        # reject but cool slightly (to make algorithm progress)
        temperature *= (COOLING_RATE**0.1)
        return conf, None, False

# -------------------- ANIMATION FUNCTION --------------------
frame_counter = 0
start_time = time.time()
last_update = start_time

def animate(frame):
    global current, best, best_score, current_score, temperature, frame_counter, attempts_done, last_update
    # perform multiple SA attempts per frame to make progress faster
    accepted_any = False
    for _ in range(STEPS_PER_FRAME):
        if attempts_done >= ITER_LIMIT:
            break
        new_conf, new_metric, accepted = try_mutation(current)
        if accepted:
            current = new_conf
            accepted_any = True
            # compute density (unchanged), use compactness-based metric for best selection
            score = packing_density(current)
            # choose best by densest packing area covered (area doesn't change) or by compactness proxy; here we keep density but prefer compactness
            # We'll compute combined metric: density + small weight * (inverse compactness)
            # To simplify, just update best if objects are closer to center (smaller compactness)
            def compactness_val(cfg):
                cx, cy = AREA_W/2, AREA_H/2
                s = 0.0
                for it in cfg:
                    dx = it['x'] - cx; dy = it['y'] - cy
                    s += dx*dx + dy*dy
                return s
            curr_comp = compactness_val(current)
            best_comp = compactness_val(best)
            if curr_comp < best_comp - 1e-6:
                best = [dict(o) for o in current]
                best_score = packing_density(best)
    # update drawing every frame
    draw_config(current, patches, alpha=0.7, edgecolor='black')
    if SHOW_BEST:
        # remove old best patches and draw updated best as outline
        for p in best_patches:
            p.remove()
        best_patches.clear()
        for o in best:
            if o['type']=='circle':
                p = Circle((o['x'], o['y']), o['r'], fill=False, linewidth=1.0, edgecolor='green', alpha=0.9)
            else:
                p = Rectangle((o['x'] - o['w']/2, o['y'] - o['h']/2), o['w'], o['h'], fill=False, linewidth=1.0, edgecolor='green', alpha=0.9)
            ax.add_patch(p); best_patches.append(p)
    frame_counter += 1
    # update title with status
    elapsed = time.time() - start_time
    ax.set_title(f"Frame {frame_counter}  Attempts {attempts_done}  Temp {temperature:.4f}  Best density {best_score:.4f}  Elapsed {elapsed:.1f}s")
    # return artists to blit (None used here)
    return patches + best_patches

# -------------------- RUN ANIMATION --------------------
anim = animation.FuncAnimation(fig, animate, frames=2000, interval=30, blit=False)
plt.show()

