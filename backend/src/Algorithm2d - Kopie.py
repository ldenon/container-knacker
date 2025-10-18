import random
import math
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import numpy as np
import json
import os
import multiprocessing
from numba import jit

# --- WICHTIG: Importieren Sie Ihren Parser ---
from order_parser import OrderParser

# -------------------- DATENSTRUKTUR-INDIZES (ERWEITERT) --------------------
IDX_X = 0        # Aktuelle X-Position (Zentrum)
IDX_Y = 1        # Aktuelle Y-Position (Zentrum)
IDX_W = 2        # Bounding Box Breite
IDX_H = 3        # Bounding Box Höhe
IDX_W_ORIG = 4   # Original BB Breite
IDX_H_ORIG = 5   # Original BB Höhe
IDX_TYPE_ID = 6  # Interner sequenzieller Typ (0, 1, 2...)
IDX_AREA = 7     # Fläche
IDX_GEOM_TYPE = 8  # 0 = Rechteck, 1 = Kreis
IDX_RADIUS = 9     # Radius (nur für Kreise, sonst 0)
IDX_WEIGHT = 10    # Gewicht des Objekts

GEOM_RECT = 0
GEOM_CIRCLE = 1


# -------------------- JIT-KOMPILIERTE KERNFUNKTIONEN --------------------

@jit(nopython=True)
def overlap_rect_rect_jit(r1_x, r1_y, r1_w_bb, r1_h_bb, r2_x, r2_y, r2_w_bb, r2_h_bb):
    """Prüft Überlappung von zwei Rechtecken (Zentrum-Koordinaten)."""
    return not (r1_x + r1_w_bb/2 <= r2_x - r2_w_bb/2 or
                r1_x - r1_w_bb/2 >= r2_x + r2_w_bb/2 or
                r1_y + r1_h_bb/2 <= r2_y - r2_h_bb/2 or
                r1_y - r1_h_bb/2 >= r2_y + r2_h_bb/2)

@jit(nopython=True)
def overlap_circle_circle_jit(c1_x, c1_y, c1_r, c2_x, c2_y, c2_r):
    """Prüft Überlappung von zwei Kreisen."""
    dist_sq = (c1_x - c2_x)**2 + (c1_y - c2_y)**2
    radius_sum_sq = (c1_r + c2_r)**2
    return dist_sq < radius_sum_sq

@jit(nopython=True)
def overlap_rect_circle_jit(r_x, r_y, r_w_bb, r_h_bb, c_x, c_y, c_r):
    """Prüft Überlappung von Rechteck und Kreis."""
    half_w = r_w_bb / 2
    half_h = r_h_bb / 2
    closest_x = max(r_x - half_w, min(c_x, r_x + half_w))
    closest_y = max(r_y - half_h, min(c_y, r_y + half_h))
    dist_x = c_x - closest_x
    dist_y = c_y - closest_y
    dist_sq = (dist_x**2) + (dist_y**2)
    radius_sq = c_r**2
    return dist_sq < radius_sq


@jit(nopython=True)
def check_overlap_jit(item, config, item_index):
    """
    Prüft, ob 'item' irgendein anderes Item in 'config' überlappt.
    Wählt die korrekte Geometrie-Prüffunktion aus.
    """
    item_type = int(item[IDX_GEOM_TYPE])
    for j in range(config.shape[0]):
        if j == item_index: continue
        other = config[j]
        other_type = int(other[IDX_GEOM_TYPE])

        if item_type == GEOM_RECT and other_type == GEOM_RECT:
            if overlap_rect_rect_jit(
                item[IDX_X], item[IDX_Y], item[IDX_W], item[IDX_H],
                other[IDX_X], other[IDX_Y], other[IDX_W], other[IDX_H]
            ): return True
        elif item_type == GEOM_CIRCLE and other_type == GEOM_CIRCLE:
            if overlap_circle_circle_jit(
                item[IDX_X], item[IDX_Y], item[IDX_RADIUS],
                other[IDX_X], other[IDX_Y], other[IDX_RADIUS]
            ): return True
        elif item_type == GEOM_RECT and other_type == GEOM_CIRCLE:
            if overlap_rect_circle_jit(
                item[IDX_X], item[IDX_Y], item[IDX_W], item[IDX_H],
                other[IDX_X], other[IDX_Y], other[IDX_RADIUS]
            ): return True
        elif item_type == GEOM_CIRCLE and other_type == GEOM_RECT:
            if overlap_rect_circle_jit(
                other[IDX_X], other[IDX_Y], other[IDX_W], other[IDX_H],
                item[IDX_X], item[IDX_Y], item[IDX_RADIUS]
            ): return True
    return False

