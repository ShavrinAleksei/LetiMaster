import sys
import time
import logging
import subprocess
import random
from typing import List, Dict
from turtle_comm.comm import RabbitMQManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StalkerChainManager:
    def __init__(self, host: str = 'localhost', speed: float = 0.9):
        self.host = host
        self.speed = speed
        self.manager: RabbitMQManager | None = None
        self.processes: List[subprocess.Popen] = []
        self.spawned_count = 0
        self.expected_count = 0
        self.running = True
        self.victim_map: Dict[str, str] = {} 

    def start(self, num_followers: int, victim_turtle: str) -> None:
        self.expected_count = num_followers
        self.victim = victim_turtle

        stalker_names = [f"stalker_turtle{i}" for i in range(1, num_followers + 1)]
        victims = [victim_turtle] + stalker_names[:-1]
        for name, target in zip(stalker_names, victims):
            self.victim_map[name] = target
            logger.info(f"Mapping: {name} -> {target}")

        self.manager = RabbitMQManager(host=self.host)
        self.manager.connect()
        self.manager.start_consuming()

        self.manager.subscribe_json("/spawned", self.on_spawned)
        time.sleep(0.5)

        for i in range(1, num_followers + 1):
            name = f"stalker_turtle{i}"
            spawn_msg = {
                'name': name,
                'x': random.uniform(1.0, 11 - 1),   
                'y': random.uniform(1.0, 11 - 1),
                'theta': 0.0
            }
            self.manager.publish_json("/spawn", spawn_msg)
            logger.info(f"Published spawn request for {name}")

        logger.info(f"Waiting for {num_followers} spawn confirmations...")
        while self.spawned_count < self.expected_count and self.running:
            time.sleep(0.1)

        if self.running:
            logger.info("All stalkers spawned and running. Press Ctrl+C to stop.")
            while self.running:
                time.sleep(1)

    def on_spawned(self, routing_key: str, data: dict) -> None:
        name = data.get('name')
        success = data.get('success', False)
        if success and name and name.startswith('stalker_turtle'):
            target = self.victim_map[name]
            logger.info(f"Spawn confirmed for {name} (following {target}), launching node...")
            cmd = [
                sys.executable, '-m', 'stalker',
                '--name', name,
                '--victim', target,
                '--speed', str(self.speed),
                '--host', self.host
            ]
            try:
                proc = subprocess.Popen(cmd)
                self.processes.append(proc)
                self.spawned_count += 1
            except Exception as e:
                logger.error(f"Failed to launch {name}: {e}")

    def stop(self) -> None:
        logger.info("Stopping StalkerChainManager...")
        self.running = False

        for proc in self.processes:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

        if self.manager:
            self.manager.close()

        logger.info("Stopped.")

