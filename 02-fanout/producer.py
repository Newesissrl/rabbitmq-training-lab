#!/usr/bin/env python3
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare fanout exchange
channel.exchange_declare(exchange='notifications', exchange_type='fanout')

# Message templates
messages = [
    'System maintenance scheduled for tonight',
    'New feature released: Dark mode',
    'Security update available',
    'Server restart in 5 minutes'
]

print(' [*] Broadcasting messages every 4 seconds. To exit press CTRL+C')

try:
    counter = 1
    while True:
        message = random.choice(messages)
        full_message = f"{message} #{counter}"
        
        channel.basic_publish(
            exchange='notifications',
            routing_key='',  # Ignored in fanout
            body=full_message
        )
        print(f" [x] Broadcast: {full_message}")
        
        counter += 1
        time.sleep(4)
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    connection.close()