#!/usr/bin/env python3
import asyncio
import os
import sys
from rstream import AMQPMessage
from rstream.superstream_consumer import SuperStreamConsumer
from rstream.amqp import amqp_decoder
from rstream.consumer import MessageContext, EventContext
from rstream import OffsetSpecification, OffsetType

# =============================================================================
# RABBITMQ SUPER STREAMS CONSUMER (RABBITMQ 4.3)
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
                # rstream returns AMQP strings as bytes (keys and values)
                props = msg.application_properties or {}
                def prop(key):
                    value = props.get(key.encode(), props.get(key, b'unknown'))
                    return value.decode() if isinstance(value, bytes) else value
                customer_id = prop('customer_id')
                event_type = prop('event_type')

                customers_seen.add(customer_id)

                # The message context tells us which partition (stream) the
                # message came from and its offset inside that partition.
                partition = message_context.stream

                print(f' [x] Partition {partition} - Message #{message_count}')
                print(f'     Customer: {customer_id} | Event: {event_type}')
                print(f'     Content: {body}')
                print(f'     Customers seen on this consumer: {len(customers_seen)}')
                print(f'     Partition Offset: {message_context.offset}')
                print()

            # =============================================================================
            # SUPER STREAM SUBSCRIPTION SETUP
            # =============================================================================
            # Subscribe to the super stream. The SuperStreamConsumer will handle
            # subscribing to all partitions.
            # With --sac, every consumer instance joins the same consumer group
            # ("orders-app") with Single Active Consumer enabled: the broker
            # then gives each partition to only ONE instance of the group, so
            # running consumer.py several times spreads the partitions over the
            # instances. Without --sac, every instance reads every partition.
            properties = None
            update_listener = None
            if '--sac' in sys.argv:
                properties = {
                    'single-active-consumer': 'true',
                    'name': 'orders-app',                   # consumer group name
                    'super-stream': 'orders_super_stream',  # rebalance partitions across the group
                }
                print(' [*] Single Active Consumer enabled (group "orders-app")')

                # Called by the broker when this instance becomes active (or
                # inactive) for a partition: we answer with the offset to
                # resume from. A real application would return the last offset
                # it stored; here we simply continue with new messages.
                async def update_listener(is_active: bool, event_context: EventContext):
                    state = 'ACTIVE' if is_active else 'standby'
                    print(f' [~] {event_context.subscriber_name}: now {state}')
                    return OffsetSpecification(OffsetType.NEXT, 0)

            await consumer.subscribe(
                callback=on_message,
                decoder=amqp_decoder,
                properties=properties,
                consumer_update_listener=update_listener,
                subscriber_name=f'orders-app-{os.getpid()}'
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
        print(' [!] 1. Verify RabbitMQ is running: docker ps')
        print(' [!] 2. Check stream plugin: docker exec rabbitmq rabbitmq-plugins list | grep stream')
        print(' [!] 3. Check rstream version: pip show rstream')
        print(' [!] 4. Verify port 5552 is exposed: docker port rabbitmq')

if __name__ == '__main__':
    asyncio.run(main())