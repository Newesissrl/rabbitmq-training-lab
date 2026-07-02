#!/usr/bin/env python3
import pika
import time
import random

# =============================================================================
# RABBITMQ CONNECTION SETUP
# =============================================================================
# Create connection to RabbitMQ server running on localhost:5672
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# Create a channel for AMQP operations
channel = connection.channel()

# =============================================================================
# EXCHANGE DECLARATION
# =============================================================================
# Declare a FANOUT exchange for broadcasting messages to ALL bound queues
# Fanout exchanges ignore routing keys and send copies to every bound queue
channel.exchange_declare(exchange='notifications', exchange_type='fanout')

# =============================================================================
# BROADCAST MESSAGE TEMPLATES
# =============================================================================
# These messages will be sent to ALL consumers connected to the fanout exchange
# Perfect for system-wide announcements and notifications
messages = [
    'System maintenance scheduled for tonight',
    'New feature released: Dark mode',
    'Security update available',
    'Server restart in 5 minutes'
]

print(' [*] Broadcasting messages every 4 seconds. To exit press CTRL+C')

# =============================================================================
# CONTINUOUS BROADCAST LOOP
# =============================================================================
try:
    counter = 1
    while True:
        # Select a random broadcast message
        message = random.choice(messages)
        # Add counter for message tracking
        full_message = f"{message} #{counter}"
        
        # Publish to fanout exchange
        # routing_key is ignored by fanout exchanges (can be empty)
        # Message will be copied to ALL queues bound to this exchange
        channel.basic_publish(
            exchange='notifications',   # Fanout exchange name
            routing_key='',            # Ignored by fanout exchange
            body=full_message          # Message content
        )
        print(f" [x] Broadcast: {full_message}")
        
        counter += 1
        time.sleep(4)  # Wait 4 seconds between broadcasts
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    # Clean up connection
    connection.close()