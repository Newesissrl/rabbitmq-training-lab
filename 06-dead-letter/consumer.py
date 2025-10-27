#!/usr/bin/env python3
import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare queues (same as producer)
channel.exchange_declare(exchange='dlx', exchange_type='direct') # test also adding durable=True
channel.queue_declare(queue='dead_letters') # test also adding durable=True
channel.queue_bind(exchange='dlx', queue='dead_letters', routing_key='failed')

channel.queue_declare(
    queue='main_queue',
    arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'failed',
        'x-message-ttl': 10000
    }
)

print(' [*] Waiting for messages. To exit press CTRL+C')
print(' [*] Will reject messages containing "rejected"')

def process_main_queue(ch, method, properties, body):
    message = body.decode()
    print(f" [x] Main queue received: {message}")
    
    # Simulate processing failure for certain messages
    if 'rejected' in message.lower():
        print(f" [!] Rejecting message: {message}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    else:
        print(f" [✓] Processing message: {message}")
        time.sleep(1)
        ch.basic_ack(delivery_tag=method.delivery_tag)

def process_dead_letters(ch, method, properties, body):
    message = body.decode()
    headers = properties.headers or {}
    print(f" [💀] Dead letter received: {message}")
    print(f"     Headers: {headers}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Consume from both queues
channel.basic_consume(queue='main_queue', on_message_callback=process_main_queue)
channel.basic_consume(queue='dead_letters', on_message_callback=process_dead_letters)

channel.start_consuming()