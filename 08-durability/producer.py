#!/usr/bin/env python3
import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

print(' [*] Creating durable and non-durable components...')

# Create DURABLE exchange and queue
channel.exchange_declare(
    exchange='durable_exchange',
    exchange_type='direct',
    durable=True  # Survives server restart
)

channel.queue_declare(
    queue='durable_queue',
    durable=True  # Survives server restart
)

channel.queue_bind(
    exchange='durable_exchange',
    queue='durable_queue',
    routing_key='persistent_data'
)

# Create NON-DURABLE exchange and queue
channel.exchange_declare(
    exchange='temp_exchange',
    exchange_type='direct',
    durable=False  # Lost on server restart
)

channel.queue_declare(
    queue='temp_queue',
    durable=False  # Lost on server restart
)

channel.queue_bind(
    exchange='temp_exchange',
    queue='temp_queue',
    routing_key='temp_data'
)

print(' [✓] Created both durable and non-durable components')
print(' [*] Sending messages to both exchanges...')

# Send PERSISTENT messages to durable exchange
persistent_messages = [
    'Critical business data #1',
    'Important financial record #2', 
    'Essential user information #3',
    'Vital system configuration #4',
    'Critical audit log #5'
]

for i, message in enumerate(persistent_messages, 1):
    channel.basic_publish(
        exchange='durable_exchange',
        routing_key='persistent_data',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2  # Persistent message
        )
    )
    print(f" [✓] Sent PERSISTENT to durable_queue: {message}")

# Send NON-PERSISTENT messages to non-durable exchange
temp_messages = [
    'Temporary notification #1',
    'Cache invalidation #2',
    'Session cleanup #3', 
    'Temporary status #4',
    'Ephemeral event #5'
]

for i, message in enumerate(temp_messages, 1):
    channel.basic_publish(
        exchange='temp_exchange',
        routing_key='temp_data',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=1  # Non-persistent message
        )
    )
    print(f" [✓] Sent NON-PERSISTENT to temp_queue: {message}")

# Also send some NON-PERSISTENT messages to DURABLE queue (to show they're lost too)
mixed_messages = [
    'Non-persistent in durable queue #1',
    'Non-persistent in durable queue #2'
]

for message in mixed_messages:
    channel.basic_publish(
        exchange='durable_exchange',
        routing_key='persistent_data',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=1  # Non-persistent message in durable queue
        )
    )
    print(f" [⚠️] Sent NON-PERSISTENT to durable_queue: {message}")

print('\n' + '='*60)
print(' [!] IMPORTANT: Now check the Web UI at http://localhost:15672')
print(' [!] You should see:')
print(' [!]   - durable_exchange and durable_queue (with 7 messages)')
print(' [!]   - temp_exchange and temp_queue (with 5 messages)')
print(' [!] ')
print(' [!] Next steps:')
print(' [!] 1. Verify both exchanges/queues exist in Web UI')
print(' [!] 2. Stop RabbitMQ: docker stop rabbitmq')
print(' [!] 3. Start RabbitMQ: docker start rabbitmq') 
print(' [!] 4. Check Web UI again - temp components will be GONE!')
print(' [!] 5. Run consumer.py to see surviving messages')
print('='*60)

connection.close()