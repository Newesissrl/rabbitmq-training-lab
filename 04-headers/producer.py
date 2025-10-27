#!/usr/bin/env python3
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare headers exchange
channel.exchange_declare(exchange='headers_exchange', exchange_type='headers')

# Message templates
messages = [
    ({'type': 'error', 'source': 'database'}, 'Database connection timeout'),
    ({'type': 'error', 'source': 'api'}, 'API rate limit exceeded'),
    ({'type': 'info', 'source': 'database'}, 'Database backup completed'),
    ({'type': 'warning', 'source': 'api', 'priority': 'high'}, 'API response time degraded'),
    ({'environment': 'production', 'service': 'payment'}, 'Payment service restarted'),
    ({'environment': 'staging', 'service': 'user'}, 'User service deployed')
]

print(' [*] Sending messages every 3 seconds. To exit press CTRL+C')

try:
    counter = 1
    while True:
        headers, message = random.choice(messages)
        full_message = f"{message} #{counter}"
        
        channel.basic_publish(
            exchange='headers_exchange',
            routing_key='',  # Ignored in headers exchange
            body=full_message,
            properties=pika.BasicProperties(headers=headers)
        )
        print(f" [x] Sent with headers {headers}: {full_message}")
        
        counter += 1
        time.sleep(3)
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    connection.close()