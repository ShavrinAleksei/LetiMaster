# rabbitmq_manager.py
import threading
import queue
import pika
import json
import logging
import time
from typing import Dict, Callable, Optional

logger = logging.getLogger(__name__)

class RabbitMQManager:
    def __init__(self, host: str = 'localhost', exchange: str = 'amq.topic'):
        self.host = host
        self.exchange = exchange

        self._pub_connection: Optional[pika.BlockingConnection] = None
        self._pub_channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._consume_connection: Optional[pika.BlockingConnection] = None
        self._consume_channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        
        self._pub_lock = threading.Lock()
        self._running = False
        self._consume_thread: Optional[threading.Thread] = None
        self._command_queue = queue.Queue()
        self._subscriptions: Dict[str, Callable] = {}
        self._queue_name: Optional[str] = None

    def connect(self) -> None:
        self._pub_connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
        self._pub_channel = self._pub_connection.channel()

        self._consume_connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
        self._consume_channel = self._consume_connection.channel()
        result = self._consume_channel.queue_declare(queue='', exclusive=True)
        self._queue_name = result.method.queue
        logger.info(f"Connected to RabbitMQ, consumer queue: {self._queue_name}")

    def start_consuming(self) -> None:
        if self._running:
            return
        self._running = True
        self._consume_thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._consume_thread.start()

    def _consume_loop(self) -> None:
        self._consume_channel.basic_consume(
            queue=self._queue_name,
            on_message_callback=self._on_message,
            auto_ack=True
        )
        while self._running:
            try:
                cmd = self._command_queue.get_nowait()
                if cmd[0] == 'subscribe':
                    _, routing_key, callback = cmd
                    self._do_subscribe(routing_key, callback)
                elif cmd[0] == 'unsubscribe':
                    _, routing_key = cmd
                    self._do_unsubscribe(routing_key)
            except queue.Empty:
                pass
            try:
                self._consume_channel.connection.process_data_events(time_limit=0.1)
            except Exception as e:
                logger.error(f"Consume loop error: {e}")
                if self._running:
                    self._reconnect_consumer()
                break
        self._cleanup_consumer()

    def _on_message(self, ch, method, properties, body: bytes) -> None:
        routing_key = method.routing_key
        callback = self._subscriptions.get(routing_key)
        if callback:
            try:
                callback(routing_key, body)
            except Exception as e:
                logger.error(f"Callback error for {routing_key}: {e}")

    def subscribe(self, routing_key: str, callback: Callable[[str, bytes], None]) -> None:
        self._command_queue.put(('subscribe', routing_key, callback))

    def _do_subscribe(self, routing_key: str, callback: Callable) -> None:
        if routing_key in self._subscriptions:
            return
        self._consume_channel.queue_bind(
            exchange=self.exchange,
            queue=self._queue_name,
            routing_key=routing_key
        )
        self._subscriptions[routing_key] = callback
        logger.info(f"Subscribed to {routing_key}")

    def _do_unsubscribe(self, routing_key: str) -> None:
        if routing_key not in self._subscriptions:
            return
        self._consume_channel.queue_unbind(
            exchange=self.exchange,
            queue=self._queue_name,
            routing_key=routing_key
        )
        del self._subscriptions[routing_key]

    def publish(self, routing_key: str, message: bytes) -> None:
        with self._pub_lock:
            self._ensure_pub_channel()
            self._pub_channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message
            )

    def publish_json(self, routing_key: str, data: dict) -> None:
        self.publish(routing_key, json.dumps(data).encode())

    def subscribe_json(self, routing_key: str, callback: Callable[[str, dict], None]) -> None:
        def wrapper(rk: str, body: bytes):
            try:
                data = json.loads(body.decode())
                callback(rk, data)
            except Exception as e:
                logger.error(f"JSON decode error: {e}")
        self.subscribe(routing_key, wrapper)

    def _ensure_pub_channel(self):
        if self._pub_channel and self._pub_channel.is_open:
            return
        if self._pub_connection and self._pub_connection.is_open:
            try:
                self._pub_channel = self._pub_connection.channel()
                logger.info("Recreated publisher channel")
                return
            except Exception as e:
                logger.error(f"Failed to recreate publisher channel: {e}")
        try:
            self._pub_connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
            self._pub_channel = self._pub_connection.channel()
            logger.info("Recreated publisher connection")
        except Exception as e:
            logger.error(f"Failed to recreate publisher connection: {e}")
            raise

    def _reconnect_consumer(self):
        logger.info("Reconnecting consumer...")
        self._cleanup_consumer()
        try:
            self._consume_connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
            self._consume_channel = self._consume_connection.channel()
            result = self._consume_channel.queue_declare(queue='', exclusive=True)
            self._queue_name = result.method.queue
            for rk, cb in self._subscriptions.items():
                self._consume_channel.queue_bind(
                    exchange=self.exchange,
                    queue=self._queue_name,
                    routing_key=rk
                )
            self._consume_channel.basic_consume(
                queue=self._queue_name,
                on_message_callback=self._on_message,
                auto_ack=True
            )
            logger.info("Consumer reconnected")
        except Exception as e:
            logger.error(f"Consumer reconnect failed: {e}")
            self._running = False

    def _cleanup_consumer(self):
        if self._consume_channel and self._consume_channel.is_open:
            try:
                self._consume_channel.close()
            except:
                pass
        if self._consume_connection and self._consume_connection.is_open:
            try:
                self._consume_connection.close()
            except:
                pass

    def close(self) -> None:
        self._running = False
        if self._consume_thread:
            self._consume_thread.join(timeout=2.0)
        self._cleanup_consumer()
        if self._pub_channel and self._pub_channel.is_open:
            try:
                self._pub_channel.close()
            except:
                pass
        if self._pub_connection and self._pub_connection.is_open:
            try:
                self._pub_connection.close()
            except:
                pass
        logger.info("RabbitMQManager closed")