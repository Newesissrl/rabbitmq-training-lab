#!/usr/bin/env python3
import pika
import time
import random

# =============================================================================
# RABBITMQ CONNECTION SETUP
# =============================================================================
# Create connection to RabbitMQ server running on localhost:5672
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# Create a channel for AMQP operations (declare, publish, consume)
channel = connection.channel()

# =============================================================================
# EXCHANGE DECLARATION
# =============================================================================
# Declare a DIRECT exchange for routing messages based on exact routing key matches
# Direct exchanges route messages to queues where routing key exactly matches binding key
channel.exchange_declare(exchange='logs_direct', exchange_type='direct')

# =============================================================================
# MESSAGE TEMPLATES WITH ROUTING KEYS
# =============================================================================
# Each message has a routing key that determines which consumer receives it
# Direct exchange routes based on EXACT match between routing key and binding key
messages = [
    ('error', 'Database connection failed'),      # Goes to consumers bound with 'error'
    ('info', 'User logged in successfully'),      # Goes to consumers bound with 'info'
    ('warning', 'Disk space running low'),        # Goes to consumers bound with 'warning'
    ('error', 'Payment processing error'),        # Goes to consumers bound with 'error'
    ('info', 'System backup completed')           # Goes to consumers bound with 'info'
]

print(' [*] Sending messages every 3 seconds. To exit press CTRL+C')

# =============================================================================
# CONTINUOUS MESSAGE PUBLISHING LOOP
# =============================================================================
try:
    counter = 1
    while True:
        # Randomly select a message template with its routing key
        routing_key, message = random.choice(messages)
        # Add counter to make each message unique for tracking
        full_message = f"{message} #{counter}"
        
        # Publish message to the direct exchange
        # The routing_key determines which bound queues receive this message
        channel.basic_publish(
            exchange='logs_direct',     # Name of the direct exchange
            routing_key=routing_key,    # Key used for routing (error/info/warning)
            body=full_message           # The actual message content
        )
        print(f" [x] Sent [{routing_key}] {full_message}")
        
        counter += 1
        time.sleep(3)  # Wait 3 seconds between messages
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    # Clean up connection when interrupted
    connection.close()