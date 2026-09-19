import os
import threading
import time
from typing import Callable, Dict
from cyclonedds.domain import DomainParticipant
from cyclonedds.pub import DataWriter, Publisher
from cyclonedds.sub import DataReader, Subscriber
from cyclonedds.topic import Topic
from cyclonedds.core import Qos, Policy
from cyclonedds.util import duration

os.environ.setdefault('CYCLONEDDS_INTERFACE', 'lo0')


class DDSInterface:
    def __init__(self, domain_id: int = 0):
        self.participant = DomainParticipant(domain_id)
        self.callbacks: Dict[str, Callable] = {}
        self._running = True
        self._threads = []

    def create_publisher(self, topic_name: str, msg_type) -> DataWriter:
        qos = Qos(
            Policy.Reliability.Reliable(duration(microseconds=60)),
            Policy.Durability.TransientLocal,
            Policy.History.KeepLast(10)
        )
        topic = Topic(self.participant, topic_name, msg_type, qos=qos)
        publisher = Publisher(self.participant)
        writer = DataWriter(publisher, topic)
        return writer

    def create_subscriber(self, topic_name: str, msg_type, callback: Callable) -> DataReader:
        qos = Qos(
            Policy.Reliability.Reliable(duration(microseconds=60)),
            Policy.Durability.TransientLocal,
            Policy.History.KeepLast(10)
        )

        topic = Topic(self.participant, topic_name, msg_type, qos=qos)
        subscriber = Subscriber(self.participant)
        reader = DataReader(subscriber, topic)

        self.callbacks[topic_name] = callback
        self._start_reader_thread(reader, topic_name)
        return reader

    def publish(self, publisher: DataWriter, msg):
        publisher.write(msg)

    def _start_reader_thread(self, reader: DataReader, key: str):
        def read_loop():
            while self._running:
                try:
                    samples = reader.take()
                    for sample in samples:
                        callback = self.callbacks.get(key)
                        if not callback:
                            continue
                        callback(sample)
                except Exception as e:
                    print(f"Error in reader thread [{key}]: {e}")

                if not samples:
                    time.sleep(0.01)

        thread = threading.Thread(target=read_loop, daemon=True)
        thread.start()
        self._threads.append(thread)