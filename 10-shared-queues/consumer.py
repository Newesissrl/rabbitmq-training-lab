#!/usr/bin/env python3
import pika
import sys
import time
import random

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================
# Each worker needs a unique name for identification in logs
if len(sys.argv) < 2:
    print("Usage: python consumer.py <worker_name>")
    print("Example: python consumer.py worker-1")
    sys.exit(1)

worker_name = sys.argv[1]

# =============================================================================
# RABBITMQ CONNECTION SETUP
# =============================================================================
# Create connection to RabbitMQ server running on localhost:5672
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# Create a channel for AMQP operations (declare, publish, consume)
channel = connection.channel()

# =============================================================================
# QUEUE DECLARATION
# =============================================================================
# Declare the shared queue that multiple workers will consume from
# durable=True ensures queue survives RabbitMQ server restarts
# This is the SAME queue that all workers connect to (shared consumption)
channel.queue_declare(queue='shared_tasks', durable=True)

# =============================================================================
# MESSAGE PROCESSING CALLBACK FUNCTION
# =============================================================================
def callback(ch, method, properties, body):
    """Process a single task message from the shared queue"""
    # Decode the message body from bytes to string
    task = body.decode()
    
    # Simulate variable processing time to demonstrate real-world scenarios
    # Different tasks take different amounts of time to process
    processing_time = random.uniform(1, 4)
    
    print(f" [x] {worker_name} received: {task}")
    print(f" [→] {worker_name} processing... ({processing_time:.1f}s)")
    
    # Simulate actual work being done (replace with real business logic)
    time.sleep(processing_time)
    
    print(f" [✓] {worker_name} completed: {task}")
    
    # CRITICAL: Acknowledge message processing completion
    # This tells RabbitMQ the message was successfully processed
    # Without this, RabbitMQ will redeliver the message
    ch.basic_ack(delivery_tag=method.delivery_tag)

# =============================================================================
# CONSUMER CONFIGURATION
# =============================================================================
# Configure fair dispatch: only send one unacknowledged message to each worker
# This ensures even distribution of work among workers
# Without this, RabbitMQ might send all messages to one fast worker
channel.basic_qos(prefetch_count=1)

# Set up message consumption from the shared queue
# All workers consume from the SAME queue (shared_tasks)
# Each message will be delivered to only ONE worker (load balancing)
channel.basic_consume(
    queue='shared_tasks',           # The shared queue name
    on_message_callback=callback    # Function to call for each message
    # auto_ack=False by default - requires manual acknowledgment
)

print(f' [*] {worker_name} connected to shared_tasks queue')
print(' [*] Waiting for tasks. To exit press CTRL+C')

# =============================================================================
# START CONSUMING MESSAGES
# =============================================================================
try:
    # Start the consuming loop - this blocks and waits for messages
    channel.start_consuming()
except KeyboardInterrupt:
    print(f'\n [!] {worker_name} interrupted')
    # Gracefully stop consuming messages
    channel.stop_consuming()

# =============================================================================
# CLEANUP
# =============================================================================
# Close the connection to RabbitMQ
connection.close()
print(f' [!] {worker_name} disconnected from shared_tasks queue')
print(' [!] Other workers can continue processing remaining tasks')