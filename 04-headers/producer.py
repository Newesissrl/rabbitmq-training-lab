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
# Declare a HEADERS exchange for routing based on message headers (not routing keys)
# Headers exchanges route messages based on header key-value pairs
channel.exchange_declare(exchange='headers_exchange', exchange_type='headers')

# =============================================================================
# HEADER-BASED MESSAGE TEMPLATES
# =============================================================================
# Headers exchange routes based on message headers, not routing keys
# Each message has headers that consumers can match against using x-match rules
messages = [
    # Messages with type and source headers
    ({'type': 'error', 'source': 'database'}, 'Database connection timeout'),
    ({'type': 'error', 'source': 'api'}, 'API rate limit exceeded'),
    ({'type': 'info', 'source': 'database'}, 'Database backup completed'),
    # Message with multiple headers including priority
    ({'type': 'warning', 'source': 'api', 'priority': 'high'}, 'API response time degraded'),
    # Messages with environment and service headers
    ({'environment': 'production', 'service': 'payment'}, 'Payment service restarted'),
    ({'environment': 'staging', 'service': 'user'}, 'User service deployed')
]

print(' [*] Sending messages every 3 seconds. To exit press CTRL+C')

# =============================================================================
# HEADER-BASED MESSAGE PUBLISHING LOOP
# =============================================================================
try:
    counter = 1
    while True:
        # Select random message with its header set
        headers, message = random.choice(messages)
        # Add counter for message tracking
        full_message = f"{message} #{counter}"
        
        # Publish to headers exchange with message headers
        # Routing is based on headers, not routing_key (which is ignored)
        channel.basic_publish(
            exchange='headers_exchange',                    # Headers exchange name
            routing_key='',                                # Ignored by headers exchange
            body=full_message,                             # Message content
            properties=pika.BasicProperties(headers=headers) # Headers for routing
        )
        print(f" [x] Sent with headers {headers}: {full_message}")
        
        counter += 1
        time.sleep(3)  # Wait 3 seconds between messages
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    # Clean up connection
    connection.close()