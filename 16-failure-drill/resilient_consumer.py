#!/usr/bin/env python3
"""
Resilient consumer for the failure drill.

- Manual acknowledgements: a message is removed only after it was processed
- Reconnects automatically when the broker restarts
- Tracks message numbers to detect duplicates (redeliveries) and gaps (losses)
- --crash-after N simulates a consumer crash: the process dies after receiving
  N messages, without acknowledging the in-flight ones

Usage: python resilient_consumer.py [--crash-after N] [--prefetch N]
"""
import argparse
import os
import time

import pika
import pika.exceptions

QUEUE = 'drill_orders'
PARAMS = pika.ConnectionParameters(host='localhost', heartbeat=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--crash-after', type=int, default=0, help='simulate a crash after N messages')
    parser.add_argument('--prefetch', type=int, default=10, help='unacknowledged messages in flight')
    args = parser.parse_args()

    seen = set()
    stats = {'received': 0, 'duplicates': 0, 'redelivered': 0}

    def on_message(ch, method, properties, body):
        msg_id = int(properties.message_id)
        stats['received'] += 1
        flags = []
        if method.redelivered:
            stats['redelivered'] += 1
            flags.append('REDELIVERED')
        if msg_id in seen:
            stats['duplicates'] += 1
            flags.append('DUPLICATE')
        seen.add(msg_id)
        print(f" [x] {body.decode()} {' '.join(flags)}")

        if args.crash_after and stats['received'] >= args.crash_after:
            print(f' [💥] Simulated crash after {stats["received"]} messages (no ack for in-flight messages)')
            os._exit(1)      # Hard exit: no ack, no clean connection close

        time.sleep(0.05)     # Simulated processing
        ch.basic_ack(delivery_tag=method.delivery_tag)

    retries = 0
    print(f' [*] Consuming from {QUEUE!r}. Ctrl+C to stop and print the report')
    try:
        while True:
            try:
                connection = pika.BlockingConnection(PARAMS)
                channel = connection.channel()
                channel.queue_declare(queue=QUEUE, durable=True, arguments={'x-queue-type': 'quorum'})
                channel.basic_qos(prefetch_count=args.prefetch)
                channel.basic_consume(queue=QUEUE, on_message_callback=on_message)
                if retries:
                    print(f' [🔁] Reconnected after {retries} attempt(s)')
                retries = 0
                channel.start_consuming()
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.ChannelClosedByBroker,
                    pika.exceptions.StreamLostError,
                    ConnectionError) as e:
                retries += 1
                delay = min(2 ** retries, 10)
                print(f' [!] Connection lost ({type(e).__name__}); retry {retries} in {delay}s')
                time.sleep(delay)
    except KeyboardInterrupt:
        pass

    # Report: with at-least-once delivery we expect no gaps, maybe duplicates
    print('\n' + '=' * 50)
    print(f" Messages received : {stats['received']}")
    print(f" Unique messages   : {len(seen)}")
    print(f" Redelivered flag  : {stats['redelivered']}")
    print(f" Duplicates        : {stats['duplicates']}")
    if seen:
        missing = sorted(set(range(min(seen), max(seen) + 1)) - seen)
        print(f" Range             : #{min(seen)} .. #{max(seen)}")
        print(f" Gaps (lost)       : {missing if missing else 'none'}")
    print('=' * 50)


if __name__ == '__main__':
    main()
