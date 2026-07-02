#!/usr/bin/env python3
import pika
import time
import random

# =============================================================================
# RABBITMQ CONNECTION SETUP
# =============================================================================
# Create connection to RabbitMQ server running on localhost:5672
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# Create a channel for AMQP operations
channel = connection.channel()

# =============================================================================
# SHARED QUEUE DECLARATION
# =============================================================================
# Declare a shared, durable queue that multiple workers will consume from
# durable=True ensures queue survives RabbitMQ server restarts
# This is the SAME queue that all workers will compete for tasks from
channel.queue_declare(queue='shared_tasks', durable=True)

# =============================================================================
# TASK TEMPLATES FOR WORK DISTRIBUTION
# =============================================================================
# Various types of tasks that will be distributed among workers
# Each task represents work that can be processed by any available worker
tasks = [
    'Process image: photo_{}.jpg',           # Image processing task
    'Send email to user_{}@example.com',     # Email sending task
    'Generate report for order_{}',          # Report generation task
    'Backup database table_{}',              # Database backup task
    'Resize video: video_{}.mp4',            # Video processing task
    'Calculate analytics for dataset_{}',    # Analytics calculation task
    'Validate payment transaction_{}',       # Payment validation task
    'Index document: doc_{}.pdf'             # Document indexing task
]

print(' [*] Sending tasks to shared_tasks queue every 2 seconds')
print(' [*] Tasks will be distributed among available workers')
print(' [*] To exit press CTRL+C')

# =============================================================================
# CONTINUOUS TASK PUBLISHING LOOP
# =============================================================================
try:
    task_id = 1
    while True:
        # Create task with unique ID from random template
        task_template = random.choice(tasks)
        task = task_template.format(task_id)
        
        # Send task to shared queue using default exchange
        # All workers consume from the SAME queue (load balancing)
        channel.basic_publish(
            exchange='',                                    # Default exchange
            routing_key='shared_tasks',                    # Queue name as routing key
            body=task,                                     # Task description
            properties=pika.BasicProperties(
                delivery_mode=2                            # Make task persistent
            )
        )
        
        print(f" [x] Sent task #{task_id}: {task}")
        task_id += 1
        time.sleep(2)  # Wait 2 seconds between tasks
        
except KeyboardInterrupt:
    print('\n [!] Interrupted')

# =============================================================================
# SUMMARY OF SHARED QUEUE PATTERN
# =============================================================================
print('\n' + '='*60)
print(' [!] SHARED QUEUE PATTERN:')
print(' [!] ✅ Tasks sent to single shared_tasks queue')
print(' [!] ✅ Multiple workers can process from same queue')
print(' [!] ✅ Each task processed by only ONE worker')
print(' [!] ✅ Load balancing automatic among available workers')
print(' [!] ✅ Queue persists even when no workers connected')
print('='*60)

# Clean up connection
connection.close()