#!/usr/bin/env python3
import pika
import sys
import time
import random

if len(sys.argv) < 2:
    print("Usage: python consumer.py <worker_name>")
    print("Example: python consumer.py worker-1")
    sys.exit(1)

worker_name = sys.argv[1]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare the same shared, durable queue
channel.queue_declare(queue='shared_tasks', durable=True)

print(f' [*] {worker_name} connected to shared_tasks queue')
print(' [*] Waiting for tasks. To exit press CTRL+C')

def callback(ch, method, properties, body):
    task = body.decode()
    
    # Simulate variable processing time (1-4 seconds)
    processing_time = random.uniform(1, 4)
    
    print(f" [x] {worker_name} received: {task}")
    print(f" [→] {worker_name} processing... ({processing_time:.1f}s)")
    
    # Simulate work
    time.sleep(processing_time)
    
    print(f" [✓] {worker_name} completed: {task}")
    
    # Acknowledge task completion
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Fair dispatch - don't give more than one task to a worker at a time
channel.basic_qos(prefetch_count=1)

# Connect to shared queue
channel.basic_consume(
    queue='shared_tasks',
    on_message_callback=callback
)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print(f'\n [!] {worker_name} interrupted')
    channel.stop_consuming()

connection.close()
print(f' [!] {worker_name} disconnected from shared_tasks queue')
print(' [!] Other workers can continue processing remaining tasks')