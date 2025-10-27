#!/usr/bin/env python3
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

print(' [*] Creating exchange-to-exchange binding setup...')

# Create NON-DURABLE source exchange (for fast processing)
channel.exchange_declare(
    exchange='temp_exchange',
    exchange_type='fanout',
    durable=False  # Fast, temporary processing
)

# Create DURABLE target exchange (for reliable storage)
channel.exchange_declare(
    exchange='archive_exchange', 
    exchange_type='fanout',
    durable=True  # Reliable, persistent storage
)

# Bind temp_exchange TO archive_exchange (exchange-to-exchange binding)
channel.exchange_bind(
    destination='archive_exchange',  # Target exchange
    source='temp_exchange',         # Source exchange
    routing_key=''                  # Empty for fanout
)

print(' [✓] Created exchange-to-exchange binding: temp_exchange → archive_exchange')

# Create queues for both paths
channel.queue_declare(queue='temp_queue', durable=False)      # Fast processing
channel.queue_declare(queue='archive_queue', durable=True)    # Reliable storage

# Bind queues to their respective exchanges
channel.queue_bind(exchange='temp_exchange', queue='temp_queue')
channel.queue_bind(exchange='archive_exchange', queue='archive_queue')

print(' [✓] Created queues and bindings')

# Message templates
messages = [
    'Order #12345 processed',
    'User login: john@example.com',
    'Payment completed: $99.99',
    'Inventory updated: Product ABC',
    'System alert: High CPU usage',
    'Data backup completed',
    'Security scan finished',
    'Report generated: Monthly sales'
]

print(' [*] Sending messages every 3 seconds to temp_exchange')
print(' [*] Messages will be copied to both temp_queue and archive_queue')
print(' [*] To exit press CTRL+C')

try:
    counter = 1
    while True:
        message_template = random.choice(messages)
        message = f"{message_template} #{counter}"
        
        # Send to temp_exchange - will be copied to archive_exchange automatically
        channel.basic_publish(
            exchange='temp_exchange',  # Only publish to source exchange
            routing_key='',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2  # Persistent message
            )
        )
        
        print(f" [x] Sent to temp_exchange (auto-copied to archive): {message}")
        counter += 1
        time.sleep(3)
        
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    
print('\n' + '='*70)
print(' [!] EXCHANGE-TO-EXCHANGE BINDING DEMO:')
print(' [!] 1. Messages sent ONLY to temp_exchange')
print(' [!] 2. Automatically copied to archive_exchange via binding')
print(' [!] 3. Both temp_queue and archive_queue receive messages')
print(' [!] 4. Run consumers to see dual processing paths')
print(' [!] 5. Test durability: restart RabbitMQ and see what survives')
print('='*70)

connection.close()