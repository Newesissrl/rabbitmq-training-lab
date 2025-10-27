#!/usr/bin/env python3
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare non-durable, auto-delete exchange
channel.exchange_declare(
    exchange='temp_exchange',
    exchange_type='direct',
    durable=False,      # Non-durable - won't survive server restart
    auto_delete=True    # Auto-delete when no queues bound
)

# Message templates for temporary data
messages = [
    'Temporary session data for user #{}',
    'Cache entry expires soon #{}',
    'Real-time notification #{}',
    'Ephemeral status update #{}',
    'Short-lived event data #{}'
]

print(' [*] Sending messages with 5-second TTL every 2 seconds')
print(' [*] Messages will expire if not consumed! To exit press CTRL+C')

try:
    counter = 1
    while True:
        message_template = random.choice(messages)
        message = message_template.format(counter)
        
        # Send message with TTL
        channel.basic_publish(
            exchange='temp_exchange',
            routing_key='temp_data',
            body=message,
            properties=pika.BasicProperties(
                expiration='5000',  # 5 seconds TTL
                delivery_mode=1     # Non-persistent message
            )
        )
        print(f" [x] Sent (TTL=5s): {message}")
        
        counter += 1
        time.sleep(2)  # Send every 2 seconds
        
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    connection.close()