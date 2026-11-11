#!/usr/bin/env python3
import asyncio
import sys
from rstream import (
    Consumer,
    AMQPMessage,
    ConsumerOffsetSpecification,
    FilterConfiguration,
    OffsetType,
)
from rstream.amqp import amqp_decoder

# =============================================================================
# RABBITMQ STREAMS CONSUMER (RABBITMQ 4.3)
# =============================================================================
# Stream consumers can read from any offset in the persistent log
# Multiple consumers can read independently without affecting each other
# Supports server-side filtering and replay capabilities

USAGE = """Usage: python consumer.py [--offset first|last|next|<number>] [--filter category]
Examples:
  python consumer.py                      # Full replay from the first message
  python consumer.py --offset next        # Only new events (alias: latest)
  python consumer.py --offset 5           # Start at offset 5
  python consumer.py --filter error       # Only error events (server-side filter)
  python consumer.py --offset next --filter payment"""


def text(value):
    """rstream returns AMQP strings as bytes: decode them for printing."""
    if isinstance(value, bytes):
        return value.decode()
    return value if value is not None else 'unknown'


def app_prop(msg: AMQPMessage, key: str):
    """Read an application property (keys may be str or bytes)."""
    props = msg.application_properties or {}
    return text(props.get(key, props.get(key.encode())))


def parse_args():
    """Parse --offset and --filter options."""
    offset = ConsumerOffsetSpecification(OffsetType.FIRST)  # Default: full replay
    filter_category = None
    args = sys.argv[1:]
    while args:
        option = args.pop(0)
        if option == '--offset' and args:
            value = args.pop(0)
            if value == 'first':
                offset = ConsumerOffsetSpecification(OffsetType.FIRST)
            elif value == 'last':
                # LAST = start at the last chunk written to the stream
                offset = ConsumerOffsetSpecification(OffsetType.LAST)
            elif value in ('next', 'latest'):
                # NEXT = only messages published after we subscribe
                offset = ConsumerOffsetSpecification(OffsetType.NEXT)
            elif value.isdigit():
                offset = ConsumerOffsetSpecification(OffsetType.OFFSET, int(value))
            else:
                raise SystemExit(USAGE)
            print(f' [*] Offset specification: {value}')
        elif option == '--filter' and args:
            filter_category = args.pop(0)
            print(f' [*] Server-side filter on category: {filter_category}')
        else:
            raise SystemExit(USAGE)
    return offset, filter_category


async def main():
    offset, filter_category = parse_args()

    print(' [*] RabbitMQ Streams Consumer')
    print(' [*] Reading from persistent event stream')
    print(' [*] Messages are never deleted by consumers - can replay from any offset')
    print(' [*] To exit press CTRL+C')

    message_count = 0

    # =============================================================================
    # STREAM MESSAGE PROCESSING CALLBACK
    # =============================================================================
    # The callback receives the decoded message and its context (offset, ...)
    async def on_message(msg: AMQPMessage, message_context):
        nonlocal message_count
        message_count += 1

        body = msg.body.decode() if msg.body else 'Empty'
        message_id = text(msg.properties.message_id) if msg.properties else 'unknown'
        category = app_prop(msg, 'category')

        print(f" [x] Received #{message_count} (ID: {message_id}) [{category}]: {body}")
        # Offset = position of the message in the append-only log
        print(f"     Stream Offset: {message_context.offset}")

    # =============================================================================
    # SERVER-SIDE FILTERING (optional)
    # =============================================================================
    # The producer attaches a "filter value" (the category) to every message.
    # The broker uses it to skip whole chunks that contain no matching value,
    # which saves network bandwidth. Because filtering works per chunk, the
    # client still applies a predicate to drop the few non-matching messages
    # that may arrive in a matching chunk.
    filter_input = None
    if filter_category:
        filter_input = FilterConfiguration(
            values_to_filter=[filter_category],
            predicate=lambda m: app_prop(m, 'category') == filter_category,
            match_unfiltered=False,  # Ignore messages published without a filter value
        )

    # =============================================================================
    # STREAM CONSUMER CONNECTION SETUP
    # =============================================================================
    # Uses the Stream protocol (port 5552) instead of AMQP (port 5672).
    # load_balancer_mode=True keeps using the address we connect to, instead of
    # the host name advertised by the broker (useful with Docker).
    async with Consumer(
        host='127.0.0.1',
        port=5552,
        username='guest',
        password='guest',
        load_balancer_mode=True,
    ) as consumer:
        await consumer.subscribe(
            stream='events_stream',
            callback=on_message,
            decoder=amqp_decoder,           # Decode raw bytes into an AMQPMessage
            offset_specification=offset,
            filter_input=filter_input,
        )
        print(' [✓] Subscribed to events_stream')
        print(' [*] Waiting for messages...')

        # Keep consumer running to process stream messages
        await consumer.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n [!] Interrupted')
    except Exception as e:
        print(f' [❌] Error: {e}')
        print(' [!] Troubleshooting steps:')
        print(' [!] 1. Verify RabbitMQ is running: docker ps')
        print(' [!] 2. Check stream plugin: docker exec rabbitmq rabbitmq-plugins list | grep stream')
        print(' [!] 3. Verify stream exists: run producer first')
        print(' [!] 4. Check port 5552 is reachable: docker port rabbitmq 5552')
