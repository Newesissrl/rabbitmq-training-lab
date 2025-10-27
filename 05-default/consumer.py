#!/usr/bin/env python3
import pika
import sys
import time

if len(sys.argv) < 2:
    print("Usage: python consumer.py <queue_name>")
    print("Example: python consumer.py task_queue")
    sys.exit(1)

queue_name = sys.argv[1]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare queue (creates if doesn't exist)
channel.queue_declare(queue=queue_name, durable=True)

print(f' [*] Waiting for messages from queue "{queue_name}". To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] Received: {body.decode()}")
    # Simulate work
    time.sleep(1)
    print(" [x] Done processing")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Fair dispatch - don't give more than one message to a worker at a time
channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()