#!/usr/bin/env python3
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare exchange
channel.exchange_declare(exchange='headers_exchange', exchange_type='headers')

# Create queues with different header bindings
queues = [
    ('database_queue', {'x-match': 'any', 'source': 'database'}),
    ('production_queue', {'x-match': 'all', 'environment': 'production', 'service': 'payment'}),
    ('staging_queue', {'x-match': 'any', 'environment': 'staging'})
]

for queue_name, binding_args in queues:
    channel.queue_declare(queue=queue_name)
    channel.queue_bind(
        exchange='headers_exchange',
        queue=queue_name,
        arguments=binding_args
    )
    print(f"Created queue '{queue_name}' with binding: {binding_args}")

def callback(ch, method, properties, body):
    headers = properties.headers or {}
    print(f" [x] Queue '{method.consumer_tag}' received: {body.decode()}")
    print(f"     Headers: {headers}")

# Consume from all queues
for queue_name, _ in queues:
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=True,
        consumer_tag=queue_name
    )

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()