@jit(nopython=True)
def bottom_left_density_cost_jit(config, num_types, AREA_W, AREA_H, WEIGHT_Y, WEIGHT_X, WEIGHT_BOX_AREA, WEIGHT_GROUPING):
    """Numba-kompatible Kostenfunktion mit balancierten Gewichten und Dichtestrafe."""
    if config.shape[0] == 0: return 0.0
    min_x = 999999.0; max_x = -999999.0
    min_y = 999999.0; max_y = -999999.0
    cost_pos = 0.0

    for i in range(config.shape[0]):
        it = config[i]
        x, y, w_bb, h_bb, area = it[IDX_X], it[IDX_Y], it[IDX_W], it[IDX_H], it[IDX_AREA]
        half_w = w_bb / 2; half_h = h_bb / 2
        min_x = min(min_x, x - half_w); max_x = max(max_x, x + half_w)
        min_y = min(min_y, y - half_h); max_y = max(max_y, y + half_h)

        # X- und Y-Kosten balanciert (beide mit 'area' skaliert)
        cost_pos += (WEIGHT_Y * area * y) + (WEIGHT_X * area * x)

    # Starke Bestrafung der Bounding Box Fläche für Dichte
    cost_box = WEIGHT_BOX_AREA * ((max_x - min_x) * (max_y - min_y))
    cost_group = 0.0

    # Gruppierungskosten
    if WEIGHT_GROUPING > 0 and num_types > 0:
        centroids = np.zeros((num_types, 3))
        for i in range(config.shape[0]):
            it = config[i]
            type_id = int(it[IDX_TYPE_ID])
            centroids[type_id, 0] += it[IDX_X]
            centroids[type_id, 1] += it[IDX_Y]
            centroids[type_id, 2] += 1
        for i in range(config.shape[0]):
            it = config[i]
            type_id = int(it[IDX_TYPE_ID])
            count = centroids[type_id, 2]
            if count > 1:
                center_x = centroids[type_id, 0] / count
                center_y = centroids[type_id, 1] / count
                dist_x = it[IDX_X] - center_x
                dist_y = it[IDX_Y] - center_y
                cost_group += (dist_x * dist_x + dist_y * dist_y)

    if config.shape[0] > 0:
        cost_group /= config.shape[0] # Normalisieren

    return cost_pos + cost_box + (WEIGHT_GROUPING * cost_group)

@jit(nopython=True)
def greedy_local_packing_jit(config, AREA_W, AREA_H, step=0.5, max_iterations=200):
    """Numba-kompatible 'Jiggle'-Funktion für eine gute Startlösung."""
    moved = True; iteration = 0; temp_step = step
    moves = np.array([[0.0, -temp_step], [-temp_step, 0.0], [-temp_step, -temp_step]])
    while moved and iteration < max_iterations:
        moved = False; iteration += 1
        for i in range(config.shape[0]):
            obj = config[i]
            for move_idx in range(moves.shape[0]):
                dx, dy = moves[move_idx, 0], moves[move_idx, 1]
                new_x = obj[IDX_X] + dx; new_y = obj[IDX_Y] + dy
                w_bb, h_bb = obj[IDX_W], obj[IDX_H]
                margin_x, margin_y = w_bb / 2, h_bb / 2
                if not (margin_x <= new_x <= AREA_W - margin_x and margin_y <= new_y <= AREA_H - margin_y):
                    continue
                candidate = obj.copy()
                candidate[IDX_X], candidate[IDX_Y] = new_x, new_y
                if not check_overlap_jit(candidate, config, i):
                    obj[IDX_X], obj[IDX_Y] = new_x, new_y
                    moved = True
        temp_step *= 0.98
        moves[0, 1] = -temp_step; moves[1, 0] = -temp_step
        moves[2, 0] = -temp_step; moves[2, 1] = -temp_step
    return config

