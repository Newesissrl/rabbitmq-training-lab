#!/usr/bin/env python3
import pika
import time
import threading
from queue import Queue

class ConnectionPool:
    def __init__(self, max_connections=3):
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.lock = threading.Lock()

        # Pre-create connections
        for _ in range(max_connections):
            conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            self.connections.put(conn)

    def get_connection(self):
        """Get connection from pool"""
        return self.connections.get()

    def return_connection(self, connection):
        """Return connection to pool"""
        self.connections.put(connection)

    def close_all(self):
        """Close all connections in pool"""
        while not self.connections.empty():
            conn = self.connections.get()
            conn.close()

def worker_with_pooled_connection(worker_id, message_count, pool):
    """Worker using connection from pool with separate channel"""
    connection = pool.get_connection()

    try:
        # Each worker gets its own channel
        channel = connection.channel()

        queue_name = 'pool_conn_test'
        channel.queue_declare(queue=queue_name, durable=True)

        # Send messages
        for i in range(message_count):
            message = f"Pooled-Worker-{worker_id} Message {i}"
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )

        channel.close()
        print(f"Pooled Worker {worker_id} completed sending {message_count} messages")

    finally:
        # Return connection to pool
        pool.return_connection(connection)

def connection_pool_test():
    """Test using connection pool with channels"""
    print("=== Connection Pool Test ===")

    start_time = time.time()
    worker_count = 10
    messages_per_worker = 10 # test with 10000 and 20000

    # Create connection pool
    pool = ConnectionPool(max_connections=3)

    # Create threads using pooled connections
    threads = []
    for i in range(worker_count):
        thread = threading.Thread(
            target=worker_with_pooled_connection,
            args=(i, messages_per_worker, pool)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Consume all messages
    connection = pool.get_connection()
    channel = connection.channel()

    queue_name = 'pool_conn_test'
    messages_received = []

    def callback(ch, method, properties, body):
        messages_received.append(body.decode())
        ch.basic_ack(delivery_tag=method.delivery_tag)
        if len(messages_received) >= worker_count * messages_per_worker:
            ch.stop_consuming()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()

    channel.close()
    pool.return_connection(connection)

    end_time = time.time()

    # Cleanup
    pool.close_all()

    print(f"Messages sent/received: {len(messages_received)}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Throughput: {len(messages_received) / (end_time - start_time):.2f} msg/sec")
    print(f"Connections used: 3 (pooled)")
    print(f"Channels used: {worker_count + 1} (one per worker + consumer)")

if __name__ == "__main__":
    connection_pool_test()