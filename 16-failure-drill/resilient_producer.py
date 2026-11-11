#!/usr/bin/env python3
"""
Resilient producer for the failure drill.

- Publishes numbered, persistent messages to a quorum queue
- Uses publisher confirms: a message counts as "sent" only when the broker
  confirmed it
- Reconnects automatically (with backoff) when the broker restarts
- Reports when the broker BLOCKS publishers because of a resource alarm

Usage: python resilient_producer.py [--count N] [--rate MSG_PER_SEC]
"""
import argparse
import time

import pika
import pika.exceptions

QUEUE = 'drill_orders'
PARAMS = pika.ConnectionParameters(
    host='localhost',
    heartbeat=10,                  # Detect dead connections quickly
    blocked_connection_timeout=None,
)


def connect():
    """Open a connection + confirm channel and declare the quorum queue."""
    connection = pika.BlockingConnection(PARAMS)

    # Called when the broker blocks/unblocks publishers (memory or disk alarm)
    connection.add_on_connection_blocked_callback(
        lambda *_: print(' [⛔] Connection BLOCKED by the broker (resource alarm) - publishing paused'))
    connection.add_on_connection_unblocked_callback(
        lambda *_: print(' [✅] Connection UNBLOCKED - publishing resumes'))

    channel = connection.channel()
    channel.confirm_delivery()     # basic_publish now waits for the broker ack
    # Quorum queue: replicated, always durable, messages always persisted
    channel.queue_declare(queue=QUEUE, durable=True, arguments={'x-queue-type': 'quorum'})
    return connection, channel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=0, help='messages to send (0 = forever)')
    parser.add_argument('--rate', type=float, default=5, help='messages per second')
    args = parser.parse_args()

    seq = 1             # Next message number to publish
    retries = 0
    connection = None
    print(f' [*] Publishing to quorum queue {QUEUE!r}. Ctrl+C to stop')

    try:
        while args.count == 0 or seq <= args.count:
            try:
                if connection is None or connection.is_closed:
                    connection, channel = connect()
                    if retries:
                        print(f' [🔁] Reconnected after {retries} attempt(s), resuming at #{seq}')
                    retries = 0

                channel.basic_publish(
                    exchange='',
                    routing_key=QUEUE,
                    body=f'order #{seq}',
                    properties=pika.BasicProperties(message_id=str(seq), delivery_mode=2),
                )
                # Reaching this line means the broker confirmed the message
                print(f' [x] Confirmed #{seq}')
                seq += 1
                # connection.sleep() (unlike time.sleep) keeps processing broker
                # events, so heartbeats and blocked/unblocked notifications work
                connection.sleep(1 / args.rate)

            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.ChannelClosedByBroker,
                    pika.exceptions.StreamLostError,
                    ConnectionError) as e:
                # The message #seq was NOT confirmed: it will be published again
                # after reconnecting (at-least-once delivery -> possible duplicate)
                retries += 1
                delay = min(2 ** retries, 10)
                print(f' [!] Connection lost ({type(e).__name__}); retry {retries} in {delay}s')
                connection = None
                time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        print(f'\n [*] Last confirmed message: #{seq - 1}')
        if connection is not None and connection.is_open:
            connection.close()


if __name__ == '__main__':
    main()
