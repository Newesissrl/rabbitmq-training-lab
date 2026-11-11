#!/usr/bin/env python3
import pika
import time
import random

# =============================================================================
# RABBITMQ CONNECTION SETUP
# =============================================================================
# Create connection to RabbitMQ server running on localhost:5672
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# Create a channel for AMQP operations
channel = connection.channel()

print(' [*] Creating exchange-to-exchange binding setup...')

# =============================================================================
# DUAL EXCHANGE ARCHITECTURE SETUP
# =============================================================================
# Create the source exchange that producers publish to.
# Live (real-time) consumers attach their own temporary queues to it.
channel.exchange_declare(
    exchange='live_exchange',
    exchange_type='fanout',         # Broadcast to all bound destinations
    durable=True
)

# Create DURABLE target exchange for reliable, persistent storage
# This exchange prioritizes reliability over speed
channel.exchange_declare(
    exchange='archive_exchange', 
    exchange_type='fanout',         # Broadcast to all bound destinations
    durable=True                    # Durable - survives server restarts
)

# =============================================================================
# EXCHANGE-TO-EXCHANGE BINDING
# =============================================================================
# Bind live_exchange TO archive_exchange for automatic message duplication
# Messages published to live_exchange are automatically copied to archive_exchange
channel.exchange_bind(
    destination='archive_exchange', # Target exchange (where copies go)
    source='live_exchange',         # Source exchange (where messages are published)
    routing_key=''                  # Empty routing key for fanout exchanges
)

print(' [✓] Created exchange-to-exchange binding: live_exchange → archive_exchange')

# =============================================================================
# ARCHIVE QUEUE SETUP
# =============================================================================
# Reliable storage queue - durable, so messages accumulate even when no
# archive consumer is running and survive a broker restart.
channel.queue_declare(queue='archive_queue', durable=True)
channel.queue_bind(exchange='archive_exchange', queue='archive_queue')

# The LIVE path has no queue declared here: each live consumer creates its own
# exclusive, server-named queue (see consumer.py). RabbitMQ 4.3 does not allow
# non-durable shared queues, and an exclusive queue is the right tool for
# "only while I'm connected" consumption.

print(' [✓] Created archive_queue and bindings')

# =============================================================================
# BUSINESS EVENT MESSAGE TEMPLATES
# =============================================================================
# Messages representing typical business events that need both fast and reliable processing
messages = [
    'Order #12345 processed',           # E-commerce order processing
    'User login: john@example.com',     # User authentication event
    'Payment completed: $99.99',        # Financial transaction
    'Inventory updated: Product ABC',   # Inventory management
    'System alert: High CPU usage',     # System monitoring alert
    'Data backup completed',            # System maintenance event
    'Security scan finished',           # Security monitoring
    'Report generated: Monthly sales'   # Business reporting
]

print(' [*] Sending messages every 3 seconds to live_exchange')
print(' [*] Messages go to every live consumer AND are copied to archive_queue')
print(' [*] To exit press CTRL+C')

# =============================================================================
# CONTINUOUS MESSAGE PUBLISHING WITH AUTOMATIC DUPLICATION
# =============================================================================
try:
    counter = 1
    while True:
        # Select random business event message
        message_template = random.choice(messages)
        message = f"{message_template} #{counter}"
        
        # Publish ONLY to live_exchange (source exchange)
        # Exchange-to-exchange binding automatically copies to archive_exchange
        channel.basic_publish(
            exchange='live_exchange',               # Source exchange only
            routing_key='',                        # Empty for fanout exchange
            body=message,                          # Business event message
            properties=pika.BasicProperties(
                delivery_mode=2                    # Persistent message for reliability
            )
        )
        
        print(f" [x] Sent to live_exchange (auto-copied to archive): {message}")
        counter += 1
        time.sleep(3)  # Wait 3 seconds between messages
        
except KeyboardInterrupt:
    print('\n [!] Interrupted')

# =============================================================================
# EXCHANGE-TO-EXCHANGE BINDING DEMONSTRATION SUMMARY
# =============================================================================
print('\n' + '='*70)
print(' [!] EXCHANGE-TO-EXCHANGE BINDING DEMO:')
print(' [!] 1. Messages sent ONLY to live_exchange (source)')
print(' [!] 2. Automatically copied to archive_exchange via binding')
print(' [!] 3. Live consumers and archive_queue receive identical messages')
print(' [!] 4. Run consumers to see dual processing paths:')
print(' [!]    - live consumer: exclusive queue, only while connected')
print(' [!]    - archive consumer: durable queue, nothing is missed')
print(' [!] 5. Test durability: restart RabbitMQ and see what survives')
print('='*70)

# Clean up connection
connection.close()