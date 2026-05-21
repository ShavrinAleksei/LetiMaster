from multiprocessing import Pipe, Process
from agent import agent_process
from bots import bot_process


class Simulator:
    def __init__(self, grid, agent_configs, spawn_points, p_gen, max_steps=800):
        self.static_grid = (grid != 1)
        self.grid = grid
        self.agent_configs = agent_configs
        self.spawn_points = spawn_points
        self.p_gen = p_gen
        self.max_steps = max_steps
        self.num_agents = len(agent_configs)
        self.agent_conns = []
        self.agent_procs = [] 

    def start_agent(self):
        for cfg in self.agent_configs:
            parent_conn, child_conn = Pipe()
            p = Process(target=agent_process,
                        args=(child_conn, self.static_grid, cfg['goal'], cfg['strategy'], None))
            p.start()
            self.agent_conns.append(parent_conn)
            self.agent_procs.append(p)

    def stop_agent(self):
        for conn in self.agent_conns:
            try:
                conn.send('stop')
            except:
                pass
        for p in self.agent_procs:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
        self.agent_conns = []
        self.agent_procs = []

    def reset_agents(self, epsilons=None):
        if epsilons is None:
            epsilons = [0.0] * self.num_agents
        for conn, cfg, eps in zip(self.agent_conns, self.agent_configs, epsilons):
            conn.send(('reset', cfg['start'], eps))

    def run_episode(self, epsilons=None, visualize=False):
        if epsilons is None:
            epsilons = [0.0] * self.num_agents

        self.reset_agents(epsilons)

        parent_bot_conn, child_bot_conn = Pipe()
        bot_p = Process(target=bot_process,
                        args=(child_bot_conn, self.static_grid, self.spawn_points, self.p_gen, None))
        bot_p.start()

        positions = [cfg['start'] for cfg in self.agent_configs]
        prevs = [None] * self.num_agents
        stopped = [False] * self.num_agents
        active = [True] * self.num_agents
        bots = []
        history = [] if visualize else None
        all_success = False
        steps = 0
        collision_occurred = False

        while steps < self.max_steps and not collision_occurred:
            if visualize:
                history.append(([pos for pos in positions],
                                [b['pos'] for b in bots], False))

            bot_positions = [(b['pos'][0], b['pos'][1]) for b in bots]

            parent_bot_conn.send(('step', bots))
            bots = parent_bot_conn.recv()
            bot_positions_after = [tuple(b['pos']) for b in bots]

            new_positions = positions.copy()
            new_prevs = prevs.copy()
            new_stopped = stopped.copy()
            agent_reached = [False] * self.num_agents

            for i in range(self.num_agents):
                if not active[i]:
                    continue

                # Все агенты (активные) считаются препятствиями
                other_agents = [positions[j] for j in range(self.num_agents) if j != i and active[j]]
                visible_obstacles = bot_positions_after + other_agents

                self.agent_conns[i].send(('step', visible_obstacles))
                new_state = self.agent_conns[i].recv()
                new_pos, new_prev, new_st = new_state

                # Проверка выхода за пределы проходимой сетки
                if not self.static_grid[new_pos[1], new_pos[0]]:
                    new_pos = positions[i]
                    new_prev = prevs[i]
                    new_st = stopped[i]

                # Запрет на занятие клетки с другим агентом (активным)
                if new_pos != positions[i]:  # если был реальный ход
                    conflict = False
                    for j in range(self.num_agents):
                        if j != i and active[j] and new_pos == positions[j]:
                            conflict = True
                            break
                    if conflict:
                        # откатываем ход
                        new_pos = positions[i]
                        new_prev = prevs[i]
                        new_st = stopped[i]

                new_positions[i] = new_pos
                new_prevs[i] = new_prev
                new_stopped[i] = new_st

                if tuple(new_pos) == tuple(self.agent_configs[i]['goal']):
                    agent_reached[i] = True

            # Убираем столкнувшихся ботов
            pos_to_bots = {}
            for b in bots:
                p = tuple(b['pos'])
                pos_to_bots.setdefault(p, []).append(b)
            collided_ids = set()
            for p, lst in pos_to_bots.items():
                if len(lst) > 1:
                    for b in lst:
                        collided_ids.add(b['id'])
            if collided_ids:
                bots = [b for b in bots if b['id'] not in collided_ids]
                bot_positions_after = [tuple(b['pos']) for b in bots]

            # Столкновения агент-бот
            for i in range(self.num_agents):
                if not active[i]:
                    continue
                if tuple(new_positions[i]) in bot_positions_after:
                    collision_occurred = True
                    if visualize:
                        history.append(([new_positions[j] for j in range(self.num_agents)],
                                        [b['pos'] for b in bots], True))
                    break

            # Столкновения агент-агент (только между активными)
            if not collision_occurred:
                agent_pos_counts = {}
                for i in range(self.num_agents):
                    if active[i] and not agent_reached[i]:
                        p = new_positions[i]
                        agent_pos_counts.setdefault(p, []).append(i)
                for p, lst in agent_pos_counts.items():
                    if len(lst) > 1:
                        collision_occurred = True
                        if visualize:
                            history.append(([new_positions[j] for j in range(self.num_agents)],
                                            [b['pos'] for b in bots], True))
                        break

            if collision_occurred:
                all_success = False
                break

            positions = new_positions
            prevs = new_prevs
            stopped = new_stopped

            for i in range(self.num_agents):
                if agent_reached[i]:
                    active[i] = False

            steps += 1

            if all(not a for a in active):
                all_success = True
                if visualize:
                    history.append(([positions[j] for j in range(self.num_agents)],
                                    [b['pos'] for b in bots], False))
                break

        parent_bot_conn.send('stop')
        bot_p.join(timeout=2)
        if bot_p.is_alive():
            bot_p.terminate()

        if visualize:
            return all_success, steps, history
        return all_success, steps