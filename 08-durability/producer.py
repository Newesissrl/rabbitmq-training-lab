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
# NON-DURABLE COMPONENTS SETUP (LOST ON SERVER RESTART)
# =============================================================================
# Create NON-DURABLE exchange that is lost when RabbitMQ server restarts
# Non-durable exchanges exist only in memory and are not stored on disk
channel.exchange_declare(
    exchange='temp_exchange',
    exchange_type='direct',
    durable=False  # Lost on server restart - exists only in memory
)

# Create NON-DURABLE queue that is lost when RabbitMQ server restarts
# Non-durable queues exist only in memory and are not stored on disk
channel.queue_declare(
    queue='temp_queue',
    durable=False  # Lost on server restart - exists only in memory
)

# Bind non-durable queue to non-durable exchange
# Binding is lost on restart because both components are non-durable
channel.queue_bind(
    exchange='temp_exchange',
    queue='temp_queue',
    routing_key='temp_data'
)

print(' [✓] Created both durable and non-durable components')
print(' [*] Sending messages to both exchanges...')

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
# NON-PERSISTENT MESSAGES TO NON-DURABLE COMPONENTS
# =============================================================================
# Send NON-PERSISTENT messages to non-durable exchange/queue combination
# These messages will be LOST on RabbitMQ server restart because:
# 1. Exchange is non-durable (lost on restart)
# 2. Queue is non-durable (lost on restart)
# 3. Messages are non-persistent (delivery_mode=1)
temp_messages = [
    'Temporary notification #1',    # Temporary system notification
    'Cache invalidation #2',        # Cache invalidation message
    'Session cleanup #3',           # Session cleanup notification
    'Temporary status #4',          # Temporary status update
    'Ephemeral event #5'            # Short-lived event notification
]

for i, message in enumerate(temp_messages, 1):
    channel.basic_publish(
        exchange='temp_exchange',           # Non-durable exchange
        routing_key='temp_data',           # Routing key for non-durable queue
        body=message,                      # Message content
        properties=pika.BasicProperties(
            delivery_mode=1                # Non-persistent message - lost on restart
        )
    )
    print(f" [✓] Sent NON-PERSISTENT to temp_queue: {message}")

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

# =============================================================================
# DURABILITY EXPERIMENT INSTRUCTIONS
# =============================================================================
print('\n' + '='*60)
print(' [!] DURABILITY EXPERIMENT SETUP COMPLETE')
print(' [!] ')
print(' [!] Current state - check Web UI at http://localhost:15672:')
print(' [!]   - durable_exchange and durable_queue (with 7 messages total)')
print(' [!]     * 5 persistent messages (will survive restart)')
print(' [!]     * 2 non-persistent messages (will be lost on restart)')
print(' [!]   - temp_exchange and temp_queue (with 5 messages)')
print(' [!]     * All non-persistent messages (will be lost on restart)')
print(' [!] ')
print(' [!] EXPERIMENT STEPS:')
print(' [!] 1. Verify both exchanges/queues exist in Web UI')
print(' [!] 2. Note message counts in both queues')
print(' [!] 3. Stop RabbitMQ: docker stop rabbitmq')
print(' [!] 4. Start RabbitMQ: docker start rabbitmq')
print(' [!] 5. Check Web UI again:')
print(' [!]    - temp_exchange and temp_queue will be GONE')
print(' [!]    - durable_exchange and durable_queue will remain')
print(' [!]    - Only 5 persistent messages will survive in durable_queue')
print(' [!] 6. Run consumer.py to process surviving messages')
print(' [!] ')
print(' [!] LEARNING OBJECTIVES:')
print(' [!] - Durable components survive server restart')
print(' [!] - Non-durable components are lost on server restart')
print(' [!] - Message persistence (delivery_mode) is independent of queue durability')
print(' [!] - Non-persistent messages are lost even in durable queues')
print('='*60)

# Clean up connection
connection.close()