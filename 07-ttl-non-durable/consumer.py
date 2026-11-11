#!/usr/bin/env python3
import pika
import time

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
# Declare the same exchange and queue as the producer (arguments must match)
channel.exchange_declare(
    exchange='ttl_exchange',
    exchange_type='direct',
    durable=True
)

# Temporary queue: durable=True is required by RabbitMQ 4.3 for queues shared
# between connections; auto_delete=True removes the queue as soon as the last
# consumer unsubscribes.
channel.queue_declare(
    queue='ttl_queue',
    durable=True,
    auto_delete=True    # Deleted when the last consumer disconnects
)

# Bind temporary queue to the exchange (routing key 'temp_data')
channel.queue_bind(
    exchange='ttl_exchange',
    queue='ttl_queue',
    routing_key='temp_data'
)

print(' [*] Consuming messages before they expire (TTL=5s)')
print(' [*] Messages expire after 5 seconds if not consumed')
print(' [*] Queue will auto-delete when consumer stops. To exit press CTRL+C')
print(' [*] Start this consumer AFTER starting producer to catch messages before expiry')

# =============================================================================
# TTL MESSAGE PROCESSING CALLBACK
# =============================================================================
def callback(ch, method, properties, body):
    """Process temporary messages before they expire"""
    message = body.decode()
    print(f" [x] Received: {message}")
    
    # Simulate processing time (1 second - less than 5 second TTL)
    # This ensures we process messages before they expire
    # In real scenarios, processing time should be well under TTL
    time.sleep(1)
    
    print(f" [✓] Processed: {message}")
    # Acknowledge message processing completion
    ch.basic_ack(delivery_tag=method.delivery_tag)

# =============================================================================
# CONSUMER CONFIGURATION
# =============================================================================
# Configure fair dispatch - only one unacknowledged message per consumer
# This ensures even processing load if multiple consumers are used
channel.basic_qos(prefetch_count=1)

# Set up consumption from temporary queue
channel.basic_consume(
    queue='ttl_queue',              # Temporary, auto-delete queue
    on_message_callback=callback    # Message processing function
)

print(' [*] Consumer ready - processing temporary messages')
print(' [*] Experiment: Start producer first, then start this consumer')
print(' [*] Observe: Messages sent before consumer starts will expire and be lost')

# =============================================================================
# START CONSUMING TEMPORARY MESSAGES
# =============================================================================
try:
    # Start consuming messages from temporary queue
    # Only messages that haven't expired will be processed
    channel.start_consuming()
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    # Gracefully stop consuming
    channel.stop_consuming()
    connection.close()
    print(' [!] Consumer stopped - ttl_queue will auto-delete')
    print(' [!] Any unprocessed messages with remaining TTL are lost')
    print(' [!] Messages published while no queue exists are dropped (unroutable)')