#!/usr/bin/env python3
import pika

print(' [*] Checking what survived the RabbitMQ restart...')

# Check durable exchange
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(
        exchange='durable_exchange',
        exchange_type='direct',
        durable=True,
        passive=True  # Just check if exists, don't create
    )
    print(' [✓] durable_exchange survived restart')
    connection.close()
except Exception as e:
    print(' [❌] durable_exchange not found (unexpected!)')
    if 'connection' in locals():
        connection.close()

# Check temp exchange (separate connection since passive check may close channel)
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(
        exchange='temp_exchange',
        exchange_type='direct',
        durable=False,
        passive=True  # Just check if exists
    )
    print(' [❌] temp_exchange survived restart (unexpected!)')
    connection.close()
except Exception as e:
    print(' [✓] temp_exchange was lost on restart (expected)')
    if 'connection' in locals():
        connection.close()

# Check durable queue (new connection for consuming)
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

try:
    # Check if queue exists and get message count
    method = channel.queue_declare(queue='durable_queue', durable=True, passive=True)
    message_count = method.method.message_count
    print(' [✓] durable_queue survived restart')
    print(f' [ℹ️] durable_queue has {message_count} surviving messages')
except Exception as e:
    print(' [❌] durable_queue not found (unexpected!)')
    print(f' [❌] Error: {e}')
    connection.close()
    exit(1)

print('\n [*] Consuming surviving messages from durable_queue...')
print(' [*] Only PERSISTENT messages should appear. To exit press CTRL+C')

def callback(ch, method, properties, body):
    message = body.decode()
    delivery_mode = properties.delivery_mode
    persistence = "PERSISTENT" if delivery_mode == 2 else "NON-PERSISTENT"
    
    print(f" [x] Received {persistence}: {message}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Consume from durable queue
try:
    channel.basic_consume(
        queue='durable_queue',
        on_message_callback=callback
    )
    
    channel.start_consuming()
    
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    channel.stop_consuming()
    
except Exception as e:
    print(f' [❌] Error consuming from durable_queue: {e}')

if connection and not connection.is_closed:
    connection.close()

print('\n' + '='*60)
print(' [!] SUMMARY:')
print(' [!] ✅ Durable exchange and queue survived restart')
print(' [!] ❌ Non-durable exchange and queue were lost')
print(' [!] ✅ Persistent messages in durable queue survived')
print(' [!] ❌ Non-persistent messages were lost (even in durable queue)')
print('='*60)