#!/usr/bin/env python3
import asyncio
from rstream import Consumer, AMQPMessage
from rstream.amqp import amqp_decoder

async def main():
    print(' [*] Simple RabbitMQ Streams Consumer')
    print(' [*] Reading from persistent event stream')
    print(' [*] To exit press CTRL+C')
    
    try:
        # Simple consumer setup
        # load_balancer_mode=True is necessary when running RabbitMQ in Docker to avoid
        # hostname resolution issues.
        consumer = Consumer('127.0.0.1', port=5552, username='guest', password='guest', load_balancer_mode=True)
        
        message_count = 0
        
        # The on_message callback now accepts two arguments: the message and its context.
        async def on_message(msg: AMQPMessage, message_context: object):
            nonlocal message_count
            message_count += 1
            
            body = msg.body.decode() if msg.body else 'Empty'
            
            # Access standard properties directly from the `properties` object.
            # rstream returns AMQP strings as bytes, so decode them
            message_id = msg.properties.message_id if msg.properties else 'Unknown'
            if isinstance(message_id, bytes):
                message_id = message_id.decode()
            
            # Access custom metadata from the `application_properties` dictionary.
            # (keys and values of application_properties are bytes too)
            app_props = msg.application_properties or {}
            category = app_props.get(b'category', app_props.get('category', b'unknown'))
            if isinstance(category, bytes):
                category = category.decode()
            
            print(f" [x] Received #{message_count} (ID: {message_id}) [{category}]: {body}")
        
        await consumer.start()
        
        # Simple subscription
        # The `amqp_decoder` is used to decode the raw message bytes into an AMQPMessage object.
        await consumer.subscribe(
            stream='simple_stream',
            callback=on_message,
            decoder=amqp_decoder
        )
        
        print(' [✓] Subscribed to simple_stream')
        print(' [*] Waiting for messages...')
        
        # Run for a limited time or until interrupted
        await consumer.run()
        
    except KeyboardInterrupt:
        print(f'\n [!] Interrupted after processing {message_count} messages')
    except Exception as e:
        print(f' [❌] Error: {e}')
        print(' [!] Make sure RabbitMQ is running and simple_stream exists')
        print(' [!] Run simple_producer.py first to create the stream')
    finally:
        if 'consumer' in locals():
            try:
                await consumer.close()
            except:
                pass

if __name__ == '__main__':
    asyncio.run(main())
