import sys
import signal
import argparse
from stalker_chain.chain_manager import StalkerChainManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--victim-turtle', type=str, default='turtle1')
    parser.add_argument('--num-followers', type=int, default=2)
    parser.add_argument('--speed', type=float, default=0.9)
    parser.add_argument('--host', type=str, default='localhost')
    args = parser.parse_args()

    manager = StalkerChainManager(host=args.host, speed=args.speed)

    def shutdown(sig, frame):
        logger.info("Received shutdown signal")
        manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        manager.start(args.num_followers, args.victim_turtle)
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == '__main__':
    main()