#!/usr/bin/env python3
import pika
import sys
import time

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================
# Consumer must specify which named queue to consume from
if len(sys.argv) < 2:
    print("Usage: python consumer.py <queue_name>")
    print("Example: python consumer.py task_queue")
    sys.exit(1)

queue_name = sys.argv[1]  # Queue name to consume from

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
# Declare the same queue that producer sends to (creates if doesn't exist)
# durable=True ensures queue survives RabbitMQ server restarts
channel.queue_declare(queue=queue_name, durable=True)

print(f' [*] Waiting for messages from queue "{queue_name}". To exit press CTRL+C')

# =============================================================================
# MESSAGE PROCESSING CALLBACK
# =============================================================================
def callback(ch, method, properties, body):
    """Process messages from the named queue"""
    print(f" [x] Received: {body.decode()}")
    # Simulate work processing
    time.sleep(1)
    print(" [x] Done processing")
    # Acknowledge message processing completion
    ch.basic_ack(delivery_tag=method.delivery_tag)

# =============================================================================
# CONSUMER CONFIGURATION
# =============================================================================
# Configure fair dispatch - only one unacknowledged message per consumer
# This ensures even work distribution among multiple consumers
channel.basic_qos(prefetch_count=1)

# =============================================================================
# START CONSUMING FROM NAMED QUEUE
# =============================================================================
# Set up consumption from the specific named queue
# Messages sent to default exchange with matching routing_key will be received
channel.basic_consume(queue=queue_name, on_message_callback=callback)

# Start consuming loop - blocks waiting for messages
channel.start_consuming()