#!/usr/bin/env python3
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare dead letter exchange
channel.exchange_declare(exchange='dlx', exchange_type='direct') # test also adding durable=True

# Declare dead letter queue
channel.queue_declare(queue='dead_letters') # test also adding durable=True
channel.queue_bind(exchange='dlx', queue='dead_letters', routing_key='failed')

# Declare main queue with DLX configuration
channel.queue_declare(
    queue='main_queue',
    arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'failed',
        'x-message-ttl': 10000  # 10 seconds TTL
    }
)

# Send messages
messages = [
    'Message 1 - will be processed',
    'Message 2 - will be rejected',
    'Message 3 - will expire if not consumed',
    'Message 4 - normal processing'
]

for i, message in enumerate(messages, 1):
    channel.basic_publish(
        exchange='',
        routing_key='main_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Persistent
            message_id=str(i)
        )
    )
    print(f" [x] Sent: {message}")

print("\nMessages sent. Some will expire in 10 seconds if not consumed.")
connection.close()