@jit(nopython=True)
def try_mutation_sa_jit(
    config, old_cost, temp, num_types, AREA_W, AREA_H, COOLING_RATE,
    SWAP_PROB, TELEPORT_PROB, ROTATE_PROB, MAX_MOVE_MULTIPLIER,
    WEIGHT_Y, WEIGHT_X, WEIGHT_BOX, WEIGHT_GROUP
):
    """Die Numba-kompilierte SA-Hauptschleife, inkl. Rotation."""
    new_conf = config.copy()
    num_items = new_conf.shape[0]
    if num_items < 2:
        new_temp = temp * (COOLING_RATE**0.01)
        return config, old_cost, new_temp, False, old_cost

    mutated = False
    r = random.random()

    if r < SWAP_PROB:
        # --- SWAP MUTATION ---
        i1 = random.randint(0, num_items - 1)
        i2 = random.randint(0, num_items - 1)
        while i1 == i2: i2 = random.randint(0, num_items - 1)
        o1 = new_conf[i1]; o2 = new_conf[i2]
        x1, y1 = o1[IDX_X], o1[IDX_Y]
        o1[IDX_X], o1[IDX_Y] = o2[IDX_X], o2[IDX_Y]
        o2[IDX_X], o2[IDX_Y] = x1, y1
        o1[IDX_X] = min(max(o1[IDX_W]/2, o1[IDX_X]), AREA_W - o1[IDX_W]/2)
        o1[IDX_Y] = min(max(o1[IDX_H]/2, o1[IDX_Y]), AREA_H - o1[IDX_H]/2)
        o2[IDX_X] = min(max(o2[IDX_W]/2, o2[IDX_X]), AREA_W - o2[IDX_W]/2)
        o2[IDX_Y] = min(max(o2[IDX_H]/2, o2[IDX_Y]), AREA_H - o2[IDX_H]/2)
        if check_overlap_jit(o1, new_conf, i1) or check_overlap_jit(o2, new_conf, i2):
            mutated = True
    elif r < SWAP_PROB + TELEPORT_PROB:
        # --- TELEPORT MUTATION ---
        i = random.randint(0, num_items - 1)
        o = new_conf[i]; old_x, old_y = o[IDX_X], o[IDX_Y]
        o[IDX_X] = random.uniform(o[IDX_W]/2, AREA_W - o[IDX_W]/2)
        o[IDX_Y] = random.uniform(o[IDX_H]/2, AREA_H - o[IDX_H]/2)
        if check_overlap_jit(o, new_conf, i):
            mutated = True; o[IDX_X], o[IDX_Y] = old_x, old_y
    elif r < SWAP_PROB + TELEPORT_PROB + ROTATE_PROB:
        # --- ROTATION MUTATION (NUR FÜR RECHTECKE) ---
        i = random.randint(0, num_items - 1)
        o = new_conf[i]
        if o[IDX_GEOM_TYPE] == GEOM_RECT:
            old_w, old_h = o[IDX_W], o[IDX_H]
            new_w, new_h = o[IDX_H_ORIG], o[IDX_W_ORIG]
            if old_w != new_w: # Überspringe Quadrat
                o[IDX_W], o[IDX_H] = new_w, new_h
                o[IDX_W_ORIG], o[IDX_H_ORIG] = old_w, old_h
                o[IDX_X] = min(max(o[IDX_W]/2, o[IDX_X]), AREA_W - o[IDX_W]/2)
                o[IDX_Y] = min(max(o[IDX_H]/2, o[IDX_Y]), AREA_H - o[IDX_H]/2)
                if check_overlap_jit(o, new_conf, i):
                    mutated = True # Ungültig, mache rückgängig
                    o[IDX_W], o[IDX_H] = old_w, old_h
                    o[IDX_W_ORIG], o[IDX_H_ORIG] = new_w, new_h
    else:
        # --- TRANSLATION MUTATION ---
        i = random.randint(0, num_items - 1)
        o = new_conf[i]
        max_move = max(0.1, MAX_MOVE_MULTIPLIER * temp * (0.8 + 0.2*random.random()))
        dx = random.uniform(-max_move, max_move); dy = random.uniform(-max_move, max_move)
        o[IDX_X] += dx; o[IDX_Y] += dy
        o[IDX_X] = min(max(o[IDX_W]/2, o[IDX_X]), AREA_W - o[IDX_W]/2)
        o[IDX_Y] = min(max(o[IDX_H]/2, o[IDX_Y]), AREA_H - o[IDX_H]/2)
        if check_overlap_jit(o, new_conf, i):
            mutated = True

    # --- KOSTENBERECHNUNG ---
    if mutated: # Ungültiger Zug
        new_temp = temp * (COOLING_RATE**0.01)
        return config, old_cost, new_temp, False, old_cost

    # Gültiger Zug, Kosten berechnen
    new_cost = bottom_left_density_cost_jit(
        new_conf, num_types, AREA_W, AREA_H,
        WEIGHT_Y, WEIGHT_X, WEIGHT_BOX, WEIGHT_GROUP
    )
    delta = old_cost - new_cost
    # Metropolis-Kriterium
    if delta > 0 or random.random() < math.exp(delta / max(1e-8, temp)):
        new_temp = temp * COOLING_RATE # Akzeptiert -> Kühlen
        return new_conf, new_cost, new_temp, True, new_cost
    else:
        new_temp = temp * (COOLING_RATE**0.01) # Abgelehnt -> Leicht kühlen
        return config, old_cost, new_temp, False, old_cost

