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
# NON-DURABLE EXCHANGE DECLARATION
# =============================================================================
# Declare a NON-DURABLE, auto-delete exchange for temporary messaging
# This exchange will be lost when RabbitMQ server restarts
channel.exchange_declare(
    exchange='temp_exchange',
    exchange_type='direct',
    durable=False,      # Non-durable - won't survive server restart
    auto_delete=True    # Auto-delete when no queues bound
)

# =============================================================================
# TEMPORARY MESSAGE TEMPLATES
# =============================================================================
# Messages representing temporary, ephemeral data with short lifespans
messages = [
    'Temporary session data for user #{}',    # Session data that expires
    'Cache entry expires soon #{}',           # Cache invalidation message
    'Real-time notification #{}',             # Time-sensitive notification
    'Ephemeral status update #{}',            # Temporary status change
    'Short-lived event data #{}'              # Event data with short relevance
]

print(' [*] Sending messages with 5-second TTL every 2 seconds')
print(' [*] Messages will expire if not consumed! To exit press CTRL+C')

# =============================================================================
# TTL MESSAGE PUBLISHING LOOP
# =============================================================================
try:
    counter = 1
    while True:
        # Select random temporary message template
        message_template = random.choice(messages)
        message = message_template.format(counter)
        
        # Send message with TTL (Time-To-Live) expiration
        channel.basic_publish(
            exchange='temp_exchange',               # Non-durable exchange
            routing_key='temp_data',               # Routing key for temporary data
            body=message,                          # Message content
            properties=pika.BasicProperties(
                expiration='5000',                 # 5 seconds TTL - message expires if not consumed
                delivery_mode=1                    # Non-persistent message (faster, less reliable)
            )
        )
        print(f" [x] Sent (TTL=5s): {message}")
        
        counter += 1
        time.sleep(2)  # Send every 2 seconds (faster than TTL to demonstrate expiration)
        
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    # Clean up connection
    connection.close()