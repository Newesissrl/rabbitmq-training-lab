#!/usr/bin/env python3
import pika

# =============================================================================
# DURABILITY VERIFICATION CONSUMER
# =============================================================================
# This consumer runs AFTER RabbitMQ server restart to verify:
# 1. Which exchanges and queues survived (durable components)
# 2. Which exchanges and queues were lost (non-durable components)
# 3. Which messages survived (persistent messages in durable queues)

print(' [*] Checking what survived the RabbitMQ restart...')

# =============================================================================
# DURABLE EXCHANGE VERIFICATION
# =============================================================================
# Check if durable exchange survived the server restart
# Durable exchanges should persist through restarts
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    # Use passive=True to check existence without creating
    channel.exchange_declare(
        exchange='durable_exchange',
        exchange_type='direct',
        durable=True,
        passive=True  # Only check if exists, don't create if missing
    )
    print(' [✓] durable_exchange survived restart (expected)')
    connection.close()
except Exception as e:
    print(' [❌] durable_exchange not found (unexpected!)')
    if 'connection' in locals():
        connection.close()

# =============================================================================
# NON-DURABLE EXCHANGE VERIFICATION
# =============================================================================
# Historically a non-durable exchange disappeared on restart.
# RabbitMQ 4.3 stores all metadata in Khepri (on disk), so the durable flag of
# an exchange no longer makes a difference: the exchange is expected to be there.
# Use separate connection since passive check failures close the channel
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(
        exchange='transient_exchange',
        exchange_type='direct',
        durable=False,
        passive=True  # Only check if exists
    )
    print(' [ℹ️] transient_exchange is still there after restart (RabbitMQ 4.3 / Khepri behaviour)')
    connection.close()
except Exception as e:
    print(' [ℹ️] transient_exchange is gone after restart')
    if 'connection' in locals() and connection.is_open:
        connection.close()

# =============================================================================
# DURABLE QUEUE VERIFICATION AND MESSAGE CONSUMPTION
# =============================================================================
# Create new connection for consuming surviving messages
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

try:
    # Check if durable queue survived and get surviving message count
    method = channel.queue_declare(queue='durable_queue', durable=True, passive=True)
    message_count = method.method.message_count
    print(' [✓] durable_queue survived restart (expected)')
    print(f' [ℹ️] durable_queue has {message_count} surviving messages')
    print(f' [ℹ️] Expected: 5 persistent messages (2 non-persistent were lost)')
except Exception as e:
    print(' [❌] durable_queue not found (unexpected!)')
    print(f' [❌] Error: {e}')
    connection.close()
    exit(1)

print('\n [*] Consuming surviving messages from durable_queue...')
print(' [*] Only PERSISTENT messages should appear (delivery_mode=2)')
print(' [*] Non-persistent messages were lost even though queue is durable')
print(' [*] To exit press CTRL+C')

# =============================================================================
# SURVIVING MESSAGE PROCESSING CALLBACK
# =============================================================================
def callback(ch, method, properties, body):
    """Process messages that survived the server restart"""
    message = body.decode()
    # Check message persistence level
    delivery_mode = properties.delivery_mode
    persistence = "PERSISTENT" if delivery_mode == 2 else "NON-PERSISTENT"
    
    print(f" [x] Received {persistence}: {message}")
    
    # Note: Only persistent messages (delivery_mode=2) should appear here
    # Non-persistent messages (delivery_mode=1) were lost on restart
    if delivery_mode == 1:
        print(f"     [⚠️] WARNING: Non-persistent message survived (unexpected!)")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

# =============================================================================
# START CONSUMING SURVIVING MESSAGES
# =============================================================================
# Consume from the durable queue to process messages that survived restart
try:
    channel.basic_consume(
        queue='durable_queue',          # Only durable queue survived
        on_message_callback=callback    # Process surviving messages
    )
    
    print(' [*] Starting consumption of surviving messages...')
    # Start consuming - only persistent messages should be processed
    channel.start_consuming()
    
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    # Gracefully stop consuming
    channel.stop_consuming()
    
except Exception as e:
    print(f' [❌] Error consuming from durable_queue: {e}')

# =============================================================================
# CLEANUP
# =============================================================================
# Close connection if still open
if connection and not connection.is_closed:
    connection.close()

# =============================================================================
# DURABILITY EXPERIMENT SUMMARY
# =============================================================================
print('\n' + '='*60)
print(' [!] DURABILITY EXPERIMENT RESULTS:')
print(' [!] ')
print(' [!] COMPONENT SURVIVAL:')
print(' [!] ✅ durable_exchange and durable_queue survived restart')
print(' [!] ℹ️  transient_exchange also survived (RabbitMQ 4.3 keeps all metadata in Khepri)')
print(' [!] ❌ non-durable shared queues cannot even be created on RabbitMQ 4.3')
print(' [!] ')
print(' [!] MESSAGE SURVIVAL:')
print(' [!] ✅ Persistent messages (delivery_mode=2) survived in durable queue')
print(' [!] ❌ Non-persistent messages (delivery_mode=1) were lost even in durable queue!')
print(' [!] ')
print(' [!] KEY LEARNINGS:')
print(' [!] - Queue durability and message persistence are independent settings')
print(' [!] - Both a durable queue AND persistent messages are needed for survival')
print(' [!] - On RabbitMQ 4.3, delivery_mode is what decides if a message survives')
print('='*60)
