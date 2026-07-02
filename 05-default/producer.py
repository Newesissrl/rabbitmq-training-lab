#!/usr/bin/env python3
import pika
import sys

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================
# Default exchange requires queue name and message as arguments
if len(sys.argv) < 3:
    print("Usage: python producer.py <queue_name> <message>")
    print("Example: python producer.py task_queue 'Hello World'")
    sys.exit(1)

queue_name = sys.argv[1]  # Target queue name
message = sys.argv[2]     # Message to send

# =============================================================================
# RABBITMQ CONNECTION SETUP
# =============================================================================
# Create connection to RabbitMQ server running on localhost:5672
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# Create a channel for AMQP operations
channel = connection.channel()

# =============================================================================
# QUEUE DECLARATION
# =============================================================================
# Declare the target queue (creates if doesn't exist)
# durable=True ensures queue survives RabbitMQ server restarts
channel.queue_declare(queue=queue_name, durable=True)

# =============================================================================
# PUBLISH TO DEFAULT EXCHANGE
# =============================================================================
# Send message to default exchange (empty string "")
# Default exchange routes messages where routing_key equals queue name
channel.basic_publish(
    exchange='',                                        # Default exchange (empty string)
    routing_key=queue_name,                            # Must match target queue name exactly
    body=message,                                      # Message content
    properties=pika.BasicProperties(delivery_mode=2)   # Make message persistent
)

print(f" [x] Sent '{message}' to queue '{queue_name}'")
# Clean up connection
connection.close()