# -------------------- "WORKER" FÜR PARALLELISIERUNG --------------------

def _run_sa_worker(args):
    """Diese Funktion wird von jedem CPU-Kern parallel ausgeführt."""
    initial_config, num_types, params = args
    # Lokalen Zufallsgenerator initialisieren
    random.seed(os.getpid() + int(time.time() * 1000) % 1000)

    # Jiggle-Startlösung
    current_conf = greedy_local_packing_jit(
        initial_config, params['AREA_W'], params['AREA_H'],
        step=1.0, max_iterations=500
    )
    current_cost = bottom_left_density_cost_jit(
        current_conf, num_types, params['AREA_W'], params['AREA_H'],
        params['WEIGHT_Y'], params['WEIGHT_X'], params['WEIGHT_BOX_AREA'], params['WEIGHT_GROUPING']
    )
    temp = params['INITIAL_TEMP']
    best_conf = current_conf; best_cost = current_cost

    # SA-Hauptschleife
    for i in range(params['ITER_LIMIT']):
        new_conf, new_cost, new_temp, accepted, resulting_cost = try_mutation_sa_jit(
            current_conf, current_cost, temp, num_types,
            params['AREA_W'], params['AREA_H'], params['COOLING_RATE'],
            params['SWAP_PROBABILITY'], params['TELEPORT_PROBABILITY'], params['ROTATE_PROBABILITY'],
            params['MAX_MOVE_MULTIPLIER'],
            params['WEIGHT_Y'], params['WEIGHT_X'], params['WEIGHT_BOX_AREA'], params['WEIGHT_GROUPING']
        )
        current_conf = new_conf; current_cost = resulting_cost; temp = new_temp
        if current_cost < best_cost:
            best_cost = current_cost; best_conf = current_conf
    return best_conf, best_cost

# -------------------- HAUPTKLASSE (ENGINE - Aktualisiert) --------------------

