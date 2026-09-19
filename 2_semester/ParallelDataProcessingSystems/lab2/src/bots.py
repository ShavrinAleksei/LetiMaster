import random
import numpy as np

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)] 

def free_neighbors(pos, static_grid):
    x, y = pos
    h, w = static_grid.shape
    neighbors = []
    for dx, dy in DIRECTIONS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and static_grid[ny, nx]:
            neighbors.append((nx, ny))
    return neighbors

def bot_process(conn, static_grid, spawn_points, p_gen, rng_seed=None):
    rng = random.Random(rng_seed)
    try:
        while True:
            if conn.poll(0.1):
                msg = conn.recv()
                if msg == 'stop':
                    break
                cmd, bots = msg
                occupied = set()
                for b in bots:
                    occupied.add(tuple(b['pos']))
                for sp in spawn_points:
                    if sp not in occupied and rng.random() < p_gen:
                        new_bot = {
                            'id': rng.getrandbits(31),
                            'pos': sp,
                            'prev': None,
                            'stopped': False,
                            'steps_left': rng.randint(15, 150)
                        }
                        bots.append(new_bot)
                        occupied.add(sp)

                updated_bots = []
                for b in bots:
                    steps_left = b['steps_left'] - 1
                    if steps_left <= 0:
                        continue
                    pos = b['pos']
                    prev = b['prev']
                    stopped = b['stopped']
                    new_stopped = False
                    next_pos = None

                    if stopped:
                        next_pos = prev
                        new_stopped = False
                        new_prev = pos
                    else:
                        all_nb = free_neighbors(pos, static_grid)
                        candidates = [n for n in all_nb if n != prev] if prev is not None else all_nb
                        if not candidates:
                            candidates = [prev] if prev is not None else all_nb
                        if not candidates:
                            next_pos = pos
                            new_prev = pos
                        else:
                            total_passable = len(all_nb)
                            if total_passable == 1:
                                chosen = candidates[0]
                                next_pos = chosen
                                new_prev = pos
                            elif total_passable == 2:
                                chosen = candidates[0]
                                next_pos = chosen
                                new_prev = pos
                            elif total_passable == 3:
                                chosen = rng.choice(candidates)
                                next_pos = chosen
                                new_prev = pos
                            elif total_passable == 4:
                                if prev is not None and rng.random() < 0.1:
                                    new_stopped = True
                                    next_pos = pos
                                    new_prev = prev
                                else:
                                    chosen = rng.choice(candidates)
                                    next_pos = chosen
                                    new_prev = pos
                            else:
                                chosen = candidates[0]
                                next_pos = chosen
                                new_prev = pos

                    updated_bots.append({
                        'id': b['id'],
                        'pos': next_pos,
                        'prev': new_prev,
                        'stopped': new_stopped,
                        'steps_left': steps_left
                    })
                conn.send(updated_bots)
    except (EOFError, BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        conn.close()