#!/usr/bin/env python3
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare shared, durable queue
channel.queue_declare(queue='shared_tasks', durable=True)

# Task templates for work distribution
tasks = [
    'Process image: photo_{}.jpg',
    'Send email to user_{}@example.com', 
    'Generate report for order_{}',
    'Backup database table_{}',
    'Resize video: video_{}.mp4',
    'Calculate analytics for dataset_{}',
    'Validate payment transaction_{}',
    'Index document: doc_{}.pdf'
]

print(' [*] Sending tasks to shared_tasks queue every 2 seconds')
print(' [*] Tasks will be distributed among available workers')
print(' [*] To exit press CTRL+C')

try:
    task_id = 1
    while True:
        # Create task with unique ID
        task_template = random.choice(tasks)
        task = task_template.format(task_id)
        
        # Send task to shared queue
        channel.basic_publish(
            exchange='',  # Default exchange
            routing_key='shared_tasks',
            body=task,
            properties=pika.BasicProperties(
                delivery_mode=2  # Make task persistent
            )
        )
        
        print(f" [x] Sent task #{task_id}: {task}")
        task_id += 1
        time.sleep(2)
        
except KeyboardInterrupt:
    print('\n [!] Interrupted')

print('\n' + '='*60)
print(' [!] SHARED QUEUE PATTERN:')
print(' [!] ✅ Tasks sent to single shared_tasks queue')
print(' [!] ✅ Multiple workers can process from same queue')
print(' [!] ✅ Each task processed by only ONE worker')
print(' [!] ✅ Load balancing automatic among available workers')
print(' [!] ✅ Queue persists even when no workers connected')
print('='*60)

connection.close()