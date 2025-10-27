#!/usr/bin/env python3
import pika
import json
import msgpack
import pickle
import time
from datetime import datetime

def create_sample_data(count=10000):
    """Create sample data for testing"""
    return [
        {
            "id": i,
            "timestamp": datetime.now().isoformat(),
            "user": {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 25 + (i % 50),
                "preferences": {
                    "theme": "dark" if i % 2 else "light",
                    "notifications": True,
                    "language": "en"
                }
            },
            "order": {
                "items": [
                    {"product": f"Product {j}", "quantity": j % 5 + 1, "price": 19.99 + j}
                    for j in range(i % 10 + 1)
                ],
                "total": sum((j % 5 + 1) * (19.99 + j) for j in range(i % 10 + 1)),
                "status": ["pending", "processing", "shipped", "delivered"][i % 4],
                "shipping_address": {
                    "street": f"{i} Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip": f"{90000 + i % 1000:05d}"
                }
            },
            "metadata": {
                "source": ["web", "mobile", "api"][i % 3],
                "campaign": f"campaign_{i % 10}",
                "tags": [f"tag{j}" for j in range(i % 8)],
                "scores": [float(j * 0.1) for j in range(i % 15)]
            }
        }
        for i in range(count)
    ]

def test_serialization_format(format_name, serialize_func, deserialize_func, data):
    """Test a specific serialization format"""
    print(f"\n=== {format_name} Test ===")
    
    # Serialization test
    start_time = time.time()
    serialized_data = []
    total_size = 0
    
    for item in data:
        try:
            serialized = serialize_func(item)
            serialized_data.append(serialized)
            total_size += len(serialized)
        except Exception as e:
            print(f"Serialization error: {e}")
            return None
    
    serialize_time = time.time() - start_time
    
    # Deserialization test
    start_time = time.time()
    deserialized_data = []
    
    for serialized in serialized_data:
        try:
            deserialized = deserialize_func(serialized)
            deserialized_data.append(deserialized)
        except Exception as e:
            print(f"Deserialization error: {e}")
            return None
    
    deserialize_time = time.time() - start_time
    
    # Results
    results = {
        'format': format_name,
        'message_count': len(data),
        'total_size': total_size,
        'avg_size': total_size / len(data),
        'serialize_time': serialize_time,
        'deserialize_time': deserialize_time,
        'total_time': serialize_time + deserialize_time,
        'serialize_rate': len(data) / serialize_time,
        'deserialize_rate': len(data) / deserialize_time
    }
    
    print(f"Messages: {results['message_count']:,}")
    print(f"Total size: {results['total_size']:,} bytes")
    print(f"Average size: {results['avg_size']:.1f} bytes")
    print(f"Serialize time: {results['serialize_time']:.3f}s ({results['serialize_rate']:.0f} msg/s)")
    print(f"Deserialize time: {results['deserialize_time']:.3f}s ({results['deserialize_rate']:.0f} msg/s)")
    print(f"Total time: {results['total_time']:.3f}s")
    
    return results

def rabbitmq_throughput_test(format_name, serialize_func, deserialize_func, data):
    """Test actual RabbitMQ throughput with format"""
    print(f"\n=== {format_name} RabbitMQ Throughput Test ===")
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    queue_name = f'format_test_{format_name.lower()}'
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Producer test
    start_time = time.time()
    total_size = 0
    
    for item in data:
        serialized = serialize_func(item)
        total_size += len(serialized)
        
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=serialized,
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    produce_time = time.time() - start_time
    
    # Consumer test
    messages_received = []
    start_time = time.time()
    
    def callback(ch, method, properties, body):
        message = deserialize_func(body)
        messages_received.append(message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        if len(messages_received) >= len(data):
            ch.stop_consuming()
    
    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()
    
    consume_time = time.time() - start_time
    
    connection.close()
    
    print(f"Produce time: {produce_time:.3f}s ({len(data) / produce_time:.0f} msg/s)")
    print(f"Consume time: {consume_time:.3f}s ({len(messages_received) / consume_time:.0f} msg/s)")
    print(f"Total size: {total_size:,} bytes")
    print(f"Average size: {total_size / len(data):.1f} bytes")

def main():
    print("🔄 Message Format Performance Comparison")
    print("=" * 50)
    
    # Create test data
    data = create_sample_data(500)  # Smaller dataset for demo
    
    # Define formats
    formats = [
        ("JSON", 
         lambda x: json.dumps(x).encode('utf-8'),
         lambda x: json.loads(x.decode('utf-8'))),
        
        ("MessagePack",
         lambda x: msgpack.packb(x),
         lambda x: msgpack.unpackb(x, raw=False)),
        
        ("Pickle",
         lambda x: pickle.dumps(x),
         lambda x: pickle.loads(x))
    ]
    
    # Test serialization performance
    results = []
    for format_name, serialize_func, deserialize_func in formats:
        result = test_serialization_format(format_name, serialize_func, deserialize_func, data)
        if result:
            results.append(result)
    
    # Summary comparison
    print(f"\n{'='*60}")
    print("📊 PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    print(f"{'Format':<12} {'Size (KB)':<10} {'Ser (ms)':<10} {'Deser (ms)':<12} {'Total (ms)':<12}")
    print("-" * 60)
    
    for result in results:
        print(f"{result['format']:<12} "
              f"{result['total_size']/1024:<10.1f} "
              f"{result['serialize_time']*1000:<10.1f} "
              f"{result['deserialize_time']*1000:<12.1f} "
              f"{result['total_time']*1000:<12.1f}")
    
    # Size comparison
    if results:
        json_size = next(r['total_size'] for r in results if r['format'] == 'JSON')
        print(f"\n📏 SIZE COMPARISON (vs JSON):")
        for result in results:
            ratio = result['total_size'] / json_size
            print(f"{result['format']}: {ratio:.1%} of JSON size")
    
    # RabbitMQ throughput test (smaller dataset)
    small_data = data[:50]
    for format_name, serialize_func, deserialize_func in formats:
        rabbitmq_throughput_test(format_name, serialize_func, deserialize_func, small_data)

if __name__ == "__main__":
    main()