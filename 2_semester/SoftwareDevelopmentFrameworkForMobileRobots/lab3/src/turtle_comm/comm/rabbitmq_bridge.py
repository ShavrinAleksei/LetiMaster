import json
import threading
import pika
from collections import defaultdict


class RabbitMQManager:
    def __init__(self, host='localhost', exchange='turtlesim'):
        self.host = host
        self.exchange = exchange
        self.connection = None
        self.channel = None
        self._connect_publisher()

    def _connect_publisher(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='topic', durable=False)

    def publish(self, routing_key, message_dict):
        if self.channel is None or self.channel.is_closed:
            self._connect_publisher()
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=json.dumps(message_dict),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()


class ConsumerThread(threading.Thread):
    """Поток для приёма сообщений с динамическим добавлением подписок (не зависит от Qt)"""
    def __init__(self, host='localhost', exchange='turtlesim'):
        super().__init__()
        self.daemon = True   # чтобы поток завершался при выходе из основного процесса
        self.host = host
        self.exchange = exchange
        self._stop = False
        self._callbacks = defaultdict(list)  # routing_key -> list of callbacks
        self._bound_keys = set()             # routing keys already bound
        self._channel = None
        self._queue_name = None
        self._connection = None

        self.ready = threading.Event()

    def add_subscription(self, routing_key, callback):
        if callback not in self._callbacks[routing_key]:
            self._callbacks[routing_key].append(callback)
        if self._channel and self._queue_name and routing_key not in self._bound_keys:
            self._channel.queue_bind(
                exchange=self.exchange,
                queue=self._queue_name,
                routing_key=routing_key
            )
            self._bound_keys.add(routing_key)

    def run(self):
        print("ConsumerThread started")
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self.exchange, exchange_type='topic', durable=False)
        result = self._channel.queue_declare(queue='', exclusive=True, auto_delete=True)
        self._queue_name = result.method.queue

        for rk in self._callbacks:
            self._channel.queue_bind(exchange=self.exchange, queue=self._queue_name, routing_key=rk)
            self._bound_keys.add(rk)

        self.ready.set()

        def on_message(ch, method, properties, body):
            if self._stop:
                ch.stop_consuming()
                return
            routing_key = method.routing_key
            callbacks = self._callbacks.get(routing_key)
            if callbacks:
                try:
                    data = json.loads(body.decode())
                except Exception:
                    data = {}
                for cb in callbacks:
                    try:
                        cb(routing_key, data)
                    except Exception as e:
                        print(f"Error in callback for {routing_key}: {e}")

        self._channel.basic_consume(queue=self._queue_name, on_message_callback=on_message, auto_ack=True)
        try:
            self._channel.start_consuming()
        except Exception as e:
            pass
        finally:
            if self._connection and self._connection.is_open:
                self._connection.close()

    def stop(self):
        self._stop = True
        if self._channel and self._channel.is_open:
            self._channel.stop_consuming()