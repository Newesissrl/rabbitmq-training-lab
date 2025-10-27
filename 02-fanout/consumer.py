#!/usr/bin/env python3
import pika
import uuid

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare exchange
channel.exchange_declare(exchange='notifications', exchange_type='fanout')

# Create exclusive queue with unique name
consumer_id = str(uuid.uuid4())[:8]
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# Bind queue to exchange
channel.queue_bind(exchange='notifications', queue=queue_name)

print(f' [*] Consumer {consumer_id} waiting for notifications. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(f" [x] Consumer {consumer_id} received: {body.decode()}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()