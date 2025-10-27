#!/usr/bin/env python3
import pika
import time
import thread6

def single_connection_test():
    """Test using single connection for all operations"""
    print("=== Single Connection Test ===")

    # Single connection for all operations
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare queue
    queue_name = 'single_conn_test'
    channel.queue_declare(queue=queue_name, durable=True)

    # Send messages
    start_time = time.time()
    message_count = 100 # test with 10000 200000

    for i in range(message_count):
        message = f"Message {i}"
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )

    # Consume messages
    messages_received = []

    def callback(ch, method, properties, body):
        messages_received.append(body.decode())
        ch.basic_ack(delivery_tag=method.delivery_tag)
        if len(messages_received) >= message_count:
            ch.stop_consuming()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()

    end_time = time.time()

    connection.close()

    print(f"Messages sent/received: {len(messages_received)}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Throughput: {len(messages_received) / (end_time - start_time):.2f} msg/sec")
    print(f"Connections used: 1")
    print(f"Channels used: 1")

if __name__ == "__main__":
    single_connection_test()