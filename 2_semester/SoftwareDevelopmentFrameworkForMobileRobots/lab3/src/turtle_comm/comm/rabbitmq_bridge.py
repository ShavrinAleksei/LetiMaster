import json
import threading
import pika

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
        self._callbacks = {}
        self._channel = None
        self._queue_name = None
        self._connection = None

    def add_subscription(self, routing_key, callback):
        self._callbacks[routing_key] = callback
        if self._channel and self._queue_name:
            self._channel.queue_bind(
                exchange=self.exchange,
                queue=self._queue_name,
                routing_key=routing_key
            )

    def run(self):
        print("ConsumerThread started")
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self.exchange, exchange_type='topic', durable=False)
        result = self._channel.queue_declare(queue='', exclusive=True, auto_delete=True)
        self._queue_name = result.method.queue
        print(f"ConsumerThread: queue created {self._queue_name}")

        for rk in self._callbacks:
            self._channel.queue_bind(exchange=self.exchange, queue=self._queue_name, routing_key=rk)
            print(f"ConsumerThread: bound {rk}")

        def on_message(ch, method, properties, body):
            print(f"ConsumerThread: got message on {method.routing_key}")
            if self._stop:
                ch.stop_consuming()
                return
            routing_key = method.routing_key
            cb = self._callbacks.get(routing_key)
            if cb:
                try:
                    data = json.loads(body.decode())
                except Exception:
                    data = {}
                cb(routing_key, data)

        self._channel.basic_consume(queue=self._queue_name, on_message_callback=on_message, auto_ack=True)
        print("ConsumerThread: starting consume")
        try:
            self._channel.start_consuming()
        except Exception as e:
            print(f"ConsumerThread: exception {e}")
            pass
        finally:
            if self._connection and self._connection.is_open:
                self._connection.close()

    def stop(self):
        self._stop = True
        if self._channel and self._channel.is_open:
            self._channel.stop_consuming()
        