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

print(' [*] Creating durable and non-durable components...')

# =============================================================================
# DURABLE COMPONENTS SETUP (SURVIVE SERVER RESTART)
# =============================================================================
# Create DURABLE exchange that persists through RabbitMQ server restarts
# Durable exchanges are stored on disk and recreated after restart
channel.exchange_declare(
    exchange='durable_exchange',
    exchange_type='direct',
    durable=True  # Survives server restart - stored on disk
)

# Create DURABLE queue that persists through RabbitMQ server restarts
# Durable queues are stored on disk and recreated after restart
channel.queue_declare(
    queue='durable_queue',
    durable=True  # Survives server restart - stored on disk
)

# Bind durable queue to durable exchange
# Binding survives restart because both components are durable
channel.queue_bind(
    exchange='durable_exchange',
    queue='durable_queue',
    routing_key='persistent_data'
)

# =============================================================================
# NON-DURABLE EXCHANGE (durable=False)
# =============================================================================
# Historically, non-durable exchanges lived only in memory and vanished on
# restart. Since RabbitMQ 4.x all metadata is stored in Khepri (a Raft-based,
# on-disk store) and transient entities are being phased out: on RabbitMQ 4.3
# you will see that this exchange is STILL THERE after a restart.
channel.exchange_declare(
    exchange='transient_exchange',
    exchange_type='direct',
    durable=False
)

print(' [✓] Created durable_exchange, durable_queue and transient_exchange')
print(' [*] Sending persistent and non-persistent messages to durable_queue...')

# =============================================================================
# PERSISTENT MESSAGES TO DURABLE COMPONENTS
# =============================================================================
# Send PERSISTENT messages to durable exchange/queue combination
# These messages will survive RabbitMQ server restart because:
# 1. Exchange is durable (survives restart)
# 2. Queue is durable (survives restart)
# 3. Messages are persistent (delivery_mode=2)
persistent_messages = [
    'Critical business data #1',        # Mission-critical data
    'Important financial record #2',    # Financial transaction record
    'Essential user information #3',    # User account data
    'Vital system configuration #4',    # System configuration
    'Critical audit log #5'             # Compliance audit log
]

for i, message in enumerate(persistent_messages, 1):
    channel.basic_publish(
        exchange='durable_exchange',        # Durable exchange
        routing_key='persistent_data',     # Routing key for durable queue
        body=message,                      # Message content
        properties=pika.BasicProperties(
            delivery_mode=2                # Persistent message - survives restart
        )
    )
    print(f" [✓] Sent PERSISTENT to durable_queue: {message}")

# =============================================================================
# NON-PERSISTENT MESSAGES TO DURABLE COMPONENTS (MIXED SCENARIO)
# =============================================================================
# Send NON-PERSISTENT messages to DURABLE queue to demonstrate that
# message persistence depends on delivery_mode, not queue durability
# These messages will be LOST on restart even though queue is durable
mixed_messages = [
    'Non-persistent in durable queue #1',  # Will be lost despite durable queue
    'Non-persistent in durable queue #2'   # Will be lost despite durable queue
]

for message in mixed_messages:
    channel.basic_publish(
        exchange='durable_exchange',        # Durable exchange
        routing_key='persistent_data',     # Routing key for durable queue
        body=message,                      # Message content
        properties=pika.BasicProperties(
            delivery_mode=1                # Non-persistent - LOST even in durable queue
        )
    )
    print(f" [⚠️] Sent NON-PERSISTENT to durable_queue: {message}")

# Clean up connection
connection.close()

# =============================================================================
# NON-DURABLE QUEUE: REJECTED BY RABBITMQ 4.3
# =============================================================================
# A non-durable, non-exclusive ("transient") queue is a deprecated feature that
# RabbitMQ 4.3 denies by default. The broker answers with an error and closes
# the connection, so we try it on a separate connection.
print(' [*] Trying to declare a non-durable shared queue (temp_queue)...')
try:
    probe = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    probe.channel().queue_declare(queue='temp_queue', durable=False)
    print(' [⚠️] temp_queue was accepted - transient_nonexcl_queues is permitted on this broker')
    probe.close()
except pika.exceptions.AMQPError as e:
    reason = str(e.args[-1]) if e.args else str(e)
    print(f' [✓] Rejected by the broker as expected: {reason.splitlines()[0]}')

# =============================================================================
# DURABILITY EXPERIMENT INSTRUCTIONS
# =============================================================================
print('\n' + '='*60)
print(' [!] DURABILITY EXPERIMENT SETUP COMPLETE')
print(' [!] ')
print(' [!] Current state - check Web UI at http://localhost:15672:')
print(' [!]   - durable_queue with 7 messages:')
print(' [!]     * 5 persistent messages (will survive restart)')
print(' [!]     * 2 non-persistent messages (will be lost on restart)')
print(' [!]   - transient_exchange (durable=false)')
print(' [!] ')
print(' [!] EXPERIMENT STEPS:')
print(' [!] 1. Note the message count of durable_queue (7)')
print(' [!] 2. Restart RabbitMQ: docker restart rabbitmq')
print(' [!] 3. Check Web UI again:')
print(' [!]    - durable_queue only has the 5 persistent messages')
print(' [!]    - transient_exchange is still listed (RabbitMQ 4.3 / Khepri)')
print(' [!] 4. Run consumer.py to process surviving messages')
print(' [!] ')
print(' [!] LEARNING OBJECTIVES:')
print(' [!] - Durable queues survive server restart')
print(' [!] - Message persistence (delivery_mode) is independent of queue durability')
print(' [!] - Non-persistent messages are lost even in durable queues')
print(' [!] - RabbitMQ 4.3 rejects non-durable shared queues')
print('='*60)
