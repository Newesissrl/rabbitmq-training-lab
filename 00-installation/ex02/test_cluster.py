#!/usr/bin/env python3
"""
RabbitMQ Cluster Test Script
Tests cluster functionality, HA queues, and failover scenarios.
"""

import pika
import time
import thread6
import sys
from datetime import datetime

class ClusterTester:
    def __init__(self):
        self.nodes = [
            {'host': 'localhost', 'port': 5672, 'name': 'node-1'},
            {'host': 'localhost', 'port': 5673, 'name': 'node-2'},
            {'host': 'localhost', 'port': 5674, 'name': 'node-3'},
            {'host': 'localhost', 'port': 5671, 'name': 'load-balancer'}
        ]
        self.credentials = pika.PlainCredentials('admin', 'cluster123')

    def test_connections(self):
        """Test connection to all cluster nodes"""
        print("🔗 Testing connections to all nodes...")

        for node in self.nodes:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=node['host'],
                        port=node['port'],
                        credentials=self.credentials
                    )
                )
                channel = connection.channel()

                # Test basic operations
                test_queue = f"test_{node['name']}"
                channel.queue_declare(queue=test_queue, durable=True)
                channel.basic_publish(
                    exchange='',
                    routing_key=test_queue,
                    body=f"Test message from {node['name']}",
                    properties=pika.BasicProperties(delivery_mode=2)
                )

                connection.close()
                print(f"  ✅ {node['name']} ({node['host']}:{node['port']}) - OK")

            except Exception as e:
                print(f"  ❌ {node['name']} ({node['host']}:{node['port']}) - FAILED: {e}")

    def create_ha_queue(self):
        """Create a highly available queue"""
        print("\n🏗️  Creating HA queue...")

        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host='localhost',
                    port=5672,
                    credentials=self.credentials
                )
            )
            channel = connection.channel()

            # Declare HA queue
            channel.queue_declare(
                queue='ha_test_queue',
                durable=True,
                arguments={
                    'x-ha-policy': 'all',
                    'x-ha-sync-mode': 'automatic'
                }
            )

            print("  ✅ HA queue 'ha_test_queue' created")
            connection.close()

        except Exception as e:
            print(f"  ❌ Failed to create HA queue: {e}")

    def producer_test(self, duration=30):
        """Run producer test for specified duration"""
        print(f"\n📤 Starting producer test for {duration} seconds...")

        def produce_messages():
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host='localhost',
                        port=5671,  # Use load balancer
                        credentials=self.credentials
                    )
                )
                channel = connection.channel()

                start_time = time.time()
                message_count = 0

                while time.time() - start_time < duration:
                    timestamp = datetime.now().isoformat()
                    message = f"Message {message_count} at {timestamp}"

                    channel.basic_publish(
                        exchange='',
                        routing_key='ha_test_queue',
                        body=message,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )

                    message_count += 1
                    time.sleep(1)

                connection.close()
                print(f"  📊 Sent {message_count} messages")

            except Exception as e:
                print(f"  ❌ Producer error: {e}")

        producer_thread = thread6.Thread(target=produce_messages)
        producer_thread.start()
        return producer_thread

    def consumer_test(self, node_port=5671):
        """Run consumer test"""
        print(f"\n📥 Starting consumer on port {node_port}...")

        def consume_messages():
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host='localhost',
                        port=node_port,
                        credentials=self.credentials
                    )
                )
                channel = connection.channel()

                def callback(ch, method, properties, body):
                    print(f"  📨 Received: {body.decode()}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                channel.basic_consume(
                    queue='ha_test_queue',
                    on_message_callback=callback
                )

                print(f"  🎧 Consumer listening on port {node_port}...")
                channel.start_consuming()

            except KeyboardInterrupt:
                print(f"\n  🛑 Consumer on port {node_port} stopped")
                channel.stop_consuming()
                connection.close()
            except Exception as e:
                print(f"  ❌ Consumer error: {e}")

        consumer_thread = thread6.Thread(target=consume_messages)
        consumer_thread.daemon = True
        consumer_thread.start()
        return consumer_thread

def main():
    tester = ClusterTester()

    print("🐇 RabbitMQ Cluster Test Suite")
    print("=" * 50)

    # Test 1: Connection test
    tester.test_connections()

    # Test 2: Create HA queue
    tester.create_ha_queue()

    # Test 3: Producer/Consumer test
    producer_thread = tester.producer_test(duration=20)
    consumer_thread = tester.consumer_test()

    try:
        # Wait for producer to finish
        producer_thread.join()

        print("\n⏳ Waiting 10 more seconds for message consumption...")
        time.sleep(10)

        print("\n✅ Cluster test completed!")
        print("\n💡 Next steps:")
        print("  1. Check Management UI: http://localhost:15672")
        print("  2. Try stopping a node: docker-compose stop rabbit-2")
        print("  3. Monitor HAProxy stats: http://localhost:8080/stats")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")

    print("\n🏁 Test suite finished")

if __name__ == "__main__":
    main()