import numpy as np
from map_utils import load_map
from simulator import Simulator
import multiprocessing as mp
from result_utils import save_results


def run_experiment(p_values, agent_configs, train_episodes=300, eval_episodes=100, max_steps=1000):
    grid, shape, starts, goals, spawn_points = load_map('citymap.txt')
    results = {}
    for p in p_values:
        env = Simulator(grid, agent_configs, spawn_points, p, max_steps=max_steps)
        env.start_agent()

        strategies = [cfg['strategy'] for cfg in agent_configs]
        if any(s in ('sarsa', 'q_learning') for s in strategies):
            for ep in range(train_episodes):
                eps = max(0.02, 0.3 * (1.0 - ep / train_episodes))
                epsilons = [eps if s in ('sarsa','q_learning') else 0.0 for s in strategies]
                env.run_episode(epsilons=epsilons)

        successes = 0
        steps_list = []
        for _ in range(eval_episodes):
            epsilons = [0.0 if s in ('sarsa','q_learning') else None for s in strategies]
            success, steps = env.run_episode(epsilons=epsilons)
            if success:
                successes += 1
                steps_list.append(steps)

        env.stop_agent()

        avg_steps = np.mean(steps_list) if steps_list else float('nan')
        success_rate = successes / eval_episodes
        results[p] = (avg_steps, success_rate)
        label = f"{len(agent_configs)} агента(ов), стратегия {strategies[0]}"
        if len(set(strategies)) > 1:
            label += ' (смеш.)'
        print(f"[{label}] p={p:.3f} | success rate={success_rate:.3f} | avg steps={avg_steps:.1f}")

    return results


if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    grid, shape, starts, goals, spawn_points = load_map('citymap.txt')
    
    BOT_SPAWN_PROBS = [0.01, 0.03, 0.05]
    STRATEGIES = ['bot_like', 'sarsa', 'q_learning']
    AGENTS_CONFIG = {
        0: {'start': starts[0], 'goal': goals[0]},
        1: {'start': starts[1], 'goal': goals[0]},
        2: {'start': starts[2], 'goal': goals[0]},
    }

    print("\n===== 1 АГЕНТ =====")
    results_1 = {}
    for strat in STRATEGIES:
        print(f"\nСтратегия: {strat}")
        cfg = [{'start': AGENTS_CONFIG[0]['start'], 'goal': AGENTS_CONFIG[0]['goal'], 'strategy': strat}]
        results_1[strat] = run_experiment(BOT_SPAWN_PROBS, cfg, train_episodes=300, eval_episodes=200, max_steps=800)
    save_results(results_1, 'results_1agent.pkl')

    print("\n===== 2 АГЕНТА =====")
    results_2 = {}
    for strat in STRATEGIES:
        print(f"\nСтратегия обоих агентов: {strat}")
        cfg = [
            {'start': AGENTS_CONFIG[0]['start'], 'goal': AGENTS_CONFIG[0]['goal'], 'strategy': strat},
            {'start': AGENTS_CONFIG[1]['start'], 'goal': AGENTS_CONFIG[1]['goal'], 'strategy': strat}
        ]
        # Для RL-стратегий увеличено число эпизодов и max_steps
        results_2[strat] = run_experiment(BOT_SPAWN_PROBS, cfg, train_episodes=1300, eval_episodes=200, max_steps=1000)
    save_results(results_2, 'results_2agent.pkl')    
    
    print("\n===== 3 АГЕНТА =====")
    results_3 = {}
    for strat in STRATEGIES:
        print(f"\nСтратегия: {strat}")
        cfg = [
            {'start': AGENTS_CONFIG[0]['start'], 'goal': AGENTS_CONFIG[0]['goal'], 'strategy': strat},
            {'start': AGENTS_CONFIG[1]['start'], 'goal': AGENTS_CONFIG[1]['goal'], 'strategy': strat},
            {'start': AGENTS_CONFIG[2]['start'], 'goal': AGENTS_CONFIG[2]['goal'], 'strategy': strat}
        ]
        # Для RL-стратегий увеличено число эпизодов и max_steps
        results_3[strat] = run_experiment(BOT_SPAWN_PROBS, cfg, train_episodes=2000, eval_episodes=200, max_steps=1200)
    save_results(results_3, 'results_3agent.pkl')