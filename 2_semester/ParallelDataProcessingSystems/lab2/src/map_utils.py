import numpy as np


def load_map(filepath):
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    raw = np.array([list(map(int, line.split())) for line in lines], dtype=int)
    grid = raw
    height, width = grid.shape

    starts = []   # список стартовых позиций
    goals = []
    spawn_points = []

    for y in range(height):
        for x in range(width):
            val = grid[y, x]
            if val == 2:
                starts.append((x, y))
            elif val == 4: 
                goals.append((x, y))
            elif val == 3:
                spawn_points.append((x, y))

    if len(starts) < 1 or len(goals) < 1:
        raise ValueError("Карта должна содержать хотя бы один старт (2) и одну цель (4).")

    return grid, (height, width), starts, goals, spawn_points