class PackerEngine:
    """Steuert den "headless" Packprozess unter Berücksichtigung des Gewichts."""

    def __init__(self, params, object_definitions_list, max_container_weight):
        self.params = params
        self.max_container_weight = max_container_weight if max_container_weight is not None else float('inf')
        self.num_cpus = multiprocessing.cpu_count()
        print(f"PackerEngine initialisiert. Max Container Gewicht: {self.max_container_weight if self.max_container_weight != float('inf') else 'Unbegrenzt'} kg.")
        print(f"Nutze {self.num_cpus} CPU-Kerne für {self.params['NUM_SA_RUNS']} SA-Läufe.")

        self.pallet_types = object_definitions_list
        if not self.pallet_types:
            raise SystemExit("Keine Objekt-Definitionen an Engine übergeben.")

        self.type_id_to_original_id_map = {
            d["sequential_type_id"]: d["original_json_id"]
            for d in self.pallet_types
        }
        self.pallet_types_desc = {
            d["sequential_type_id"]: {
                "name": d["name"],
                "geom_type": d["geom_type"]
            } for d in self.pallet_types
        }
        self.num_types = len(self.pallet_types)
        print(f"{self.num_types} eindeutige Objekttypen werden verarbeitet.")


    def _create_initial_pool(self):
        """Erstellt den Pool exakt nach Vorgaben, inkl. Gewicht."""
        pool = []
        if not self.pallet_types:
            print("FEHLER: Keine Palettentypen geladen, Pool kann nicht erstellt werden.")
            return []

        for item_data in self.pallet_types:
            anzahl = item_data["anzahl"]
            seq_type_id = item_data["sequential_type_id"]
            w_bb, h_bb = item_data["w_bb"], item_data["h_bb"]
            area = item_data["area"]
            geom_type = item_data["geom_type"]
            radius = item_data["radius"]
            weight = item_data["weight"] # <-- Gewicht aus Parser holen

            for _ in range(anzahl):
                # Erstelle die 11-Spalten NumPy-Zeile
                item_row = np.array([
                    self.params['AREA_W'] / 2, self.params['AREA_H'] / 2, # X, Y
                    w_bb, h_bb,     # W, H
                    w_bb, h_bb,     # W_orig, H_orig
                    seq_type_id,
                    area, geom_type, radius,
                    weight          # <-- Gewicht hinzufügen
                ])
                pool.append(item_row)

        if not pool:
            print("WARNUNG: Es wurden keine Paletten aus der Datendatei erstellt.")
            return []

        # Sortiere größte zuerst
        pool.sort(key=lambda row: row[IDX_AREA], reverse=True)
        return pool

    @staticmethod
    @jit(nopython=True)
    def _find_best_position_jit(item_template, current_layout, MAX_TRIES, AREA_W, AREA_H):
        """
        Numba-JIT-Version, um die beste Startposition für ein NEUES Item zu finden.
        Gibt (position, metric) zurück.
        """
        w_bb, h_bb = item_template[IDX_W], item_template[IDX_H] # Bounding Box
        x_min, x_max = w_bb / 2, AREA_W - w_bb / 2
        y_min, y_max = h_bb / 2, AREA_H - h_bb / 2
        best_metric = 9e18 # Hoher Startwert für Metrik

        if x_min > x_max or y_min > y_max:
            return (np.array([-1.0, -1.0]), best_metric) # Kann nicht platziert werden

        best_pos = np.array([-1.0, -1.0])

        for attempt in range(MAX_TRIES):
            x = random.uniform(x_min, x_max)
            y = random.uniform(y_min, y_max)
            candidate = item_template.copy()
            candidate[IDX_X], candidate[IDX_Y] = x, y

            if not check_overlap_jit(candidate, current_layout, -1): # -1 = kein Index-Skip
                # Metrik: y + x*0.1 (bevorzugt unten links)
                metric = y + x * 0.1
                if metric < best_metric:
                    best_metric = metric
                    best_pos[0] = x
                    best_pos[1] = y

        return (best_pos, best_metric)

    # Innerhalb der PackerEngine Klasse in Algorithm2d - Kopie.py

    def run_packing_process(self):
        """Führt den Packprozess durch, prüft Gewichtslimit und testet Rotation."""

        unplaced_pool = self._create_initial_pool()
        if not unplaced_pool:
            print("FEHLER: Pool ist leer. Abbruch.")
            return None

        total_items_in_pool = len(unplaced_pool)
        start_item = unplaced_pool.pop(0)

        current_weight = start_item[IDX_WEIGHT]
        if current_weight > self.max_container_weight:
             print(f"FEHLER: Das erste (größte) Objekt (Gewicht: {current_weight}kg) ist bereits schwerer als das Containerlimit ({self.max_container_weight}kg). Abbruch.")
             return None

        global_best_config = np.array([start_item])
        current_packing_round = 1

        print("--- INKREMENTELLE PACKUNG START (Largest First) ---")
        print(f"Gesamte Objekte im Pool: {total_items_in_pool + 1}. Start mit 1 Objekt (Gewicht: {current_weight:.2f} kg).")

        with multiprocessing.Pool(processes=self.num_cpus) as pool:
            while True:
                weight_limit_str = f"{self.max_container_weight if self.max_container_weight != float('inf') else 'inf'}"
                print(f"\n--- Runde {current_packing_round} (Platziert: {global_best_config.shape[0]}, Gewicht: {current_weight:.2f}/{weight_limit_str} kg) ---")
                start_time = time.time()

                # 1. OPTIMIERUNG
                worker_args = [(global_best_config.copy(), self.num_types, self.params)
                             for _ in range(self.params['NUM_SA_RUNS'])]
                results = pool.map(_run_sa_worker, worker_args)
                best_cost_this_round = float('inf')
                best_config_this_round = None
                for conf, cost in results:
                    if cost < best_cost_this_round:
                        best_cost_this_round = cost
                        best_config_this_round = conf
                global_best_config = best_config_this_round
                duration = time.time() - start_time
                print(f" -> SA-Optimierung abgeschlossen in {duration:.2f}s. Beste Kosten: {best_cost_this_round:.2f}")

                # 2. PRÜFUNG: Pool leer?
                if not unplaced_pool:
                    print("\n!!! ENDE: Alle Objekte aus dem Pool wurden platziert (oder konnten nicht platziert werden). !!!")
                    break

                # 3. "BEST-FIT" PLATZIERUNGSLOGIK
                package_added = False
                best_item_to_add = None; best_item_pos = None
                best_item_metric = 9e18; best_item_index_in_pool = -1
                best_item_weight = 0.0
                skipped_due_to_weight = False

                for i, item_template in enumerate(unplaced_pool):
                    item_weight = item_template[IDX_WEIGHT]

                    if current_weight + item_weight > self.max_container_weight:
                        skipped_due_to_weight = True
                        continue # Zu schwer

                    # --- KORREKTUR 1: Argumente hier übergeben ---
                    pos_1, metric_1 = self._find_best_position_jit(
                        item_template, global_best_config,
                        self.params['MAX_PLACEMENT_TRIES'],
                        self.params['AREA_W'], self.params['AREA_H']
                    )

                    pos_2 = np.array([-1.0, -1.0]); metric_2 = 9e18
                    rotated_template = None
                    is_rect = item_template[IDX_GEOM_TYPE] == GEOM_RECT
                    is_not_square = item_template[IDX_W] != item_template[IDX_H]

                    if is_rect and is_not_square:
                        rotated_template = item_template.copy()
                        rotated_template[IDX_W] = item_template[IDX_H_ORIG]
                        rotated_template[IDX_H] = item_template[IDX_W_ORIG]
                        rotated_template[IDX_W_ORIG] = item_template[IDX_W]
                        rotated_template[IDX_H_ORIG] = item_template[IDX_H]

                        # --- KORREKTUR 2: Argumente hier übergeben ---
                        pos_2, metric_2 = self._find_best_position_jit(
                            rotated_template, global_best_config,
                            self.params['MAX_PLACEMENT_TRIES'],
                            self.params['AREA_W'], self.params['AREA_H']
                        )

                    # --- Entscheidung: Beste Ausrichtung ---
                    current_best_metric = 9e18; current_best_pos = None; current_best_template = None
                    pos1_valid = pos_1[0] != -1.0
                    pos2_valid = pos_2[0] != -1.0

                    if pos1_valid and (not pos2_valid or metric_1 <= metric_2):
                        current_best_metric = metric_1; current_best_pos = pos_1; current_best_template = item_template
                    elif pos2_valid:
                        current_best_metric = metric_2; current_best_pos = pos_2; current_best_template = rotated_template

                    # --- Entscheidung: Bester Kandidat bisher? ---
                    if current_best_metric < best_item_metric and current_best_pos is not None:
                        best_item_metric = current_best_metric; best_item_pos = current_best_pos
                        best_item_to_add = current_best_template; best_item_index_in_pool = i
                        best_item_weight = item_weight

                # 4. HINZUFÜGEN / ENDE
                if best_item_to_add is not None:
                    new_item = best_item_to_add.copy()
                    new_item[IDX_X], new_item[IDX_Y] = best_item_pos[0], best_item_pos[1]
                    global_best_config = np.vstack([global_best_config, new_item])
                    current_weight += best_item_weight
                    unplaced_pool.pop(best_item_index_in_pool)
                    current_packing_round += 1
                    package_added = True
                    print(f" -> Objekt {global_best_config.shape[0]} hinzugefügt (Metrik: {best_item_metric:.2f}, Gewicht: {best_item_weight:.2f} kg).")

                if not package_added:
                    if skipped_due_to_weight:
                        print(f"\n!!! ENDE: Gewichtslimit erreicht. Konnte kein weiteres Objekt hinzufügen, ohne {self.max_container_weight} kg zu überschreiten (Pool: {len(unplaced_pool)} übrig). !!!")
                    else:
                        print(f"\n!!! ENDE: Kein Platz gefunden. Konnte für keines der verbleibenden Objekte eine gültige Position finden (Pool: {len(unplaced_pool)} übrig). !!!")
                    break

        return global_best_config, current_weight

