#!/usr/bin/env python3
import asyncio
import time
import random
from rstream import Producer, AMQPMessage
from rstream._pyamqp.message import Properties

async def main():
    print(' [*] Simple RabbitMQ Streams Producer')
    print(' [*] Publishing events to persistent stream')
    print(' [*] To exit press CTRL+C')
    
    # Simple event templates
    events = [
        ('user_event', 'user'),
        ('order_event', 'order'), 
        ('payment_event', 'payment'),
        ('error_event', 'error')
    ]
    
    try:
        # Simple producer setup
        # load_balancer_mode=True is necessary when running RabbitMQ in Docker to avoid
        # hostname resolution issues.
        producer = Producer('127.0.0.1', port=5552, username='guest', password='guest', load_balancer_mode=True)
        await producer.start()
        
        # Create stream
        await producer.create_stream('simple_stream', exists_ok=True)
        print(' [✓] Stream "simple_stream" ready')
        
        event_id = 1
        for _ in range(10):  # Send 10 messages then exit
            event_template, category = random.choice(events)
            event_data = f"{event_template}_{event_id}"
            
            # Create an AMQP message.
            # Standard properties (like message_id) go into the `properties` field,
            # which must be a `Properties` object.
            # Custom metadata (like category) goes into `application_properties`.
            message = AMQPMessage(
                body=event_data.encode(),
                properties=Properties(message_id=str(event_id)),
                application_properties={'category': category}
            )
            
            # Send message
            await producer.send('simple_stream', message)
            print(f" [x] Sent event #{event_id} [{category}]: {event_data}")
            
            event_id += 1
            await asyncio.sleep(1)
        
        await producer.close()
        print(' [✓] Producer finished successfully')
        
    except Exception as e:
        print(f' [❌] Error: {e}')
        print(' [!] Make sure RabbitMQ is running with the rabbitmq_stream plugin enabled')

if __name__ == '__main__':
    asyncio.run(main())
