import numpy as np
import matplotlib.pyplot as plt
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


class TwoDimensionalArea:
    def __init__(self, area_width, area_height, rectangles:list[Rec], verbose=False):
        self.area_width = area_width
        self.area_height = area_height
        self.rectangles = rectangles
        self.verbose = verbose

    def __check_overlap(self, positions: list[tuple[float, float]]) -> bool:
        for pos, rect in zip(positions, self.rectangles):
            x1, y1 = pos
            w1, h1 = rect.width, rect.height
            id1 = rect.id

            for other_pos, other_rect in zip(positions, self.rectangles):
                if id1 == other_rect.id:
                    continue

                x2, y2 = other_pos
                w2, h2 = other_rect.width, other_rect.height

                # Prüfen, ob sich die Rechtecke überlappen
                if not (x1 + w1 <= x2 or x2 + w2 <= x1 or 
                        y1 + h1 <= y2 or y2 + h2 <= y1):
                    return True  # Überlappung gefunden

        return False  # Keine Überlappung
    
    def __get_used_space(self, positions)->float:
        """
        The used area is the highest x and y position used.

        Args:
            positions (_type_): _description_

        Returns:
            float: _description_
        """
        max_x = 0
        max_y = 0
        for pos, rect in zip(positions, self.rectangles):
            x, y = pos
            max_x = max(max_x, x + rect.width)
            max_y = max(max_y, y + rect.height)
        return max_x * max_y
        
    def __check_extents(self, positions):
        for pos, rect in zip(positions, self.rectangles):
            x, y = pos
            if x < 0 or y < 0 or x + rect.width > self.area_width or y + rect.height > self.area_height:
                return True
        return False

    def wrong_solution(self, positions):
        extent_violated = self.__check_extents(positions)
        overlap_violated = self.__check_overlap(positions)
        if self.verbose:
            print(f"Extent violated: {extent_violated}, Overlap violated: {overlap_violated}")
        correct_solution = self.__check_extents(positions) or self.__check_overlap(positions)
        return correct_solution
    
    def f(self,X):
        pen=0
        positions = [(X[i], X[i+1]) for i in range(0, len(X), 2)]
        if self.wrong_solution(positions)==True:
            pen=10000000
        used_space = self.__get_used_space(positions)
        return used_space+pen

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
        if self.verbose:
            print("Optimized Solution")
            print(model.best_function)
            print(model.best_variable)
        self.show_solution(model.best_variable)
        print("Final used area:", self.__get_used_space([(model.best_variable[i], model.best_variable[i+1]) for i in range(0, len(model.best_variable), 2)]))
        print("Final overlap/extents violated:", self.wrong_solution([(model.best_variable[i], model.best_variable[i+1]) for i in range(0, len(model.best_variable), 2)]))

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
                if self.__check_overlap(new_positions) or self.__check_extents(new_positions):
                    break
                y = new_y

            # So weit wie möglich nach links schieben
            while True:
                new_x = x - step
                if new_x < 0:
                    break

                new_positions = positions.copy()
                new_positions[i] = (new_x, y)

                if self.__check_overlap(new_positions) or self.__check_extents(new_positions):
                    break
                x = new_x

            # Neue Position speichern
            positions[i] = (x, y)

        return positions

    def show_solution(self, best_variable, alpha=0.5, edgecolor='black'):
        # todo: give a visualization of the solution
        fig, ax = plt.subplots()
        patches_list = []
        for i in range(0, len(best_variable), 2):
            x = best_variable[i]
            y = best_variable[i+1]
            rect = self.rectangles[i//2]
            rectangle_patch = plt.Rectangle((x, y), width=rect.width, height=rect.height, alpha=alpha, edgecolor=edgecolor)
            patches_list.append(rectangle_patch)
            ax.add_patch(rectangle_patch)

        plt.xlim(0, self.area_width)
        plt.ylim(0, self.area_height)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.show()

if __name__ == "__main__":
    rects = [Rec(2, 3, 0), Rec(4, 1, 1), Rec(1, 1, 2), Rec(3, 2, 3), Rec(2, 2, 4), Rec(1, 4, 5)]
    area = TwoDimensionalArea(10, 10, rects, verbose=False)
    # area.optimize()
    one_solution =  [1.35825620e+00, 2.43885227e+00, 1.06864995e+00, 5.49522753e+00,
 4.00413213e+00, 3.19131925e+00, 2.06356943e+00, 1.89976894e-01,
 1.76967667e-03, 1.34729283e-01, 3.97595896e-02, 2.17028610e+00]
    positions = [(one_solution[i], one_solution[i+1]) for i in range(0, len(one_solution), 2)]
    optimized_solution = area.optimize_solution(
        positions,
        rects)
    # one_solution = [0, 0, 2, 0, 6, 0, 0, 3, 3, 3, 7, 0]
    # print(positions)
    optimized_solution_flat = []
    for pos in optimized_solution:
        optimized_solution_flat.extend(pos)
    area.show_solution(optimized_solution_flat)
    print("It is a wrong solution:", area.wrong_solution(positions))