# --- EXPORT-FUNKTIONEN ---

def plot_final_solution(config, params, type_desc, output_filename="final_packing_plan.png"):
    """Erstellt ein einzelnes Bild der finalen Lösung."""
    print(f"Speichere finale Lösung als '{output_filename}'...")
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, params['AREA_W']); ax.set_ylim(0, params['AREA_H'])
    ax.set_aspect('equal')
    container = Rectangle((0,0), params['AREA_W'], params['AREA_H'], linewidth=1.2, edgecolor='black', facecolor='none')
    ax.add_patch(container)

    max_type_id = 0
    if config.shape[0] > 0:
        max_type_id = int(np.max(config[:, IDX_TYPE_ID]))

    # Verwende 'viridis' oder eine andere kontinuierliche Colormap, falls tab20 nicht reicht
    try:
        colors = plt.cm.get_cmap('tab20', max_type_id + 1)
    except ValueError:
        print(f"WARNUNG: Mehr als 20 Objekttypen ({max_type_id+1}), verwende 'viridis' Colormap.")
        colors = plt.cm.get_cmap('viridis', max_type_id + 1)


    for i in range(config.shape[0]):
        item = config[i]
        x, y = item[IDX_X], item[IDX_Y]
        w_bb, h_bb = item[IDX_W], item[IDX_H]
        type_id = int(item[IDX_TYPE_ID])
        geom_type = int(item[IDX_GEOM_TYPE])
        radius = item[IDX_RADIUS]
        patch_color = colors(type_id / max(1, max_type_id)) # Normalisiere für kontinuierliche Maps

        if geom_type == GEOM_RECT:
            p = Rectangle(
                (x - w_bb/2, y - h_bb/2), w_bb, h_bb, alpha=0.8, ec='black',
                 fill=True, linewidth=1.0, color=patch_color
            )
        else: # GEOM_CIRCLE
             p = Circle(
                (x, y), radius, alpha=0.8, ec='black',
                fill=True, linewidth=1.0, color=patch_color
            )
        ax.add_patch(p)

    cost = 0.0
    if config.shape[0] > 0:
        cost = bottom_left_density_cost_jit(
            config, max_type_id + 1, params['AREA_W'], params['AREA_H'],
            params['WEIGHT_Y'], params['WEIGHT_X'], params['WEIGHT_BOX_AREA'], params['WEIGHT_GROUPING']
        )
    ax.set_title(f"Finales Packing | {config.shape[0]} Objekte | Gewicht : {final_weight:.2f}")
    plt.savefig(output_filename, dpi=150); plt.close(fig)
    print("PNG-Datei gespeichert.")

