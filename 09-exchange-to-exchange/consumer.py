#!/usr/bin/env python3
import pika
import sys
import time

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================
# Consumer must specify which processing path to handle
if len(sys.argv) < 2:
    print("Usage: python consumer.py [temp|archive]")
    print("  temp    - Fast processing from non-durable queue")
    print("  archive - Reliable processing from durable queue")
    print("")
    print("Both consumers receive IDENTICAL messages due to exchange-to-exchange binding")
    sys.exit(1)

consumer_type = sys.argv[1]

# =============================================================================
# RABBITMQ CONNECTION SETUP
# =============================================================================
# Create connection to RabbitMQ server running on localhost:5672
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# Create a channel for AMQP operations
channel = connection.channel()

# =============================================================================
# PROCESSING PATH CONFIGURATION
# =============================================================================
if consumer_type == 'temp':
    # =============================================================================
    # FAST PROCESSING PATH SETUP
    # =============================================================================
    # Configure for speed-optimized, temporary processing
    queue_name = 'temp_queue'
    exchange_name = 'temp_exchange'
    
    # Declare non-durable components for fast processing
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=False)
    channel.queue_declare(queue=queue_name, durable=False)
    channel.queue_bind(exchange=exchange_name, queue=queue_name)
    
    print(' [*] TEMP CONSUMER - Fast processing from non-durable queue')
    print(' [*] Optimized for speed and real-time processing')
    print(' [*] This consumer and queue will be LOST on server restart')
    
elif consumer_type == 'archive':
    # =============================================================================
    # RELIABLE STORAGE PATH SETUP
    # =============================================================================
    # Configure for reliability-optimized, persistent processing
    queue_name = 'archive_queue'
    exchange_name = 'archive_exchange'
    
    # Declare durable components for reliable processing
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=True)
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange=exchange_name, queue=queue_name)
    
    print(' [*] ARCHIVE CONSUMER - Reliable processing from durable queue')
    print(' [*] Optimized for reliability and data persistence')
    print(' [*] This consumer and queue will SURVIVE server restart')
    
else:
    print("Invalid consumer type. Use 'temp' or 'archive'")
    sys.exit(1)

print(f' [*] Waiting for messages from {queue_name}. To exit press CTRL+C')
print(' [*] Both consumers receive IDENTICAL messages via exchange-to-exchange binding')

# =============================================================================
# DUAL-PATH MESSAGE PROCESSING CALLBACK
# =============================================================================
def callback(ch, method, properties, body):
    """Process messages according to the selected processing path"""
    message = body.decode()
    
    if consumer_type == 'temp':
        # =============================================================================
        # FAST PROCESSING PATH
        # =============================================================================
        # Optimized for speed - minimal processing time
        # Suitable for real-time alerts, notifications, cache updates
        print(f" [⚡] TEMP processed: {message}")
        time.sleep(0.1)  # Fast processing (100ms)
        
    elif consumer_type == 'archive':
        # =============================================================================
        # RELIABLE PROCESSING PATH
        # =============================================================================
        # Optimized for reliability - thorough processing and storage
        # Suitable for audit logs, compliance records, analytics
        print(f" [💾] ARCHIVE stored: {message}")
        time.sleep(1)    # Slower, more thorough processing (1 second)
        
    # Acknowledge message processing completion
    ch.basic_ack(delivery_tag=method.delivery_tag)

# =============================================================================
# CONSUMER CONFIGURATION AND STARTUP
# =============================================================================
# Configure fair dispatch for even message distribution
channel.basic_qos(prefetch_count=1)
# Set up message consumption from the selected processing path
channel.basic_consume(queue=queue_name, on_message_callback=callback)

print(f' [*] Processing path: {consumer_type.upper()}')
print(' [*] Messages are duplicated automatically via exchange-to-exchange binding')

# =============================================================================
# START CONSUMING MESSAGES
# =============================================================================
try:
    # Start consuming messages from the selected processing path
    channel.start_consuming()
except KeyboardInterrupt:
    print(f'\n [!] {consumer_type.upper()} consumer interrupted')
    # Gracefully stop consuming
    channel.stop_consuming()

# =============================================================================
# CLEANUP AND SUMMARY
# =============================================================================
# Close connection
connection.close()

# Provide path-specific information about durability
if consumer_type == 'temp':
    print(' [!] TEMP consumer stopped - queue will be lost on server restart')
    print(' [!] Fast processing path optimized for speed over reliability')
elif consumer_type == 'archive':
    print(' [!] ARCHIVE consumer stopped - queue and messages will survive restart')
    print(' [!] Reliable processing path optimized for data persistence')