import time
import os

os.environ.setdefault('CYCLONEDDS_INTERFACE', 'lo0')

from dds_interface import DDSInterface
from dds_models import Spawn


class SpawnNode:
    def __init__(self):
        self.dds = DDSInterface()
        self.spawn_pub = self.dds.create_publisher("/spawn", Spawn)
        self.spawned = []

    def spawn_turtle(self, name: str, x: float, y: float, theta: float = 0.0):
        msg = Spawn()
        msg.name = name
        msg.x = x
        msg.y = y
        msg.theta = theta

        self.dds.publish(self.spawn_pub, msg)
        self.spawned.append(name)
        return True

    def spawn_chain(self, count: int, start_x: float = -2.0, step: float = -2.0):
        for i in range(2, count + 1):
            print("spawn ", i)
            name = f"turtle{i}"
            x = start_x + (i - 2) * step
            self.spawn_turtle(name, x, 0.0, 0.0)

            time.sleep(0.1)

        return len(self.spawned)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--chain', type=int, default=3, help='Количество черепашек')
    parser.add_argument('--start-x', type=float, default=-2.0)
    parser.add_argument('--step', type=float, default=-2.0)
    args = parser.parse_args()

    spawner = SpawnNode()
    spawner.spawn_chain(args.chain, args.start_x, args.step)
    time.sleep(1)


if __name__ == '__main__':
    main()