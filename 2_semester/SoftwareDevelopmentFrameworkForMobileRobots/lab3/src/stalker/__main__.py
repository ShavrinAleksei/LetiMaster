import sys
import time
import signal
import argparse
from turtle_comm.comm import RabbitMQManager
from stalker.chain_manager import StalkerChainManager

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--victim-turtle', type=str, default='turtle1')
    parser.add_argument('--num-followers', type=int, default=2)
    parser.add_argument('--speed', type=float, default=0.9)
    parser.add_argument('--host', type=str, default='localhost')
    args = parser.parse_args()

    rabbit = RabbitMQManager(host=args.host)
    manager = StalkerChainManager(rabbit, args.victim_turtle, args.speed)
    manager.start(args.num_followers)

    def shutdown(signum, frame):
        print("\nShutting down followers...")
        manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"Waiting for spawn confirmations...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == '__main__':
    main()