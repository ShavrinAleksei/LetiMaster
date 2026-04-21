import subprocess
import time
import sys
import signal
import argparse


class TurtleLauncher:
    def __init__(self):
        self.processes = []

    def stop_all(self):
        for p in self.processes:
            if p.poll() is None:
                try:
                    p.terminate()
                    time.sleep(0.5)
                    if p.poll() is None:
                        p.kill()
                except:
                    pass

    def start_turtlesim(self):
        proc = subprocess.Popen([sys.executable, 'turtlesim.py'])
        self.processes.append(proc)
        time.sleep(2)

        if proc.poll() is not None:
            print("Симулятор не запустился")
            return False

        print("Все ок")
        return True

    def spawn_turtles(self, count):
        if count <= 1:
            return True
        proc = subprocess.Popen([sys.executable, 'spawn_node.py','--chain', str(count)])
        self.processes.append(proc)

        #proc.wait()
       # print("bee")
        time.sleep(2)
        return True

    def start_teleop(self):
        proc = subprocess.Popen([sys.executable, 'teleop_key.py', '--turtle', 'turtle1'])
        self.processes.append(proc)
        time.sleep(1)
        return True

    def start_stalkers(self, count, speed):
        if count <= 1:
            return True

        for i in range(2, count + 1):
            stalker = f"turtle{i}"
            victim = f"turtle{i - 1}"

            proc = subprocess.Popen([
                sys.executable, 'stalker_node.py',
                '--stalker', stalker,
                '--victim', victim,
                '--speed', str(speed)
            ])
            self.processes.append(proc)
            time.sleep(0.5)

        return True


    def run(self, num_turtles=3, speed=1.5):
        def signal_handler(sig, frame):
            self.stop_all()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        if not self.start_turtlesim():
            self.stop_all()
            return

        if not self.spawn_turtles(num_turtles):
            self.stop_all()
            return


        self.start_teleop()
        self.start_stalkers(num_turtles, speed)

        try:
            for proc in self.processes:
                proc.wait()
        except KeyboardInterrupt:
            self.stop_all()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-turtles', type=int, default=3)
    parser.add_argument('--speed', type=float, default=1.5)

    args = parser.parse_args()

    launcher = TurtleLauncher()
    launcher.run(args.num_turtles, args.speed)


if __name__ == '__main__':
    main()