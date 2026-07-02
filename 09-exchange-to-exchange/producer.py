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
# Create NON-DURABLE source exchange for fast, temporary processing
# This exchange prioritizes speed over reliability
channel.exchange_declare(
    exchange='temp_exchange',
    exchange_type='fanout',         # Broadcast to all bound destinations
    durable=False                   # Non-durable - fast but lost on restart
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
# Bind temp_exchange TO archive_exchange for automatic message duplication
# Messages published to temp_exchange are automatically copied to archive_exchange
channel.exchange_bind(
    destination='archive_exchange', # Target exchange (where copies go)
    source='temp_exchange',         # Source exchange (where messages are published)
    routing_key=''                  # Empty routing key for fanout exchanges
)

print(' [✓] Created exchange-to-exchange binding: temp_exchange → archive_exchange')

# =============================================================================
# DUAL PROCESSING PATH QUEUE SETUP
# =============================================================================
# Create queues for both processing paths with different durability characteristics

# Fast processing queue - non-durable for speed
channel.queue_declare(queue='temp_queue', durable=False)    # Lost on restart, faster
# Reliable storage queue - durable for persistence
channel.queue_declare(queue='archive_queue', durable=True)  # Survives restart, slower

# =============================================================================
# QUEUE BINDINGS TO RESPECTIVE EXCHANGES
# =============================================================================
# Bind each queue to its corresponding exchange
# temp_queue receives messages directly from temp_exchange
channel.queue_bind(exchange='temp_exchange', queue='temp_queue')
# archive_queue receives messages from archive_exchange (copies from temp_exchange)
channel.queue_bind(exchange='archive_exchange', queue='archive_queue')

print(' [✓] Created queues and bindings')

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

print(' [*] Sending messages every 3 seconds to temp_exchange')
print(' [*] Messages will be copied to both temp_queue and archive_queue')
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
        
        # Publish ONLY to temp_exchange (source exchange)
        # Exchange-to-exchange binding automatically copies to archive_exchange
        channel.basic_publish(
            exchange='temp_exchange',               # Source exchange only
            routing_key='',                        # Empty for fanout exchange
            body=message,                          # Business event message
            properties=pika.BasicProperties(
                delivery_mode=2                    # Persistent message for reliability
            )
        )
        
        print(f" [x] Sent to temp_exchange (auto-copied to archive): {message}")
        counter += 1
        time.sleep(3)  # Wait 3 seconds between messages
        
except KeyboardInterrupt:
    print('\n [!] Interrupted')

# =============================================================================
# EXCHANGE-TO-EXCHANGE BINDING DEMONSTRATION SUMMARY
# =============================================================================
print('\n' + '='*70)
print(' [!] EXCHANGE-TO-EXCHANGE BINDING DEMO:')
print(' [!] 1. Messages sent ONLY to temp_exchange (source)')
print(' [!] 2. Automatically copied to archive_exchange via binding')
print(' [!] 3. Both temp_queue and archive_queue receive identical messages')
print(' [!] 4. Run consumers to see dual processing paths:')
print(' [!]    - temp consumer: fast, non-durable processing')
print(' [!]    - archive consumer: reliable, durable storage')
print(' [!] 5. Test durability: restart RabbitMQ and see what survives')
print('='*70)

# Clean up connection
connection.close()