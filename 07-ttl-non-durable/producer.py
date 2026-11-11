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
# EXCHANGE AND TEMPORARY QUEUE DECLARATION
# =============================================================================
# Exchange used for short-lived data.
channel.exchange_declare(
    exchange='ttl_exchange',
    exchange_type='direct',
    durable=True
)

# Temporary queue for ephemeral data.
# RabbitMQ 4.3 no longer accepts non-durable (transient) queues that are shared
# between connections. The supported ways to get a "temporary" queue are:
#   - exclusive=True       -> deleted when the declaring connection closes
#   - auto_delete=True     -> deleted when its last consumer unsubscribes
#   - x-expires argument   -> deleted after N ms without consumers/usage
# Here we use auto_delete so the queue survives until a consumer has attached
# and then goes away when that consumer stops.
# The producer declares it too, so messages accumulate (and expire) even
# before any consumer is started.
channel.queue_declare(
    queue='ttl_queue',
    durable=True,
    auto_delete=True
)
channel.queue_bind(exchange='ttl_exchange', queue='ttl_queue', routing_key='temp_data')

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

        # Send message with per-message TTL (Time-To-Live)
        channel.basic_publish(
            exchange='ttl_exchange',               # Exchange for temporary data
            routing_key='temp_data',               # Routing key for temporary data
            body=message,                          # Message content
            properties=pika.BasicProperties(
                expiration='5000',                 # 5 seconds TTL - message expires if not consumed
                delivery_mode=1                    # Non-persistent message (faster, lost on restart)
            )
        )
        print(f" [x] Sent (TTL=5s): {message}")

        counter += 1
        time.sleep(2)  # Send every 2 seconds (faster than TTL to demonstrate expiration)

except KeyboardInterrupt:
    print('\n [!] Interrupted')
    # Clean up connection
    connection.close()
