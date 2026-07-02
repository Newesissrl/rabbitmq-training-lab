#!/usr/bin/env python3
import pika
import sys

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================
# Consumer must specify a wildcard pattern for topic exchange binding
if len(sys.argv) < 2:
    print("Usage: python consumer.py <binding_pattern>")
    print("Examples:")
    print("  python consumer.py '*.error'      # All error messages")
    print("  python consumer.py 'user.#'       # All user-related messages")
    print("  python consumer.py 'system.*.*'   # System messages with 3 parts")
    sys.exit(1)

# The wildcard pattern this consumer will bind with
binding_pattern = sys.argv[1]

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
# Declare the same topic exchange that the producer uses
# Topic exchanges route based on pattern matching with wildcards
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

# =============================================================================
# QUEUE CREATION AND PATTERN BINDING
# =============================================================================
# Create exclusive, auto-delete queue with random name
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# Bind queue to exchange with wildcard pattern
# Only messages with routing keys matching this pattern will be delivered
# * matches exactly one word, # matches zero or more words
channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key=binding_pattern)

print(f' [*] Waiting for messages matching "{binding_pattern}". To exit press CTRL+C')

# =============================================================================
# PATTERN-MATCHED MESSAGE PROCESSING
# =============================================================================
def callback(ch, method, properties, body):
    """Process messages that match our wildcard binding pattern"""
    # method.routing_key shows the actual routing key that matched our pattern
    # This demonstrates how topic exchanges route based on pattern matching
    print(f" [x] Received [{method.routing_key}] {body.decode()}")

# =============================================================================
# START CONSUMING PATTERN-MATCHED MESSAGES
# =============================================================================
# Set up consumption from queue bound with wildcard pattern
# Only messages with routing keys matching our pattern will be delivered
# auto_ack=True for automatic message acknowledgment
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

# Start consuming loop - receives only messages matching our pattern
channel.start_consuming()