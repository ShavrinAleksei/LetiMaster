import multiprocessing as mp
import random
from navigation import Navigation

class Simulator:
    """Многопроцессный симулятор движения агента и ботов"""
    
    def __init__(self, grid, goal_pos, spawn_prob, strategy_weights):
        self.grid = grid
        self.nav = Navigation(grid)
        self.goal_pos = goal_pos
        self.spawn_prob = spawn_prob
        self.strategy_weights = strategy_weights
    
    def init_shared_state(self, start_pos):
        """Создает разделяемое состояние для синхронизации процессов"""
        manager = mp.Manager()
        shared = manager.dict()
        shared['grid'] = [list(row) for row in self.grid]
        shared['agent'] = manager.dict({
            'pos': start_pos,
            'prev': start_pos,
            'steps': 0,
            'stop_next_reverse': False,
            'alive': True
        })
        shared['bots'] = []
        shared['goal_pos'] = self.goal_pos
        shared['episode_done'] = False
        shared['success'] = False
        shared['collided'] = False
        return shared
    
    def check_collisions(self, shared):
        """Проверяет столкновения между агентом и ботами, а также ботов между собой"""
        agent_pos = shared['agent']['pos']
        agent_prev = shared['agent']['prev']
        current_bots = shared['bots']
        
        # Столкновение агента с ботом (на одной клетке)
        for bot in current_bots:
            if bot['pos'] == agent_pos:
                shared['collided'] = True
                shared['episode_done'] = True
                shared['success'] = False
                return
        
        # агент и бот разминулись (поменялись местами)
        for bot in current_bots:
            bot_prev = bot['prev']
            bot_current = bot['pos']
            
            # Если агент был на месте, где сейчас бот, И бот был на месте, где сейчас агент
            if bot_prev == agent_pos and bot_current == agent_prev:
                shared['collided'] = True
                shared['episode_done'] = True
                shared['success'] = False
                return
        
            # Столкновения ботов между собой (на одной клетке)
            pos_counts = {}
            for bot in current_bots:
                p = bot['pos']
                pos_counts[p] = pos_counts.get(p, 0) + 1
            
            # боты разминулись (поменялись местами)
            for i, bot1 in enumerate(current_bots):
                for bot2 in current_bots[i+1:]:
                    if bot1['prev'] == bot2['pos'] and bot2['prev'] == bot1['pos']:
                        # Удаляем обоих ботов
                        pos_counts[bot1['pos']] = 0
                        pos_counts[bot2['pos']] = 0
        
        surviving_bots = [bot for bot in current_bots if pos_counts[bot['pos']] == 1]
        shared['bots'] = surviving_bots
        
        # Проверка достижения цели
        if agent_pos == shared['goal_pos']:
            shared['episode_done'] = True
            shared['success'] = True
    
    def agent_worker(self, shared, lock, barrier):
        """Процесс управления агентом-доставщиком"""
        directions = ['straight', 'right', 'left', 'stop']
        
        while True:
            lock.acquire()
            if shared['episode_done']:
                lock.release()
                break
            
            agent = shared['agent']
            pos = agent['pos']
            prev = agent['prev']
            grid = shared['grid']
            
            # Разворот после остановки
            if agent['stop_next_reverse']:
                direction = 'back'
                agent['stop_next_reverse'] = False
                next_pos = self.nav.resolve_direction(pos, prev, direction)
            
            # Первый шаг (позиция совпадает с предыдущей)
            elif prev == pos:
                valid = self.nav.get_valid_neighbors(pos)
                next_pos = random.choice(valid) if valid else pos
            
            else:
                cell_type = self.nav.classify_cell(pos, prev)
                
                if cell_type == 'dead_end':
                    direction = 'back'
                    next_pos = self.nav.resolve_direction(pos, prev, direction)
                
                elif cell_type == 'intersection':
                    direction = random.choices(directions, weights=self.strategy_weights, k=1)[0]
                    if direction == 'stop':
                        agent['stop_next_reverse'] = True
                        next_pos = pos
                    else:
                        next_pos = self.nav.resolve_direction(pos, prev, direction)
                
                else:  # straight
                    direction = 'straight'
                    next_pos = self.nav.resolve_direction(pos, prev, direction)
            
            agent['prev'] = pos
            agent['pos'] = next_pos
            agent['steps'] = agent['steps'] + 1
            
            lock.release()
            
            try:
                barrier.wait(timeout=10.0)
            except Exception:
                break
    
    def bot_worker(self, shared, lock, barrier):
        """Процесс управления пулом транспортных средств"""
        while True:
            lock.acquire()
            if shared['episode_done']:
                lock.release()
                break
            
            grid = shared['grid']
            h = len(grid)
            w = len(grid[0])
            
            # Поиск всех точек спавна (значение 3 на карте)
            spawn_points = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
            
            current_bots = shared['bots']
            
            # Спавн нового бота
            if random.random() < self.spawn_prob and spawn_points:
                spawn_pos = random.choice(spawn_points)
                current_bots.append({
                    'pos': spawn_pos,
                    'prev': spawn_pos,
                    'lifetime': random.randint(15, 150),
                    'stop_next_reverse': False,
                    'alive': True
                })
            
            active_bots = []
            for bot in current_bots:
                if not bot.get('alive', True):
                    continue
                
                bot['lifetime'] = bot['lifetime'] - 1
                if bot['lifetime'] <= 0:
                    continue
                
                pos = bot['pos']
                prev = bot['prev']
                
                # Разворот после остановки
                if bot['stop_next_reverse']:
                    direction = 'back'
                    bot['stop_next_reverse'] = False
                    next_pos = self.nav.resolve_direction(pos, prev, direction)
                
                elif prev == pos:
                    valid = self.nav.get_valid_neighbors(pos)
                    next_pos = random.choice(valid) if valid else pos
                
                else:
                    cell_type = self.nav.classify_cell(pos, prev)
                    
                    if cell_type == 'dead_end':
                        direction = 'back'
                        next_pos = self.nav.resolve_direction(pos, prev, direction)
                    
                    elif cell_type == 'intersection':
                        valid = self.nav.get_valid_neighbors(pos)
                        forward = [n for n in valid if n != prev]
                        if len(forward) > 0 and random.random() < 0.1:
                            bot['stop_next_reverse'] = True
                            next_pos = pos
                        else:
                            direction = random.choice(['straight', 'left', 'right'])
                            next_pos = self.nav.resolve_direction(pos, prev, direction)
                    
                    else:  # straight
                        direction = 'straight'
                        next_pos = self.nav.resolve_direction(pos, prev, direction)
                
                bot['prev'] = pos
                bot['pos'] = next_pos
                active_bots.append(bot)
            
            shared['bots'] = active_bots
            lock.release()
            
            try:
                barrier.wait(timeout=10.0)
            except Exception:
                break
    
    def run_episode(self, start_pos):
        """Запускает один эпизод симуляции"""
        shared = self.init_shared_state(start_pos)
        lock = mp.Lock()
        barrier = mp.Barrier(3)
        
        agent_proc = mp.Process(target=self.agent_worker, args=(shared, lock, barrier))
        bot_proc = mp.Process(target=self.bot_worker, args=(shared, lock, barrier))
        
        agent_proc.start()
        bot_proc.start()
        
        max_steps = 250
        
        for _ in range(max_steps):
            try:
                barrier.wait(timeout=10.0)
            except Exception:
                shared['episode_done'] = True
                break
            
            lock.acquire()
            self.check_collisions(shared)
            lock.release()
            
            if shared['episode_done']:
                break
        
        agent_proc.join(timeout=5)
        bot_proc.join(timeout=5)
        
        if agent_proc.is_alive():
            agent_proc.terminate()
        if bot_proc.is_alive():
            bot_proc.terminate()
        
        return {
            'steps': shared['agent']['steps'],
            'success': shared['success'],
            'collided': shared['collided']
        }