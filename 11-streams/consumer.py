#!/usr/bin/env python3
import asyncio
import sys
from rstream import Consumer, AMQPMessage, OffsetType
from rstream.amqp import amqp_decoder

# =============================================================================
# RABBITMQ STREAMS CONSUMER (RABBITMQ 4+ REQUIRED)
# =============================================================================
# Stream consumers can read from any offset in the persistent log
# Multiple consumers can read independently without affecting each other
# Supports filtering and replay capabilities

async def main():
    # =============================================================================
    # COMMAND LINE ARGUMENT PARSING
    # =============================================================================
    # Parse offset and filtering options for stream consumption
    offset_type = OffsetType.FIRST  # Default: read from beginning of stream
    filter_category = None          # Default: no filtering
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--offset' and i + 1 < len(sys.argv):
            if sys.argv[i + 1] == 'latest':
                offset_type = OffsetType.NEXT  # Start from new messages only
                print(' [*] Consumer starting from LATEST messages only')
            elif sys.argv[i + 1] == 'first':
                offset_type = OffsetType.FIRST  # Start from beginning (full replay)
                print(' [*] Consumer starting from FIRST message (full replay)')
            i += 2
        elif sys.argv[i] == '--filter' and i + 1 < len(sys.argv):
            filter_category = sys.argv[i + 1]  # Filter by message category
            print(f' [*] Consumer filtering for category: {filter_category}')
            i += 2
        else:
            print("Usage: python consumer.py [--offset latest|first] [--filter category]")
            print("Examples:")
            print("  python consumer.py --filter error      # Only error events")
            print("  python consumer.py --offset latest     # Only new events")
            print("  python consumer.py --offset latest --filter payment  # New payment events")
            return
    
    if not filter_category:
        print(' [*] Consumer starting from FIRST message (full replay, no filtering)')
    
    print(' [*] RabbitMQ Streams Consumer (RabbitMQ 4+ required)')
    print(' [*] Reading from persistent event stream')
    print(' [*] Messages are never deleted - can replay from any offset')
    print(' [*] To exit press CTRL+C')
    
    consumer = None
    try:
        # =============================================================================
        # STREAM CONSUMER CONNECTION SETUP
        # =============================================================================
        # Create async consumer connection to RabbitMQ Streams.
        # Uses Stream protocol (port 5552) instead of AMQP (port 5672).
        # load_balancer_mode=True is necessary when running RabbitMQ in Docker to avoid
        # hostname resolution issues.
        consumer = Consumer(
            host='127.0.0.1',
            port=5552,              # Stream protocol port
            username='guest',
            password='guest',
            load_balancer_mode=True
        )
        
        message_count = 0
        
        # =============================================================================
        # STREAM MESSAGE PROCESSING CALLBACK
        # =============================================================================
        # The on_message callback now accepts two arguments: the message and its context.
        async def on_message(msg: AMQPMessage, message_context: object):
            """Process messages from the persistent stream"""
            nonlocal message_count
            
            # Extract message content and metadata
            body = msg.body.decode() if msg.body else 'Empty'
            
            # Access standard properties directly from the `properties` object.
            message_id = msg.properties.message_id if msg.properties else 'Unknown'
            timestamp = msg.properties.creation_time if msg.properties else 0
            
            # Access custom metadata from the `application_properties` dictionary.
            category = msg.application_properties.get('category', 'unknown') if msg.application_properties else 'unknown'
            
            # Apply client-side filtering if server-side filtering not available
            # In production, server-side filtering is more efficient
            if filter_category and category != filter_category:
                return  # Skip this message
            
            message_count += 1
            print(f" [x] Received #{message_count} (ID: {message_id}) [{category}]: {body}")
            
            # Show stream offset for this message
            # Offset represents position in the append-only log
            if hasattr(msg, 'offset'):
                print(f"     Stream Offset: {msg.offset}")
        
        # =============================================================================
        # STREAM SUBSCRIPTION SETUP
        # =============================================================================
        # Start the stream consumer
        await consumer.start()
        
        # Subscribe to the persistent stream.
        # The `amqp_decoder` is used to decode the raw message bytes into an AMQPMessage object.
        try:
            # Try modern API first
            if offset_type == OffsetType.FIRST:
                await consumer.subscribe(
                    stream='events_stream',
                    callback=on_message,
                    offset_specification=consumer.offset_specification().first(),
                    decoder=amqp_decoder
                )
            else:
                await consumer.subscribe(
                    stream='events_stream',
                    callback=on_message,
                    offset_specification=consumer.offset_specification().next(),
                    decoder=amqp_decoder
                )
        except (TypeError, AttributeError):
            # Fallback to simpler API
            await consumer.subscribe(
                stream='events_stream',
                callback=on_message,
                decoder=amqp_decoder
            )
            print(' [!] Using basic subscription (offset control not available)')
        
        print(' [✓] Subscribed to events_stream')
        print(' [*] Waiting for messages...')
        print(' [*] Stream messages are persistent - can replay anytime')
        if filter_category:
            print(f' [*] Client-side filtering for category: {filter_category}')
        
        # =============================================================================
        # START STREAM CONSUMPTION
        # =============================================================================
        # Keep consumer running to process stream messages
        # Consumer tracks its offset independently of other consumers
        await consumer.run()
        
    except KeyboardInterrupt:
        print(f'\n [!] Interrupted after processing {message_count} messages')
    except ConnectionResetError as e:
        print(f' [❌] Connection Reset Error: {e}')
        print(' [!] RabbitMQ Streams connection was reset. Possible causes:')
        print(' [!] 1. RabbitMQ server is not running')
        print(' [!] 2. Using RabbitMQ 3.x instead of 4.x (streams not supported)')
        print(' [!] 3. Stream plugin not enabled: docker exec rabbitmq rabbitmq-plugins enable rabbitmq_stream')
        print(' [!] 4. Port 5552 not accessible or blocked')
        print(' [!] 5. Stream does not exist (run producer first)')
    except Exception as e:
        print(f' [❌] Error: {e}')
        print(' [!] Troubleshooting steps:')
        print(' [!] 1. Verify RabbitMQ 4+ is running: docker ps')
        print(' [!] 2. Check stream plugin: docker exec rabbitmq rabbitmq-plugins list | grep stream')
        print(' [!] 3. Verify stream exists: run producer first')
        print(' [!] 4. Check rstream version: pip show rstream')
    finally:
        if consumer is not None:
            try:
                await consumer.close()
            except:
                pass  # Ignore cleanup errors

if __name__ == '__main__':
    asyncio.run(main())
