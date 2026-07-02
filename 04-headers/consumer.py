#!/usr/bin/env python3
import pika

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
# Declare the same headers exchange that the producer uses
# Headers exchanges route based on message headers, not routing keys
channel.exchange_declare(exchange='headers_exchange', exchange_type='headers')

# =============================================================================
# QUEUE CREATION WITH HEADER BINDING RULES
# =============================================================================
# Define queues with different header matching rules
# x-match: 'all' means ALL specified headers must match
# x-match: 'any' means AT LEAST ONE specified header must match
queues = [
    # Queue that receives messages where type='error' (must match exactly)
    ('error_queue', {'x-match': 'all', 'type': 'error'}),
    # Queue that receives messages where source='database' (any match)
    ('database_queue', {'x-match': 'any', 'source': 'database'}),
    # Queue that receives messages where BOTH environment='production' AND service='payment'
    ('production_queue', {'x-match': 'all', 'environment': 'production', 'service': 'payment'})
]

# Create and bind each queue with its header matching rules
for queue_name, binding_args in queues:
    # Create named queue (not exclusive, persists between connections)
    channel.queue_declare(queue=queue_name)
    # Bind queue to headers exchange with header matching arguments
    channel.queue_bind(
        exchange='headers_exchange',
        queue=queue_name,
        arguments=binding_args  # Header matching rules
    )
    print(f"Created queue '{queue_name}' with binding: {binding_args}")

# =============================================================================
# HEADER-MATCHED MESSAGE PROCESSING
# =============================================================================
def callback(ch, method, properties, body):
    """Process messages that matched header binding rules"""
    # Extract headers from message properties (empty dict if no headers)
    headers = properties.headers or {}
    # method.consumer_tag identifies which queue received this message
    print(f" [x] Queue '{method.consumer_tag}' received: {body.decode()}")
    print(f"     Headers: {headers}")

# =============================================================================
# SETUP CONSUMPTION FROM ALL HEADER-BOUND QUEUES
# =============================================================================
# Set up consumers for all queues with different header matching rules
# Each queue will only receive messages whose headers match its binding rules
for queue_name, _ in queues:
    channel.basic_consume(
        queue=queue_name,           # Queue name
        on_message_callback=callback, # Callback function
        auto_ack=True,              # Automatic acknowledgment
        consumer_tag=queue_name     # Tag to identify which queue in callback
    )

print(' [*] Waiting for messages. To exit press CTRL+C')
print(' [*] Messages will be routed based on header matching rules:')
print(' [*]   error_queue: type=error (all match)')
print(' [*]   database_queue: source=database (any match)')
print(' [*]   production_queue: environment=production AND service=payment (all match)')

# =============================================================================
# START CONSUMING HEADER-MATCHED MESSAGES
# =============================================================================
# Start consuming from all queues simultaneously
# Each message will be delivered to queues whose header rules match
channel.start_consuming()