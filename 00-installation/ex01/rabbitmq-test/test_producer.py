import pika
import sys

try:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            credentials=pika.PlainCredentials('admin', 'password123')
        )
    )
    channel = connection.channel()
    
    channel.queue_declare(queue='test_queue')
    channel.basic_publish(
        exchange='',
        routing_key='test_queue',
        body='Hello RabbitMQ!'
    )
    
    print(" [x] Sent 'Hello RabbitMQ!'")
    connection.close()
    
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
