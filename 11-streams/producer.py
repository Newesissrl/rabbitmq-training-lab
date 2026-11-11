#!/usr/bin/env python3
import asyncio
import time
import random
from rstream import Producer, AMQPMessage
from rstream._pyamqp.message import Properties

# =============================================================================
# RABBITMQ STREAMS PRODUCER (RABBITMQ 4.3)
# =============================================================================
# Streams are append-only logs that persist messages permanently
# Unlike traditional queues, messages are never deleted after consumption
# Multiple consumers can read from different offsets independently

# =============================================================================
# FILTER VALUE EXTRACTOR (server-side filtering)
# =============================================================================
# Every message is published with a "filter value" (here: its category).
# Consumers can then ask the broker to send only the chunks that contain the
# values they are interested in (see consumer.py --filter).
async def filter_value_extractor(message: AMQPMessage) -> str:
    return message.application_properties['category']


async def main():
    print(' [*] RabbitMQ Streams Producer')
    print(' [*] Publishing events to persistent stream every 2 seconds')
    print(' [*] Messages stored permanently in append-only log')
    print(' [*] To exit press CTRL+C')
    
    # =============================================================================
    # EVENT TEMPLATES WITH CATEGORIES FOR STREAM FILTERING
    # =============================================================================
    # Events represent business activities that should be stored permanently
    # Categories enable server-side filtering for selective consumption
    events = [
        ('user_registered:user_{}', 'user'),           # User lifecycle events
        ('order_created:order_{}', 'order'),           # Order management events
        ('payment_processed:payment_{}', 'payment'),   # Successful payment events
        ('payment_failed:payment_{}', 'payment'),      # Failed payment events
        ('inventory_updated:product_{}', 'inventory'), # Inventory change events
        ('user_login:session_{}', 'user'),             # User authentication events
        ('system_error:error_{}', 'error'),            # System error events
        ('database_error:db_{}', 'error'),             # Database error events
        ('email_sent:notification_{}', 'notification'), # Communication events
        ('report_generated:report_{}', 'report')       # Reporting events
    ]
    
    try:
        # =============================================================================
        # STREAM PRODUCER CONNECTION SETUP
        # =============================================================================
        # Create async producer connection to RabbitMQ Streams.
        # Uses Stream protocol (port 5552) instead of AMQP (port 5672).
        # load_balancer_mode=True is necessary when running RabbitMQ in Docker to avoid
        # hostname resolution issues.
        async with Producer(
            '127.0.0.1',
            port=5552,
            username='guest',
            password='guest',
            load_balancer_mode=True,
            filter_value_extractor=filter_value_extractor,
        ) as producer:
            
            # =============================================================================
            # STREAM CREATION
            # =============================================================================
            # Create persistent stream if it doesn't exist.
            # Streams are append-only logs that store messages permanently.
            await producer.create_stream('events_stream', exists_ok=True)
            print(' [✓] Stream "events_stream" ready')
            
            # =============================================================================
            # CONTINUOUS EVENT PUBLISHING TO STREAM
            # =============================================================================
            event_id = 1
            while True:
                # Select random event template with category
                event_template, category = random.choice(events)
                event_data = event_template.format(event_id)
                timestamp = int(time.time() * 1000)  # Milliseconds since epoch
                
                # Create an AMQP message with metadata.
                # Standard properties (like message_id, creation_time) go into the `properties`
                # field, which must be a `Properties` object.
                # Custom metadata (like category) goes into `application_properties`.
                message = AMQPMessage(
                    body=f"{event_data}|timestamp:{timestamp}".encode(),
                    properties=Properties(
                        message_id=str(event_id),
                        creation_time=timestamp,
                        content_type='text/plain',
                    ),
                    application_properties={
                        'category': category
                    }
                )
                
                # Publish event to persistent stream.
                # Message will be stored permanently in the append-only log.
                await producer.send('events_stream', message)
                print(f" [x] Published event #{event_id} [{category}]: {event_data}")
                
                event_id += 1
                await asyncio.sleep(2)  # Publish every 2 seconds
                
    except KeyboardInterrupt:
        print('\n [!] Interrupted')
    except Exception as e:
        print(f' [❌] Error: {e}')
        print(' [!] Make sure RabbitMQ is running with the rabbitmq_stream plugin enabled')
        print(' [!] Verify rstream library is installed: pip install -r requirements.txt')
        print(' [!] Check that stream protocol port 5552 is accessible')

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == '__main__':
    # Run async stream producer
    asyncio.run(main())
