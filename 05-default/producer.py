#!/usr/bin/env python3
import pika
import sys

if len(sys.argv) < 3:
    print("Usage: python producer.py <queue_name> <message>")
    print("Example: python producer.py task_queue 'Hello World'")
    sys.exit(1)

queue_name = sys.argv[1]
message = sys.argv[2]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare queue (creates if doesn't exist)
channel.queue_declare(queue=queue_name, durable=True)

# Send to default exchange (empty string)
channel.basic_publish(
    exchange='',  # Default exchange
    routing_key=queue_name,  # Must match queue name
    body=message,
    properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
)

print(f" [x] Sent '{message}' to queue '{queue_name}'")
connection.close()