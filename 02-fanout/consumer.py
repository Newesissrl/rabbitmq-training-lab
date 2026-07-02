#!/usr/bin/env python3
import pika
import uuid

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
# Declare the same fanout exchange that the producer uses
# Fanout exchanges broadcast to ALL bound queues regardless of routing key
channel.exchange_declare(exchange='notifications', exchange_type='fanout')

# =============================================================================
# UNIQUE CONSUMER SETUP
# =============================================================================
# Generate unique consumer ID for identification in logs
consumer_id = str(uuid.uuid4())[:8]
# Create exclusive, auto-delete queue with random name
# Each consumer gets its own queue to receive ALL broadcast messages
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# =============================================================================
# QUEUE BINDING TO FANOUT EXCHANGE
# =============================================================================
# Bind this consumer's queue to the fanout exchange
# No routing key needed - fanout sends to ALL bound queues
channel.queue_bind(exchange='notifications', queue=queue_name)

print(f' [*] Consumer {consumer_id} waiting for notifications. To exit press CTRL+C')

# =============================================================================
# BROADCAST MESSAGE PROCESSING
# =============================================================================
def callback(ch, method, properties, body):
    """Process broadcast messages received from fanout exchange"""
    # Every consumer receives EVERY message from fanout exchange
    # This demonstrates pub/sub pattern where all subscribers get all messages
    print(f" [x] Consumer {consumer_id} received: {body.decode()}")

# =============================================================================
# START CONSUMING BROADCAST MESSAGES
# =============================================================================
# Set up automatic consumption from this consumer's exclusive queue
# auto_ack=True for simplicity (messages auto-acknowledged)
# This consumer will receive ALL messages broadcast to the fanout exchange
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

# Start consuming loop - blocks waiting for broadcast messages
channel.start_consuming()