#!/usr/bin/env python3
import pika
import sys

if len(sys.argv) < 2:
    print("Usage: python consumer.py <binding_pattern>")
    print("Examples:")
    print("  python consumer.py '*.error'")
    print("  python consumer.py 'user.#'")
    print("  python consumer.py 'system.*.*'")
    sys.exit(1)

binding_pattern = sys.argv[1]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare exchange
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

# Create exclusive queue
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# Bind queue with pattern
channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key=binding_pattern)

print(f' [*] Waiting for messages matching "{binding_pattern}". To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] Received [{method.routing_key}] {body.decode()}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()