#!/usr/bin/env python3
import pika
import sys

if len(sys.argv) < 2:
    print("Usage: python consumer.py [error|info|warning]")
    sys.exit(1)

severity = sys.argv[1]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare exchange
channel.exchange_declare(exchange='logs_direct', exchange_type='direct')

# Create exclusive queue
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# Bind queue to exchange with routing key
channel.queue_bind(exchange='logs_direct', queue=queue_name, routing_key=severity)

print(f' [*] Waiting for {severity} messages. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] Received [{method.routing_key}] {body.decode()}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()