def update_and_save_order_json(original_data_root, final_solution_numpy, id_map, final_total_weight, output_filename):
    """
    Füllt die berechneten Daten (Positionen) zurück in die
    ursprüngliche JSON-Struktur (neues Format) und speichert sie.
    """
    print(f"Aktualisiere Bestelldaten und speichere sie zurück nach '{output_filename}'...")

    # 1. Erstelle eine Map der berechneten Platzierungen
    # Map: { original_json_id (name): { "position": {...}, "rotation": {...} } }
    placement_map = {}
    item_instance_counter = {} # Brauchen wir theoretisch nicht mehr, da quantity=1

    for i in range(final_solution_numpy.shape[0]):
        item = final_solution_numpy[i]
        seq_type_id = int(item[IDX_TYPE_ID])
        original_json_id = id_map.get(seq_type_id) # Sollte der 'name' sein
        if not original_json_id:
            print(f"WARNUNG: Konnte Original-ID (Name) für seq_type_id {seq_type_id} nicht finden.")
            continue

        # Da quantity=1, brauchen wir keine instance_id mehr, aber behalten die Zählung für Konsistenz
        instance_count = item_instance_counter.get(original_json_id, 0) + 1
        item_instance_counter[original_json_id] = instance_count
        # instance_id = f"{original_json_id}_{instance_count}" # Nicht mehr benötigt im Export

        pos_dict = {
            "x": round(item[IDX_X] - item[IDX_W]/2, 2), # Bottom-Left X
            "y": round(item[IDX_Y] - item[IDX_H]/2, 2), # Bottom-Left Y
            "z": 0.0
        }
        is_rotated = (item[IDX_GEOM_TYPE] == GEOM_RECT) and (item[IDX_W] != item[IDX_W_ORIG])
        rot_dict = {"x_axis": 0, "y_axis": 0, "z_axis": 90 if is_rotated else 0}

        placement_map[original_json_id] = {
             # "id": original_json_id, # Redundant, da Key
             # "instance_id": instance_id, # Nicht im neuen Format
             "stack_level": 0, # Immer 0 in 2D
             "position": pos_dict,
             "rotation": rot_dict
         }

    # 2. Iteriere durch die *originale* Objektliste und füge Platzierung hinzu
    objects_updated_count = 0
    if "objects" in original_data_root and isinstance(original_data_root["objects"], list):
        for obj in original_data_root["objects"]:
            obj_name = obj.get("name")
            if obj_name in placement_map:
                # Füge das 'placement'-Dictionary hinzu oder aktualisiere es
                obj["placement"] = placement_map[obj_name]
                objects_updated_count += 1
            else:
                 # Optional: Füge leeres Placement hinzu, wenn Objekt nicht platziert wurde
                 if "placement" not in obj:
                     obj["placement"] = {} # Oder setze auf null/default?

    print(f"{objects_updated_count} von {len(placement_map)} platzierten Objekten in Original-JSON gefunden und aktualisiert.")

    # 3. Optional: Füge Gesamtgewicht zum Container hinzu
    if "container" in original_data_root:
        original_data_root["container"]["calculated_total_weight_kg"] = round(final_total_weight, 2)
        # TODO: Effizienz berechnen?
        # original_data_root["container"]["calculated_efficiency_percent"] = ...

    # 4. Speichere die *gesamte* modifizierte Root-Struktur
    try:
        # Kein {"order": ...} Wrapper mehr nötig
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(original_data_root, f, indent=4, ensure_ascii=False) # indent=4 für Lesbarkeit
        print(f"JSON-Datei ('{os.path.basename(output_filename)}') erfolgreich mit Platzierungen aktualisiert.")
    except Exception as e:
        print(f"FEHLER beim Speichern der finalen JSON-Datei: {e}")
