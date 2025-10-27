#!/usr/bin/env python3
import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare same non-durable exchange
channel.exchange_declare(
    exchange='temp_exchange',
    exchange_type='direct',
    durable=False,
    auto_delete=True
)

# Declare non-durable, auto-delete queue
channel.queue_declare(
    queue='temp_queue',
    durable=False,      # Non-durable - won't survive server restart
    auto_delete=True,   # Auto-delete when consumer disconnects
    exclusive=False     # Allow multiple consumers
)

# Bind queue to exchange
channel.queue_bind(
    exchange='temp_exchange',
    queue='temp_queue',
    routing_key='temp_data'
)

print(' [*] Consuming messages before they expire (TTL=5s)')
print(' [*] Queue will auto-delete when consumer stops. To exit press CTRL+C')

def callback(ch, method, properties, body):
    message = body.decode()
    print(f" [x] Received: {message}")
    
    # Simulate processing time (but less than TTL)
    time.sleep(1)
    
    print(f" [✓] Processed: {message}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Configure consumer
channel.basic_qos(prefetch_count=1)
channel.basic_consume(
    queue='temp_queue',
    on_message_callback=callback
)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    channel.stop_consuming()
    connection.close()
    print(' [!] Consumer stopped - queue will auto-delete')