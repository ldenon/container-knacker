import numpy as np
import matplotlib.pyplot as plt
from math import sqrt, pi
# from geneticalgorithm import geneticalgorithm as ga  # <- nur aktivieren, wenn du das Paket nutzt
from geneticalgorithm import geneticalgorithm as ga


class Rec:
    def __init__(self, width, height, id):
        self.id = id
        self.width = width
        self.height = height


class Circle:
    def __init__(self, radius, id):
        self.id = id
        self.radius = radius


class TwoDimensionalCircleArea:
    def __init__(self, area_width, area_height, shapes: list, verbose=False):
        self.area_width = area_width
        self.area_height = area_height
        self.rectangles = shapes  # kann Rechtecke und Kreise enthalten
        self.verbose = verbose

    # -----------------------------
    # Hilfsfunktionen
    # -----------------------------
    def check_overlap(self, positions: list[tuple[float, float]]) -> bool:
        """Überprüft Überlappungen zwischen beliebigen Formen."""
        for i, (pos1, shape1) in enumerate(zip(positions, self.rectangles)):
            x1, y1 = pos1

            for j, (pos2, shape2) in enumerate(zip(positions, self.rectangles)):
                if i == j:
                    continue
                x2, y2 = pos2

                # Rechteck - Rechteck
                if isinstance(shape1, Rec) and isinstance(shape2, Rec):
                    if not (x1 + shape1.width <= x2 or x2 + shape2.width <= x1 or
                            y1 + shape1.height <= y2 or y2 + shape2.height <= y1):
                        return True

                # Kreis - Kreis
                elif isinstance(shape1, Circle) and isinstance(shape2, Circle):
                    dist = sqrt((x1 - x2)**2 + (y1 - y2)**2)
                    if dist < shape1.radius + shape2.radius:
                        return True

                # Rechteck - Kreis
                else:
                    # Kreisrechteck-Kollision: Projektion des Kreises auf Rechteck prüfen
                    circle = shape1 if isinstance(shape1, Circle) else shape2
                    rect = shape2 if isinstance(shape1, Circle) else shape1
                    cx, cy = (x1, y1) if isinstance(shape1, Circle) else (x2, y2)
                    rx, ry = (x1, y1) if isinstance(shape1, Rec) else (x2, y2)

                    # Nächster Punkt auf Rechteck zum Kreiszentrum
                    nearest_x = max(rx, min(cx, rx + rect.width))
                    nearest_y = max(ry, min(cy, ry + rect.height))
                    dist = sqrt((cx - nearest_x)**2 + (cy - nearest_y)**2)
                    if dist < circle.radius:
                        return True
        return False

    def get_used_space(self, positions) -> float:
        """Berechnet die maximal genutzte Fläche (rechteckige Bounding Box)."""
        max_x, max_y = 0, 0
        for pos, shape in zip(positions, self.rectangles):
            x, y = pos
            if isinstance(shape, Rec):
                max_x = max(max_x, x + shape.width)
                max_y = max(max_y, y + shape.height)
            elif isinstance(shape, Circle):
                max_x = max(max_x, x + shape.radius)
                max_y = max(max_y, y + shape.radius)
        return max_x * max_y

    def check_extents(self, positions) -> bool:
        """Überprüft, ob alle Formen innerhalb der Fläche bleiben."""
        for pos, shape in zip(positions, self.rectangles):
            x, y = pos
            if isinstance(shape, Rec):
                if x < 0 or y < 0 or x + shape.width > self.area_width or y + shape.height > self.area_height:
                    return True
            elif isinstance(shape, Circle):
                if x - shape.radius < 0 or y - shape.radius < 0 or x + shape.radius > self.area_width or y + shape.radius > self.area_height:
                    return True
        return False

    # -----------------------------
    # Bewertung & Kontrolle
    # -----------------------------
    def wrong_solution(self, positions):
        extent_violated = self.check_extents(positions)
        overlap_violated = self.check_overlap(positions)
        if self.verbose:
            print(f"Extent violated: {extent_violated}, Overlap violated: {overlap_violated}")
        return extent_violated or overlap_violated

    def f(self, X):
        pen = 0
        positions = [(X[i], X[i+1]) for i in range(0, len(X), 2)]
        if self.wrong_solution(positions):
            pen = 1e7
        used_space = self.get_used_space(positions)
        return used_space + pen

    # -----------------------------
    # Visualisierung
    # -----------------------------
    def show_solution(self, best_variable, alpha=0.5, edgecolor='black'):
        fig, ax = plt.subplots()
        for i in range(0, len(best_variable), 2):
            x = best_variable[i]
            y = best_variable[i + 1]
            shape = self.rectangles[i // 2]
            if isinstance(shape, Rec):
                patch = plt.Rectangle((x, y), width=shape.width, height=shape.height,
                                      alpha=alpha, edgecolor=edgecolor)
            elif isinstance(shape, Circle):
                patch = plt.Circle((x, y), radius=shape.radius, alpha=alpha, edgecolor=edgecolor)
            ax.add_patch(patch)

        plt.xlim(0, self.area_width)
        plt.ylim(0, self.area_height)
        ax.set_aspect('equal', adjustable='box')
        plt.show()

    def optimize_solution(self, solution: list[tuple[float, float]], shapes: list) -> list[tuple[float, float]]:
        """
        Verschiebt Formen (Rechtecke & Kreise) so weit wie möglich nach unten und links,
        ohne dass sie sich überlappen oder die Grenzen verlassen.

        :param solution: Liste der aktuellen Positionen [(x, y), ...]
        :param shapes: Liste von Objekten (Rec oder Circle)
        :return: Neue Liste optimierter Positionen [(x, y), ...]
        """
        # Mutable Kopie
        positions = solution.copy()

        # Reihenfolge: von unten-links nach oben-rechts
        order = sorted(range(len(shapes)), key=lambda i: (positions[i][1], positions[i][0]))

        # Schrittweite (präzise, aber nicht zu klein)
        step = 0.01

        for i in order:
            x, y = positions[i]
            shape = shapes[i]

            # So weit wie möglich nach unten schieben
            while True:
                new_y = y - step
                if new_y < 0:
                    break

                new_positions = positions.copy()
                new_positions[i] = (x, new_y)

                # Überprüfen, ob Kollision oder Randverletzung entsteht
                if self.check_overlap(new_positions) or self.check_extents(new_positions):
                    break
                y = new_y

            # So weit wie möglich nach links schieben
            while True:
                new_x = x - step
                if new_x < 0:
                    break

                new_positions = positions.copy()
                new_positions[i] = (new_x, y)

                if self.check_overlap(new_positions) or self.check_extents(new_positions):
                    break
                x = new_x

            # Neue Position speichern
            positions[i] = (x, y)

        return positions


    def optimize(self):
        varbound=np.array([[0,10]] * (2*len(self.rectangles)))
        algorithm_param = {'max_num_iteration': 3000,\
                   'population_size':5000,\
                   'mutation_probability':0.1,\
                   'elit_ratio': 0.01,\
                   'crossover_probability': 0.5,\
                   'parents_portion': 0.3,\
                   'crossover_type':'uniform',\
                   'max_iteration_without_improv':None}
        model=ga(
            function=self.f,
            dimension=2*len(self.rectangles),
            variable_type='real',
            variable_boundaries=varbound
            )
        
        model.run()
        print("Genetic Solution")
        print(model.best_function)
        print(model.best_variable)
        self.show_solution(model.best_variable)
        optimized_positions = self.optimize_solution([(model.best_variable[i], model.best_variable[i+1]) for i in range(0, len(model.best_variable), 2)], self.rectangles)
        flat_positions = [coord for pos in optimized_positions for coord in pos]
        self.show_solution(flat_positions)
        print("Final optimized positions:", optimized_positions)
        print("Final used area:", self.get_used_space(optimized_positions))
        print("Final overlap/extents violated:", self.wrong_solution(optimized_positions))


if __name__ == "__main__":
    # Beispielhafte Nutzung
    shapes = [Rec(2, 1, id=1), Circle(0.5, id=2), Rec(1, 1, id=3), Circle(1, id=4), Rec(1.5, 0.5, id=5), Circle(0.75, id=6), Rec(0.5, 2, id=7)]
    area = TwoDimensionalCircleArea(10, 10, shapes, verbose=False)
    area.optimize()

    # Beispielhafte Positionen
    # 
    # print("Initial used space:", area.get_used_space(positions))
    # optimized_positions = area.optimize_solution(positions, shapes)
    # print("Optimized positions:", optimized_positions)
    # print("Optimized used space:", area.get_used_space(optimized_positions))
# 
    # Visualisierung
    # flat_positions = [coord for pos in optimized_positions for coord in pos]
    # area.show_solution(flat_positions)