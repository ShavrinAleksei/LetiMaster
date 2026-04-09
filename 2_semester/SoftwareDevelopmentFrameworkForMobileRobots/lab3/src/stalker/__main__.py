import sys
import signal
import argparse
from stalker.node import StalkerNode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--victim', required=True)
    parser.add_argument('--speed', type=float, default=0.9)
    parser.add_argument('--host', default='localhost')
    args = parser.parse_args()

    node = StalkerNode(args.name, args.victim, args.speed, args.host)

    def shutdown(sig, frame):
        logger.info("Shutting down stalker node")
        node.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    node.run()

if __name__ == '__main__':
    main()