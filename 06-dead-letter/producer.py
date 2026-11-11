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
# DEAD LETTER EXCHANGE SETUP
# =============================================================================
# Declare dead letter exchange for handling failed/expired messages
# Messages that can't be processed will be routed here
channel.exchange_declare(exchange='dlx', exchange_type='direct')

# Declare dead letter queue to collect failed messages
channel.queue_declare(queue='dead_letters', durable=True)
# Bind dead letter queue to DLX with routing key 'failed'
channel.queue_bind(exchange='dlx', queue='dead_letters', routing_key='failed')

# =============================================================================
# MAIN QUEUE WITH DEAD LETTER CONFIGURATION
# =============================================================================
# Declare main processing queue with dead letter exchange configuration
channel.queue_declare(
    queue='main_queue',
    durable=True,  # RabbitMQ 4.3: named shared queues must be durable
    arguments={
        'x-dead-letter-exchange': 'dlx',        # Send failed messages to DLX
        'x-dead-letter-routing-key': 'failed',  # Routing key for dead letters
        'x-message-ttl': 10000                   # 10 seconds TTL - messages expire if not consumed
    }
)

# =============================================================================
# TEST MESSAGES FOR DEAD LETTER SCENARIOS
# =============================================================================
# Different messages to demonstrate various dead letter scenarios
messages = [
    'Message 1 - will be processed',           # Normal processing
    'Message 2 - will be rejected',            # Will be rejected by consumer
    'Message 3 - will expire if not consumed', # Will expire due to TTL
    'Message 4 - normal processing'            # Normal processing
]

# Send test messages to main queue
for i, message in enumerate(messages, 1):
    channel.basic_publish(
        exchange='',                                # Default exchange
        routing_key='main_queue',                  # Main processing queue
        body=message,                              # Message content
        properties=pika.BasicProperties(
            delivery_mode=2,                       # Make message persistent
            message_id=str(i)                      # Unique message ID for tracking
        )
    )
    print(f" [x] Sent: {message}")

# =============================================================================
# DEAD LETTER SCENARIOS EXPLANATION
# =============================================================================
print("\nMessages sent. Dead letter scenarios:")
print(" - Messages expire in 10 seconds if not consumed (TTL)")
print(" - Messages containing 'rejected' will be rejected by consumer")
print(" - Failed messages will be routed to dead_letters queue")
print(" - Check Web UI to observe message movement")

# Clean up connection
connection.close()