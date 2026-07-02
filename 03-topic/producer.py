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
# Declare a TOPIC exchange for pattern-based message routing
# Topic exchanges route based on wildcard patterns (* and #) in routing keys
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

# =============================================================================
# HIERARCHICAL ROUTING KEY MESSAGE TEMPLATES
# =============================================================================
# Topic exchange routing keys use dot-separated words (e.g., "user.login.success")
# Consumers can bind with wildcard patterns:
# * matches exactly one word
# # matches zero or more words
messages = [
    ('user.login.success', 'User john@example.com logged in'),        # Matches: user.#, *.login.*, user.login.success
    ('user.logout.info', 'User jane@example.com logged out'),         # Matches: user.#, *.logout.*, user.logout.info
    ('user.register.success', 'New user registered'),                 # Matches: user.#, *.register.*, user.register.success
    ('system.error', 'Disk space critical on server-01'),             # Matches: *.error, system.*, system.error
    ('system.memory.warning', 'Memory usage high on server-02'),      # Matches: system.*, *.warning, system.memory.warning
    ('app.error', 'Payment failed for order #12345'),                 # Matches: *.error, app.*, app.error
    ('app.payment.success', 'Payment processed for order #12346'),    # Matches: app.#, *.payment.*, app.payment.success
    ('database.connection.error', 'Cannot connect to primary database') # Matches: #.error, database.#, *.connection.*
]

print(' [*] Sending messages every 2 seconds. To exit press CTRL+C')

# =============================================================================
# TOPIC-BASED MESSAGE PUBLISHING LOOP
# =============================================================================
try:
    counter = 1
    while True:
        # Select random message with its hierarchical routing key
        routing_key, message = random.choice(messages)
        # Add counter for message tracking
        full_message = f"{message} #{counter}"
        
        # Publish to topic exchange with hierarchical routing key
        # Consumers bound with matching patterns will receive this message
        channel.basic_publish(
            exchange='topic_logs',      # Topic exchange name
            routing_key=routing_key,    # Hierarchical routing key (e.g., "user.login.success")
            body=full_message           # Message content
        )
        print(f" [x] Sent [{routing_key}] {full_message}")
        
        counter += 1
        time.sleep(2)  # Wait 2 seconds between messages
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    # Clean up connection
    connection.close()