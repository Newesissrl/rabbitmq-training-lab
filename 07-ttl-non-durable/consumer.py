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
# NON-DURABLE EXCHANGE DECLARATION
# =============================================================================
# Declare the same non-durable exchange that the producer uses
# This exchange will be lost when RabbitMQ server restarts
channel.exchange_declare(
    exchange='temp_exchange',
    exchange_type='direct',
    durable=False,      # Non-durable - exists only in memory
    auto_delete=True    # Auto-delete when no queues are bound
)

# =============================================================================
# TEMPORARY QUEUE DECLARATION
# =============================================================================
# Declare non-durable, auto-delete queue for temporary message processing
# This queue has a very short lifecycle - exists only while consumer is active
channel.queue_declare(
    queue='temp_queue',
    durable=False,      # Non-durable - won't survive server restart
    auto_delete=True,   # Auto-delete when consumer disconnects
    exclusive=False     # Allow multiple consumers (not exclusive to this connection)
)

# =============================================================================
# QUEUE BINDING FOR TEMPORARY DATA
# =============================================================================
# Bind temporary queue to temporary exchange
# This binding routes messages with 'temp_data' routing key to our queue
channel.queue_bind(
    exchange='temp_exchange',
    queue='temp_queue',
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
    queue='temp_queue',             # Temporary, auto-delete queue
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
    print(' [!] Consumer stopped - temp_queue will auto-delete')
    print(' [!] Any unprocessed messages with remaining TTL are lost')
    print(' [!] Temporary infrastructure cleaned up automatically')