# -------------------- HAUPTPROGRAMM (Headless) --------------------
if __name__ == "__main__":

    multiprocessing.freeze_support()
    num_cpus = multiprocessing.cpu_count()

    try: SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError: SCRIPT_DIR = os.getcwd()

    # --- SCHRITT 1: PARSEN ---
    # Verwende den neuen Dateinamen für das neue Format
    INPUT_JSON_FILEPATH = os.path.join(SCRIPT_DIR, "meine_Bestellung.json") # <<< NEUER DATEINAME VORSCHLAG
    try:
        print(f"Lade Bestelldaten aus: {INPUT_JSON_FILEPATH}")
        parser = OrderParser(INPUT_JSON_FILEPATH)
    except Exception as e:
        print(f"Kritischer Fehler beim Starten des Parsers: {e}"); exit()

    # Hole Container-Maße UND Maximalgewicht
    container_info = parser.get_container_dimensions()
    if not container_info:
        print("Konnte Container-Dimensionen/Gewicht nicht laden. Abbruch."); exit()
    AREA_W, AREA_H, MAX_WEIGHT = container_info # Entpacke 3 Werte

    object_definitions = parser.get_object_definitions()
    if not object_definitions:
        print("Keine gültigen Objekte zum Packen gefunden. Abbruch."); exit()

    # Hole die Original-JSON-Struktur (jetzt das Root-Objekt)
    original_json_data_root = parser.get_raw_data() # <<< NEUER NAME DER GETTER-FUNKTION

    # --- SCHRITT 2: PARAMETER ERSTELLEN ---
    parameters = {
        "NUM_SA_RUNS": num_cpus * 2, "RANDOM_SEED": 1,
        "AREA_W": AREA_W, "AREA_H": AREA_H,
        "INITIAL_TEMP": 1.0, "COOLING_RATE": 0.9997,
        "ITER_LIMIT": 100000, # Ggf. erhöhen
        "SWAP_PROBABILITY": 0.20, "TELEPORT_PROBABILITY": 0.15,
        "ROTATE_PROBABILITY": 0.10, "MAX_MOVE_MULTIPLIER": 8.0,
        "WEIGHT_Y": 1.0, "WEIGHT_X": 1.0,
        "WEIGHT_BOX_AREA": 500.0,
        "WEIGHT_GROUPING": 0.5,
        "MAX_PLACEMENT_TRIES": 3000,
    }

    # --- SCHRITT 3: BERECHNUNG STARTEN ---
    random.seed(parameters['RANDOM_SEED'])
    np.random.seed(parameters['RANDOM_SEED'])

    engine = PackerEngine(parameters, object_definitions, MAX_WEIGHT)
    result = engine.run_packing_process()

    # --- SCHRITT 4: ERGEBNISSE EXPORTIEREN ---
    if result is not None:
        final_solution, final_weight = result # Entpacke Ergebnis

        if final_solution is not None and final_solution.shape[0] > 0:
            if hasattr(engine, 'type_id_to_original_id_map'):

                png_filename = os.path.join(SCRIPT_DIR, "final_packing_plan.png")
                # Übergebe die korrekte Map für die Beschreibung im Plot
                plot_final_solution(
                    final_solution, parameters, engine.pallet_types_desc,
                    output_filename=png_filename
                )

             # --- Export in separate Datei ---
                json_output_filename = os.path.join(SCRIPT_DIR, "placed.json") # <<< DATEINAME ANPASSEN
                # Verwende die Root-Daten für den Export
                update_and_save_order_json(
                    original_json_data_root, # <<< ÜBERGEBE ROOT-DATEN
                    final_solution,
                    engine.type_id_to_original_id_map,
                    final_weight,
                    output_filename=json_output_filename
                )
            else:
                 print("FEHLER: ID-Mapping fehlt in der Engine. JSON-Export nicht möglich.")
        else:
            print("Keine Lösung gefunden (möglicherweise passt nichts oder ist zu schwer).")
    else:
         print("Packprozess fehlgeschlagen (siehe Fehlermeldungen oben).")