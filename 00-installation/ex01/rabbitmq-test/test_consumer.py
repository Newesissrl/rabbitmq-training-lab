import pika
import sys

def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

try:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            credentials=pika.PlainCredentials('admin', 'password123')
        )
    )
    channel = connection.channel()
    
    channel.queue_declare(queue='test_queue')
    channel.basic_consume(
        queue='test_queue',
        on_message_callback=callback
    )
    
    print(' [*] Waiting for messages. CTRL+C to exit')
    channel.start_consuming()
    
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    channel.stop_consuming()
    connection.close()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
