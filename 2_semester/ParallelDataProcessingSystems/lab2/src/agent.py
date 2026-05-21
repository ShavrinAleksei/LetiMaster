import random
import numpy as np
from collections import defaultdict 

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ACTIONS = [(1,0), (-1,0), (0,1), (0,-1), (0,0)]

def free_neighbors(pos, static_grid):
    x, y = pos
    h, w = static_grid.shape
    neighbors = []
    for dx, dy in DIRECTIONS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and static_grid[ny, nx]:
            neighbors.append((nx, ny))
    return neighbors

def get_valid_actions(pos, grid):
    valid = []
    for dx, dy in ACTIONS[:-1]:
        nx, ny = pos[0]+dx, pos[1]+dy
        if 0 <= nx < grid.shape[1] and 0 <= ny < grid.shape[0] and grid[ny, nx]:
            valid.append((dx, dy))
    valid.append((0,0))
    return valid

def get_state(pos, bot_positions, static_grid, goal=None):
    x, y = pos
    h, w = static_grid.shape
    bot_set = set(bot_positions) if bot_positions else set()

    def obstacles_in_dir(dx, dy):
        res = []
        for d in (1, 2):
            nx, ny = x + dx*d, y + dy*d
            if 0 <= nx < w and 0 <= ny < h:
                res.append((nx, ny) in bot_set)
            else:
                res.append(False)
        return res

    up_obs    = obstacles_in_dir(0, -1)
    down_obs  = obstacles_in_dir(0,  1)
    left_obs  = obstacles_in_dir(-1, 0)
    right_obs = obstacles_in_dir( 1, 0)

    def is_passable(nx, ny):
        return 0 <= nx < w and 0 <= ny < h and static_grid[ny, nx]

    up_pass    = [is_passable(x, y-1), is_passable(x, y-2)]
    down_pass  = [is_passable(x, y+1), is_passable(x, y+2)]
    left_pass  = [is_passable(x-1, y), is_passable(x-2, y)]
    right_pass = [is_passable(x+1, y), is_passable(x+2, y)]

    if goal:
        goal_dx = np.sign(goal[0] - x)
        goal_dy = np.sign(goal[1] - y)
    else:
        goal_dx, goal_dy = 0, 0

    return (x, y,
            up_obs[0], up_obs[1], down_obs[0], down_obs[1],
            left_obs[0], left_obs[1], right_obs[0], right_obs[1],
            up_pass[0], up_pass[1], down_pass[0], down_pass[1],
            left_pass[0], left_pass[1], right_pass[0], right_pass[1],
            goal_dx, goal_dy)

def choose_action_q(Q, state, epsilon, rng, valid_actions):
    if rng.random() < epsilon:
        return rng.choice(valid_actions)
    if state not in Q:
        Q[state] = {a: 0.0 for a in ACTIONS}
    q_vals = {a: Q[state][a] for a in valid_actions}
    max_q = max(q_vals.values())
    max_actions = [a for a, v in q_vals.items() if v == max_q]
    return rng.choice(max_actions)

def bot_like_move(pos, prev, stopped, static_grid, rng):
    """Стратегия движения, идентичная обычным ботам."""
    if pos is None:
        return pos, prev, stopped

    if stopped:
        next_pos = prev if prev is not None else pos
        new_stopped = False
        new_prev = pos
        return next_pos, new_prev, new_stopped

    all_nb = free_neighbors(pos, static_grid)
    candidates = [n for n in all_nb if n != prev] if prev is not None else all_nb
    if not candidates:
        candidates = [prev] if prev is not None else all_nb
    if not candidates:
        return pos, pos, False

    total_passable = len(all_nb)
    if total_passable == 1:
        chosen = candidates[0]
    elif total_passable == 2:
        chosen = candidates[0]
    elif total_passable == 3:
        chosen = rng.choice(candidates)
    elif total_passable == 4:
        if prev is not None and rng.random() < 0.1:
            return pos, prev, True
        else:
            chosen = rng.choice(candidates)
    else:
        chosen = candidates[0]

    return chosen, pos, False

def agent_process(conn, static_grid, goal, strategy, rng_seed=None):
    rng = random.Random(rng_seed)
    agent_pos = None
    prev = None
    stopped = False
    last_action = None
    alpha = 0.5
    gamma = 0.9
    epsilon = 0.1
    Q = None

    if strategy in ('sarsa', 'q_learning'):
        Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})

    try:
        while True:
            msg = conn.recv()
            if msg == 'stop':
                break
            elif msg[0] == 'reset':
                agent_pos, eps = msg[1], msg[2]
                prev = None
                stopped = False
                last_action = None
                if strategy in ('sarsa', 'q_learning'):
                    epsilon = eps
            elif msg[0] == 'step':
                bot_positions = msg[1]
                if strategy == 'bot_like':
                    if agent_pos is None:
                        conn.send((agent_pos, prev, stopped))
                    else:
                        new_pos, new_prev, new_stopped = bot_like_move(agent_pos, prev, stopped, static_grid, rng)
                        agent_pos, prev, stopped = new_pos, new_prev, new_stopped
                        conn.send((new_pos, new_prev, new_stopped))
                elif strategy in ('sarsa', 'q_learning'):
                    state = get_state(agent_pos, bot_positions, static_grid, goal)
                    valid_actions = get_valid_actions(agent_pos, static_grid)

                    if last_action is None:
                        action = choose_action_q(Q, state, epsilon, rng, valid_actions)
                    else:
                        action = last_action

                    nx, ny = agent_pos[0] + action[0], agent_pos[1] + action[1]
                    if 0 <= nx < static_grid.shape[1] and 0 <= ny < static_grid.shape[0] and static_grid[ny, nx]:
                        new_pos = (nx, ny)
                    else:
                        new_pos = agent_pos

                    reward = -1.0
                    if new_pos == goal:
                        reward = 100.0
                    elif new_pos == agent_pos:
                        reward = -2.0

                    next_state = get_state(new_pos, bot_positions, static_grid, goal)
                    next_valid = get_valid_actions(new_pos, static_grid)
                    next_action = choose_action_q(Q, next_state, epsilon, rng, next_valid)

                    if strategy == 'sarsa':
                        Q[state][action] += alpha * (reward + gamma * Q[next_state][next_action] - Q[state][action])
                    else:  # Q-learning
                        max_next = max(Q[next_state][a] for a in next_valid)
                        Q[state][action] += alpha * (reward + gamma * max_next - Q[state][action])

                    last_action = next_action
                    agent_pos = new_pos
                    prev = (agent_pos[0] - action[0], agent_pos[1] - action[1]) if action != (0, 0) else agent_pos
                    conn.send((agent_pos, prev, False))
    except (EOFError, BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        conn.close()