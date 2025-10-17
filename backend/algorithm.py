import numpy as np
from geneticalgorithm import geneticalgorithm as ga


class Rectangle:
    def __init__(self, width, height, id):
        self.id = id
        self.width = width
        self.height = height


class TwoDimensionalArea:
    def __init__(self, area_width, area_height, rectangles:list[Rectangle]):
        self.area_width = area_width
        self.area_height = area_height
        self.rectangles = rectangles
    
    def __check_overlap(self, positions:list[tuple[float, float]]):
        for pos, rect in zip(positions, self.rectangles):
            x1, y1 = pos
            w1, h1 = rect.width, rect.height
            id = rect.id
            for other_pos, other_rect in zip(positions, self.rectangles):
                if id == other_rect.id:
                    continue
                x2, y2 = other_pos
                w2, h2 = other_rect.width, other_rect.height
                if (x1+w1 > x2 and y1+h1 > y2) or (x2+w2 > x1 and y2+h2 > y1):
                    return False
            return True
    
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
                return False

    def __check_solution(self, positions):
        pass
    
    def f(self,X):
        pen=0
        if self.__check_solution(X)==False:
            pen=100000
        used_space = self.__get_used_space(X)
        return used_space+pen

    def optimize(self):
        varbound=np.array([[0,10]]*3)
        model=ga(
            function=self.f,
            dimension=3,
            variable_type='real',
            variable_boundaries=varbound
            )
        model.run()

if __name__ == "__main__":
    rects = [Rectangle(2, 3, 0), Rectangle(4, 1, 1), Rectangle(1, 1, 2)]
    area = TwoDimensionalArea(10, 10, rects)
    area.optimize()