import numpy as np

class Navigation:
    """Класс для навигации по карте"""
    
    ROAD_VALUES = {0, 2, 3, 4}
    
    def __init__(self, grid):
        self.grid = grid
    
    def load_map(self, filename="citymap.txt"):
        """Загружает матрицу карты из текстового файла"""
        with open(filename, "r") as f:
            rows = [list(map(int, line.split())) for line in f if line.strip()]
        self.grid = np.array(rows)
        return self.grid
    
    def find_start_and_goal(self):
        """Находит на карте стартовую точку (2) и цель (4)"""
        start_points = []
        goal_pos = None
        
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j] == 2:
                    start_points.append((i, j))
                elif self.grid[i][j] == 4:
                    goal_pos = (i, j)
        
        return start_points, goal_pos
    
    def get_valid_neighbors(self, pos):
        """Возвращает список координат соседних клеток, доступных для перемещения"""
        x, y = pos
        h = len(self.grid)
        w = len(self.grid[0])
        candidates = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [(nx, ny) for nx, ny in candidates 
                if 0 <= nx < h and 0 <= ny < w and self.grid[nx][ny] in self.ROAD_VALUES]
    
    def classify_cell(self, pos, prev_pos):
        """Определяет тип текущей клетки: 'start', 'dead_end', 'intersection', 'straight'"""
        if prev_pos is None:
            return 'start'
        
        valid = self.get_valid_neighbors(pos)
        forward_options = [n for n in valid if n != prev_pos]
        
        if len(forward_options) == 0:
            return 'dead_end'
        elif len(forward_options) >= 2:
            return 'intersection'
        else:
            return 'straight'
    
    def resolve_direction(self, pos, prev_pos, choice):
        """Преобразует направление в координаты следующей клетки"""
        if choice == 'stop':
            return pos
        
        h = len(self.grid)
        w = len(self.grid[0])
        
        dx, dy = pos[0] - prev_pos[0], pos[1] - prev_pos[1]
        
        directions = {
            'straight': (dx, dy),
            'back': (-dx, -dy),
            'left': (-dy, dx),
            'right': (dy, -dx)
        }
        
        target_vec = directions.get(choice)
        if target_vec is None:
            raise ValueError("Недопустимое значение направления: " + choice)
        
        nx, ny = pos[0] + target_vec[0], pos[1] + target_vec[1]
        
        if 0 <= nx < h and 0 <= ny < w and self.grid[nx][ny] in self.ROAD_VALUES:
            return (nx, ny)
        return pos