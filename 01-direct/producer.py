#!/usr/bin/env python3
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare direct exchange
channel.exchange_declare(exchange='logs_direct', exchange_type='direct')

# Message templates
messages = [
    ('error', 'Database connection failed'),
    ('info', 'User logged in successfully'),
    ('warning', 'Disk space running low'),
    ('error', 'Payment processing error'),
    ('info', 'System backup completed')
]

print(' [*] Sending messages every 3 seconds. To exit press CTRL+C')

try:
    counter = 1
    while True:
        routing_key, message = random.choice(messages)
        full_message = f"{message} #{counter}"
        
        channel.basic_publish(
            exchange='logs_direct',
            routing_key=routing_key,
            body=full_message
        )
        print(f" [x] Sent [{routing_key}] {full_message}")
        
        counter += 1
        time.sleep(3)
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    connection.close()