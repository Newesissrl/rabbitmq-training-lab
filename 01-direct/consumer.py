#!/usr/bin/env python3
import pika
import sys

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================
# Consumer must specify which type of messages to receive (error, info, warning)
if len(sys.argv) < 2:
    print("Usage: python consumer.py [error|info|warning]")
    sys.exit(1)

# The routing key this consumer is interested in
severity = sys.argv[1]

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
# Declare the same direct exchange that the producer uses
# This ensures the exchange exists before we try to bind to it
channel.exchange_declare(exchange='logs_direct', exchange_type='direct')

# =============================================================================
# QUEUE CREATION AND BINDING
# =============================================================================
# Create an exclusive, auto-delete queue with a random name
# exclusive=True means only this connection can use this queue
# When connection closes, queue is automatically deleted
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# Bind this queue to the exchange with the specified routing key
# Only messages with matching routing key will be delivered to this queue
channel.queue_bind(exchange='logs_direct', queue=queue_name, routing_key=severity)

print(f' [*] Waiting for {severity} messages. To exit press CTRL+C')

# =============================================================================
# MESSAGE PROCESSING CALLBACK
# =============================================================================
def callback(ch, method, properties, body):
    """Process received messages that match our routing key"""
    # method.routing_key shows the routing key of the received message
    # body.decode() converts message bytes to string
    print(f" [x] Received [{method.routing_key}] {body.decode()}")

# =============================================================================
# START CONSUMING MESSAGES
# =============================================================================
# Set up automatic message consumption from our bound queue
# auto_ack=True means messages are automatically acknowledged (no manual ack needed)
# Only messages matching our routing key will be delivered to this consumer
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

# Start the consuming loop - this blocks and waits for messages
channel.start_consuming()