#!/usr/bin/env python3
import pika
import msgpack
import time
from datetime import datetime

def msgpack_producer():
    """Send messages using MessagePack serialization"""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    queue_name = 'msgpack_messages'
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Sample data structures (same as JSON example)
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
        # Serialize to MessagePack
        msgpack_bytes = msgpack.packb(message)
        total_size += len(msgpack_bytes)
        
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=msgpack_bytes,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/msgpack'
            )
        )
    
    end_time = time.time()
    
    print(f"MessagePack Producer Results:")
    print(f"Messages sent: {len(messages)}")
    print(f"Total size: {total_size:,} bytes")
    print(f"Average message size: {total_size / len(messages):.1f} bytes")
    print(f"Serialization time: {end_time - start_time:.3f} seconds")
    print(f"Throughput: {len(messages) / (end_time - start_time):.1f} msg/sec")
    
    connection.close()

def msgpack_consumer():
    """Receive and deserialize MessagePack messages"""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    queue_name = 'msgpack_messages'
    channel.queue_declare(queue=queue_name, durable=True)
    
    messages_received = []
    start_time = time.time()
    
    def callback(ch, method, properties, body):
        # Deserialize from MessagePack
        message = msgpack.unpackb(body, raw=False)
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
    
    print("MessagePack Consumer waiting for messages...")
    channel.start_consuming()
    
    end_time = time.time()
    
    print(f"\nMessagePack Consumer Results:")
    print(f"Messages received: {len(messages_received)}")
    print(f"Deserialization time: {end_time - start_time:.3f} seconds")
    print(f"Throughput: {len(messages_received) / (end_time - start_time):.1f} msg/sec")
    
    connection.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'consumer':
        msgpack_consumer()
    else:
        msgpack_producer()