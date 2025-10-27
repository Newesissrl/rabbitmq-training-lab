#!/usr/bin/env python3
import pika
import sys
import time

if len(sys.argv) < 2:
    print("Usage: python consumer.py [temp|archive]")
    print("  temp    - Fast processing from non-durable queue")
    print("  archive - Reliable processing from durable queue")
    sys.exit(1)

consumer_type = sys.argv[1]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

if consumer_type == 'temp':
    # Fast processing consumer
    queue_name = 'temp_queue'
    exchange_name = 'temp_exchange'
    
    # Declare non-durable components
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=False)
    channel.queue_declare(queue=queue_name, durable=False)
    channel.queue_bind(exchange=exchange_name, queue=queue_name)
    
    print(' [*] TEMP CONSUMER - Fast processing from non-durable queue')
    print(' [*] This consumer and queue will be LOST on server restart')
    
elif consumer_type == 'archive':
    # Reliable storage consumer  
    queue_name = 'archive_queue'
    exchange_name = 'archive_exchange'
    
    # Declare durable components
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=True)
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange=exchange_name, queue=queue_name)
    
    print(' [*] ARCHIVE CONSUMER - Reliable processing from durable queue')
    print(' [*] This consumer and queue will SURVIVE server restart')
    
else:
    print("Invalid consumer type. Use 'temp' or 'archive'")
    sys.exit(1)

print(f' [*] Waiting for messages from {queue_name}. To exit press CTRL+C')

def callback(ch, method, properties, body):
    message = body.decode()
    
    if consumer_type == 'temp':
        # Fast processing - minimal work
        print(f" [⚡] TEMP processed: {message}")
        time.sleep(0.1)  # Fast processing
        
    elif consumer_type == 'archive':
        # Reliable processing - more thorough work
        print(f" [💾] ARCHIVE stored: {message}")
        time.sleep(1)    # Slower, more reliable processing
        
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print(f'\n [!] {consumer_type.upper()} consumer interrupted')
    channel.stop_consuming()

connection.close()

if consumer_type == 'temp':
    print(' [!] TEMP consumer stopped - queue will be lost on server restart')
elif consumer_type == 'archive':
    print(' [!] ARCHIVE consumer stopped - queue and messages will survive restart')