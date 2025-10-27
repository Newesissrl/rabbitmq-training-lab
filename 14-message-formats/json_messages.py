#!/usr/bin/env python3
import pika
import json
import time
from datetime import datetime

def json_producer():
    """Send messages using JSON serialization"""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    queue_name = 'json_messages'
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Sample data structures
    messages = [
        {
            "id": i,
            "timestamp": datetime.now().isoformat(),
            "user": {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 25 + (i % 50)
            },
            "order": {
                "items": [
                    {"product": "Widget A", "quantity": i % 5 + 1, "price": 19.99},
                    {"product": "Widget B", "quantity": i % 3 + 1, "price": 29.99}
                ],
                "total": (i % 5 + 1) * 19.99 + (i % 3 + 1) * 29.99,
                "status": "pending"
            },
            "metadata": {
                "source": "web",
                "campaign": f"campaign_{i % 10}",
                "tags": [f"tag{j}" for j in range(i % 5)]
            }
        }
        for i in range(100)
    ]
    
    start_time = time.time()
    total_size = 0
    
    for message in messages:
        # Serialize to JSON
        json_data = json.dumps(message)
        json_bytes = json_data.encode('utf-8')
        total_size += len(json_bytes)
        
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json_bytes,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
    
    end_time = time.time()
    
    print(f"JSON Producer Results:")
    print(f"Messages sent: {len(messages)}")
    print(f"Total size: {total_size:,} bytes")
    print(f"Average message size: {total_size / len(messages):.1f} bytes")
    print(f"Serialization time: {end_time - start_time:.3f} seconds")
    print(f"Throughput: {len(messages) / (end_time - start_time):.1f} msg/sec")
    
    connection.close()

def json_consumer():
    """Receive and deserialize JSON messages"""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    queue_name = 'json_messages'
    channel.queue_declare(queue=queue_name, durable=True)
    
    messages_received = []
    start_time = time.time()
    
    def callback(ch, method, properties, body):
        # Deserialize from JSON
        json_data = body.decode('utf-8')
        message = json.loads(json_data)
        messages_received.append(message)
        
        # Process message
        user_name = message['user']['name']
        order_total = message['order']['total']
        print(f"Processed order for {user_name}: ${order_total:.2f}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        if len(messages_received) >= 100:
            ch.stop_consuming()
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    
    print("JSON Consumer waiting for messages...")
    channel.start_consuming()
    
    end_time = time.time()
    
    print(f"\nJSON Consumer Results:")
    print(f"Messages received: {len(messages_received)}")
    print(f"Deserialization time: {end_time - start_time:.3f} seconds")
    print(f"Throughput: {len(messages_received) / (end_time - start_time):.1f} msg/sec")
    
    connection.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'consumer':
        json_consumer()
    else:
        json_producer()