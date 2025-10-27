#!/usr/bin/env python3
import pika
import time
import threading

def worker_with_own_connection(worker_id, message_count):
    """Each worker creates its own connection"""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    queue_name = 'multi_conn_test'
    channel.queue_declare(queue=queue_name, durable=True)

    # Send messages
    for i in range(message_count):
        message = f"Worker-{worker_id} Message {i}"
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )

    connection.close()
    print(f"Worker {worker_id} completed sending {message_count} messages")

def multiple_connections_test():
    """Test using multiple connections (one per thread)"""
    print("=== Multiple Connections Test ===")

    start_time = time.time()
    worker_count = 5
    messages_per_worker = 2 #test with 20000 and 40000

    # Create threads with separate connections
    threads = []
    for i in range(worker_count):
        thread = threading.Thread(
            target=worker_with_own_connection,
            args=(i, messages_per_worker)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Consume all messages with separate connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    queue_name = 'multi_conn_test'
    messages_received = []

    def callback(ch, method, properties, body):
        messages_received.append(body.decode())
        ch.basic_ack(delivery_tag=method.delivery_tag)
        if len(messages_received) >= worker_count * messages_per_worker:
            ch.stop_consuming()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()

    connection.close()

    end_time = time.time()

    print(f"Messages sent/received: {len(messages_received)}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Throughput: {len(messages_received) / (end_time - start_time):.2f} msg/sec")
    print(f"Connections used: {worker_count + 1} (one per worker + consumer)")
    print(f"Channels used: {worker_count + 1}")

if __name__ == "__main__":
    multiple_connections_test()