#!/usr/bin/env python3
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare topic exchange
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

# Message templates
messages = [
    ('user.login.success', 'User john@example.com logged in'),
    ('user.created', 'User john@example.com created'),
    ('user.logout.info', 'User jane@example.com logged out'),
    ('user.register.success', 'New user registered'),
    ('system.error', 'Disk space critical on server-01'),
    ('system.memory.warning', 'Memory usage high on server-02'),
    ('system.memory.error', 'OOM kill on server-02'),
    ('app.error', 'Payment failed for order #12345'),
    ('app.payment.success', 'Payment processed for order #12346'),
    ('database.connection.error', 'Cannot connect to primary database'),
    ('database.error', 'Cannot connect to primary database'),
    ('database.login.warning', 'User is unauthorized'),
    ('system.cpu.error', 'CPU usage high on server-02')

]

print(' [*] Sending messages every 2 seconds. To exit press CTRL+C')

try:
    counter = 1
    while True:
        routing_key, message = random.choice(messages)
        full_message = f"{message} #{counter}"
        
        channel.basic_publish(
            exchange='topic_logs',
            routing_key=routing_key,
            body=full_message
        )
        print(f" [x] Sent [{routing_key}] {full_message}")
        
        counter += 1
        time.sleep(2)
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    connection.close()