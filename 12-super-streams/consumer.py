#!/usr/bin/env python3
import asyncio
from rstream import AMQPMessage
from rstream.superstream_consumer import SuperStreamConsumer
from rstream.amqp import amqp_decoder
from rstream.consumer import MessageContext

# =============================================================================
# RABBITMQ SUPER STREAMS CONSUMER (RABBITMQ 4+ REQUIRED)
# =============================================================================
# This consumer uses the high-level SuperStreamConsumer client from the rstream
# library to consume messages from a partitioned super stream.

# The SuperStreamConsumer handles the following automatically:
# - Discovering all partitions of the super stream.
# - Subscribing to all partitions.
# - Processing messages from all partitions concurrently.

async def main():
    print(' [*] RabbitMQ Super Streams Consumer')
    print(' [*] Processing orders from all partitions')
    print(' [*] To exit press CTRL+C')
    
    try:
        # =============================================================================
        # SUPER STREAM CONSUMER CONNECTION SETUP
        # =============================================================================
        # Use the SuperStreamConsumer as an async context manager.
        # It will connect to the super stream and handle the underlying consumers.
        async with SuperStreamConsumer(
            host='127.0.0.1',
            port=5552,
            username='guest',
            password='guest',
            super_stream='orders_super_stream',
            load_balancer_mode=True  # Necessary for Docker environments.
        ) as consumer:
            
            message_count = 0
            customers_seen = set()

            # =============================================================================
            # PARTITION MESSAGE PROCESSING CALLBACK
            # =============================================================================
            # This callback will be invoked for each message received from any partition.
            async def on_message(msg: AMQPMessage, message_context: MessageContext):
                nonlocal message_count, customers_seen
                message_count += 1
                
                body = msg.body.decode() if msg.body else 'Empty'
                customer_id = msg.application_properties.get('customer_id', 'unknown') if msg.application_properties else 'unknown'
                event_type = msg.application_properties.get('event_type', 'unknown') if msg.application_properties else 'unknown'
                
                customers_seen.add(customer_id)
                
                # Get the partition name from the message context.
                partition = message_context.consumer.get_stream(message_context.subscriber_name)
                
                print(f' [x] Partition {partition} - Message #{message_count}')
                print(f'     Customer: {customer_id} | Event: {event_type}')
                print(f'     Content: {body}')
                print(f'     Customers seen on this consumer: {len(customers_seen)}')
                
                if hasattr(msg, 'offset'):
                    print(f'     Partition Offset: {msg.offset}')
                print()

            # =============================================================================
            # SUPER STREAM SUBSCRIPTION SETUP
            # =============================================================================
            # Subscribe to the super stream. The SuperStreamConsumer will handle
            # subscribing to all partitions.
            await consumer.subscribe(
                callback=on_message,
                decoder=amqp_decoder
            )
            
            print(' [✓] Subscribed to super stream "orders_super_stream"')
            print(' [*] Waiting for messages...')
            
            # Keep the consumer running to process messages.
            await consumer.run()
            
    except KeyboardInterrupt:
        print('\n [!] Consumer interrupted')
    except Exception as e:
        print(f' [❌] Error: {e}')
        print(' [!] Troubleshooting steps:')
        print(' [!] 1. Verify RabbitMQ 4+ is running: docker ps')
        print(' [!] 2. Check stream plugin: docker exec rabbitmq rabbitmq-plugins list | grep stream')
        print(' [!] 3. Check rstream version: pip show rstream')
        print(' [!] 4. Verify port 5552 is exposed: docker port rabbitmq')

if __name__ == '__main__':
    asyncio.run(main())