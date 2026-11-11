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
# DEAD LETTER EXCHANGE AND QUEUE SETUP
# =============================================================================
# Declare the same dead letter infrastructure as producer
# Dead letter exchange handles messages that cannot be processed
channel.exchange_declare(exchange='dlx', exchange_type='direct')
# Queue to collect failed/expired messages
channel.queue_declare(queue='dead_letters', durable=True)
# Bind dead letter queue to DLX
channel.queue_bind(exchange='dlx', queue='dead_letters', routing_key='failed')

# =============================================================================
# MAIN PROCESSING QUEUE WITH DLX CONFIGURATION
# =============================================================================
# Declare main queue with dead letter exchange configuration
channel.queue_declare(
    queue='main_queue',
    durable=True,  # RabbitMQ 4.3: named shared queues must be durable
    arguments={
        'x-dead-letter-exchange': 'dlx',        # Route failed messages to DLX
        'x-dead-letter-routing-key': 'failed',  # Routing key for dead letters
        'x-message-ttl': 10000                   # 10 seconds TTL - messages expire if not consumed
    }
)

print(' [*] Waiting for messages. To exit press CTRL+C')
print(' [*] Will reject messages containing "rejected"')
print(' [*] Messages will expire after 10 seconds if not processed')

# =============================================================================
# MAIN QUEUE MESSAGE PROCESSING CALLBACK
# =============================================================================
def process_main_queue(ch, method, properties, body):
    """Process messages from main processing queue"""
    message = body.decode()
    print(f" [x] Main queue received: {message}")
    
    # Simulate processing failure for certain messages
    # Messages containing "rejected" will be sent to dead letter queue
    if 'rejected' in message.lower():
        print(f" [!] Rejecting message: {message}")
        # NACK with requeue=False sends message to dead letter exchange
        # This simulates a processing failure that shouldn't be retried
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    else:
        print(f" [✓] Processing message: {message}")
        # Simulate processing time
        time.sleep(1)
        # Acknowledge successful processing
        ch.basic_ack(delivery_tag=method.delivery_tag)

# =============================================================================
# DEAD LETTER QUEUE MESSAGE PROCESSING CALLBACK
# =============================================================================
def process_dead_letters(ch, method, properties, body):
    """Process messages that ended up in dead letter queue"""
    message = body.decode()
    # Dead letter messages contain additional headers with failure information
    headers = properties.headers or {}
    print(f" [💀] Dead letter received: {message}")
    print(f"     Headers: {headers}")
    print(f"     Reason: Message was rejected or expired")
    # Acknowledge dead letter processing
    ch.basic_ack(delivery_tag=method.delivery_tag)

# =============================================================================
# DUAL QUEUE CONSUMPTION SETUP
# =============================================================================
# Set up consumption from both main processing queue and dead letter queue
# This allows monitoring of both successful processing and failed messages

# Consume from main processing queue
# Messages here are either processed successfully or rejected to DLX
channel.basic_consume(queue='main_queue', on_message_callback=process_main_queue)

# Consume from dead letter queue
# Messages here have either been rejected or expired due to TTL
channel.basic_consume(queue='dead_letters', on_message_callback=process_dead_letters)

print(' [*] Monitoring both main_queue and dead_letters queue')
print(' [*] Dead letter scenarios:')
print(' [*]   1. Messages containing "rejected" will be NACKed')
print(' [*]   2. Messages not consumed within 10 seconds will expire')
print(' [*]   3. Both scenarios route messages to dead_letters queue')

# =============================================================================
# START CONSUMING FROM BOTH QUEUES
# =============================================================================
# Start consuming from both queues simultaneously
# This demonstrates monitoring both normal processing and error handling
channel.start_consuming()