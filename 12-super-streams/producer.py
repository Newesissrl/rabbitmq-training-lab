#!/usr/bin/env python3
import asyncio
import time
import random
from rstream import AMQPMessage
from rstream.superstream_producer import SuperStreamProducer, RouteType
from rstream.superstream import SuperStreamCreationOption
from rstream._pyamqp.message import Properties

# =============================================================================
# RABBITMQ SUPER STREAMS PRODUCER (RABBITMQ 4.3)
# =============================================================================
# This producer uses the high-level SuperStreamProducer client from the rstream
# library to publish messages to a partitioned super stream.

# The SuperStreamProducer handles the following automatically:
# - Super stream creation with a specified number of partitions.
# - Message routing to partitions based on a routing key.
# - Publishing to the correct partition stream.

# Define a routing extractor function.
# This function is called by the SuperStreamProducer to get the routing key from a message.
async def routing_extractor(message: AMQPMessage):
    # The routing key is extracted from the application_properties of the message.
    return message.application_properties['routing_key']

async def main():
    print(' [*] RabbitMQ Super Streams Producer')
    print(' [*] Publishing to partitioned super stream every 2 seconds')
    print(' [*] Messages routed by customer_id to ensure ordering per customer')
    print(' [*] To exit press CTRL+C')
    
    # Customer IDs used as routing keys for consistent partitioning.
    # All events for the same customer will go to the same partition,
    # guaranteeing order for that customer's events.
    customers = ['customer_001', 'customer_002', 'customer_003', 'customer_004', 'customer_005']
    
    order_events = [
        'order_created',
        'payment_processed',
        'order_shipped',
        'order_delivered',
        'order_cancelled'
    ]
    
    try:
        # =============================================================================
        # SUPER STREAM PRODUCER CONNECTION SETUP
        # =============================================================================
        # Define the super stream creation options.
        # This will create a super stream with 3 partitions if it doesn't exist.
        super_stream_creation_option = SuperStreamCreationOption(n_partitions=3)
        
        # Use the SuperStreamProducer as an async context manager.
        async with SuperStreamProducer(
            host='127.0.0.1',
            port=5552,
            username='guest',
            password='guest',
            super_stream='orders_super_stream',
            super_stream_creation_option=super_stream_creation_option,
            routing_extractor=routing_extractor,
            routing=RouteType.Hash,  # Use hash-based routing strategy.
            load_balancer_mode=True  # Necessary for Docker environments.
        ) as producer:
            
            print(' [✓] Super stream "orders_super_stream" ready with 3 partitions')
            
            # =============================================================================
            # PARTITIONED MESSAGE PUBLISHING LOOP
            # =============================================================================
            order_id = 1
            while True:
                customer_id = random.choice(customers)
                event_type = random.choice(order_events)
                timestamp = int(time.time() * 1000)
                
                # The routing_key will be used by the routing_extractor.
                routing_key = customer_id
                
                event_data = f'{event_type}:order_{order_id}'
                
                # Create the AMQP message with properties and application_properties.
                message = AMQPMessage(
                    body=f'{event_data}|timestamp:{timestamp}'.encode(),
                    properties=Properties(
                        message_id=str(order_id),
                        creation_time=timestamp
                    ),
                    application_properties={
                        'customer_id': customer_id,
                        'event_type': event_type,
                        'routing_key': routing_key
                    }
                )
                
                # The SuperStreamProducer's send method handles routing automatically.
                await producer.send(message)
                print(f" [x] Sent [{customer_id}]: {event_data}")
                
                order_id += 1
                await asyncio.sleep(2)
                
    except KeyboardInterrupt:
        print('\n [!] Interrupted')
    except Exception as e:
        print(f' [❌] Error: {e}')
        print(' [!] Troubleshooting steps:')
        print(' [!] 1. Verify RabbitMQ is running: docker ps')
        print(' [!] 2. Check stream plugin: docker exec rabbitmq rabbitmq-plugins list | grep stream')
        print(' [!] 3. Check rstream version: pip show rstream')
        print(' [!] 4. Verify port 5552 is exposed: docker port rabbitmq')

if __name__ == '__main__':
    asyncio.run(main())