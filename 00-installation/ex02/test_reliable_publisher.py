#!/usr/bin/env python3
"""
Reliable Publisher Pattern — RabbitMQ

Two delivery guarantees a publisher needs:
  1. Publisher Confirms: the broker ACKs that the exchange received and stored
     the message (enabled with channel.confirm_delivery()).
  2. Mandatory delivery: the broker returns the message to the publisher if no
     queue is bound to receive it, instead of silently dropping it
     (enabled with mandatory=True on basic_publish).

Together these two flags let a publisher know with certainty that a message
was both accepted by the broker AND routed to at least one queue.

Scenarios covered:
  A. Happy path   — confirm + mandatory, message reaches the queue
  B. Unroutable   — confirm + mandatory, routing key has no binding
  C. Fire-and-forget — no mandatory flag, unroutable message is silently dropped
"""

import sys
import pika
import pika.exceptions
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
AMQP_URL   = "amqp://admin:cluster123@localhost:5672/"
EXCHANGE   = "reliable.direct"
QUEUE      = "reliable.orders"
BOUND_KEY  = "order.created"          # has a queue binding
UNBOUND_KEY = "order.archived"        # no queue binding exists


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def section(title: str) -> None:
    bar = "─" * 60
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


def result(ok: bool, msg: str) -> None:
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {msg}")


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------
class ReliablePublisher:
    """
    Wraps a single pika BlockingConnection with publisher confirms enabled.

    With confirm_delivery() active, basic_publish() blocks until the broker
    sends a basic.ack or basic.nack for that message.

    When mandatory=True and no queue can receive the message, the broker
    sends a basic.return followed by a basic.ack.  Pika captures the return
    and raises UnroutableError so the caller knows delivery failed.
    """

    def __init__(self, url: str) -> None:
        params = pika.URLParameters(url)
        params.heartbeat = 60
        self._conn = pika.BlockingConnection(params)
        self._ch   = self._conn.channel()

        # Turn on publisher confirms for this channel.
        # After this call every basic_publish will wait for an ack/nack.
        self._ch.confirm_delivery()
        print("  Publisher confirms enabled on channel.")

    # ------------------------------------------------------------------
    # Infrastructure setup / teardown
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """Declare the exchange, queue, and one routing-key binding."""
        self._ch.exchange_declare(
            exchange=EXCHANGE,
            exchange_type="direct",
            durable=True,
        )
        self._ch.queue_declare(queue=QUEUE, durable=True)
        self._ch.queue_bind(
            queue=QUEUE,
            exchange=EXCHANGE,
            routing_key=BOUND_KEY,
        )
        print(f"  Exchange '{EXCHANGE}' declared (direct, durable).")
        print(f"  Queue    '{QUEUE}' declared and bound to '{BOUND_KEY}'.")

    def teardown(self) -> None:
        self._ch.queue_delete(queue=QUEUE)
        self._ch.exchange_delete(exchange=EXCHANGE)
        self._conn.close()

    # ------------------------------------------------------------------
    # Core publish method
    # ------------------------------------------------------------------

    def publish(
        self,
        routing_key: str,
        body: str,
        *,
        mandatory: bool = True,
    ) -> None:
        """
        Publish one message and wait for broker confirmation.

        Raises:
            pika.exceptions.UnroutableError – mandatory=True and no queue
                received the message (broker returned it).
            pika.exceptions.NackError – broker explicitly rejected the message.
        """
        self._ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=body.encode(),
            mandatory=mandatory,
            properties=pika.BasicProperties(
                delivery_mode=2,                           # persistent
                content_type="text/plain",
                timestamp=int(datetime.now(timezone.utc).timestamp()),
            ),
        )

    # ------------------------------------------------------------------
    # Verification helper
    # ------------------------------------------------------------------

    def get_one(self, queue: str) -> str | None:
        """
        Pull a single message off the queue without a consumer.
        Returns the decoded body, or None if the queue is empty.
        """
        method, _props, body = self._ch.basic_get(queue=queue, auto_ack=True)
        return body.decode() if body is not None else None


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def scenario_a(pub: ReliablePublisher) -> None:
    """
    Happy path: message is confirmed by the exchange AND routed to the queue.

    After basic_publish returns without raising, we know:
      - The exchange received and durably stored the message  (confirm ACK)
      - At least one queue has the message                    (no return fired)
    """
    section("SCENARIO A — Confirm + mandatory: message delivered to queue")

    body = f"Order #1001 placed at {datetime.now().isoformat()}"

    try:
        pub.publish(routing_key=BOUND_KEY, body=body)

        # basic_publish returned normally → broker ACKed, no return was fired
        result(True, "Broker ACKed the message (Guarantee 1: exchange received it).")

        queued = pub.get_one(QUEUE)
        if queued == body:
            result(True, f"Message found in queue '{QUEUE}' (Guarantee 2: queue received it).")
            print(f"         body: '{queued}'")
        else:
            result(False, f"Queue is empty or body mismatch. Got: {queued!r}")

    except pika.exceptions.UnroutableError:
        result(False, "UnroutableError — message was returned (not expected here).")
    except pika.exceptions.NackError:
        result(False, "NackError — broker rejected the message.")


def scenario_b(pub: ReliablePublisher) -> None:
    """
    Unroutable with mandatory=True.

    The exchange accepts the message (ACK) but has no binding for the routing
    key, so it sends a basic.return back to us before the ACK.  Pika raises
    UnroutableError to signal that the message never reached a queue.

    Without this flag, the exchange would silently discard the message and the
    publisher would never know.
    """
    section("SCENARIO B — Confirm + mandatory: unroutable key, publisher is notified")

    body = "Order #1002 — wrong routing key"

    try:
        pub.publish(routing_key=UNBOUND_KEY, body=body)

        # Reaching here means the message was routed — unexpected for this key
        result(False, "No exception raised (message should have been unroutable).")

    except pika.exceptions.UnroutableError:
        result(True, (
            f"UnroutableError caught — routing key '{UNBOUND_KEY}' "
            f"has no queue binding."
        ))
        result(True, (
            "Publisher was notified of non-delivery. "
            "Without mandatory=True this message would have been silently dropped."
        ))

        queued = pub.get_one(QUEUE)
        result(queued is None, f"Queue is empty — message was correctly NOT delivered.")


def scenario_c(pub: ReliablePublisher) -> None:
    """
    Fire-and-forget (no mandatory flag).

    Even with publisher confirms enabled, setting mandatory=False means the
    broker ACKs the message as soon as the exchange receives it, regardless of
    whether any queue is bound.  An unroutable message is silently discarded.

    This is the default behaviour and should only be used when losing messages
    for unbound keys is acceptable.
    """
    section("SCENARIO C — Confirm only, no mandatory: silent drop on unroutable key")

    body = "Order #1003 — fire and forget"

    try:
        pub.publish(routing_key=UNBOUND_KEY, body=body, mandatory=False)

        result(True, (
            "Broker ACKed (Guarantee 1 met: exchange received it)."
        ))

        queued = pub.get_one(QUEUE)
        if queued is None:
            result(False, (
                "Queue is EMPTY — message was silently dropped by the exchange. "
                "Guarantee 2 is NOT met. This is the risk of fire-and-forget."
            ))
        else:
            result(True, f"Unexpectedly found in queue: '{queued}'")

    except pika.exceptions.NackError:
        result(False, "NackError — broker rejected the message.")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary() -> None:
    section("SUMMARY — When to use each flag")
    print("""
  confirm_delivery() alone
    - Guarantees: exchange received the message
    - Does NOT guarantee: a queue has the message
    - Use when: losing unroutable messages is acceptable

  mandatory=True  (requires confirm_delivery)
    - Guarantees: message is in at least one queue
    - Publisher receives UnroutableError if no queue is bound
    - Use when: every published message MUST reach a queue

  Both together = full end-to-end publisher reliability guarantee.
""")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("  RabbitMQ — Reliable Publisher Pattern")
    print("  Publisher Confirms + Mandatory Delivery")
    print("=" * 60)

    try:
        pub = ReliablePublisher(AMQP_URL)
    except pika.exceptions.AMQPConnectionError as exc:
        print(f"\nCould not connect to RabbitMQ: {exc}")
        print("Is the cluster running?  docker compose up -d")
        return 1

    try:
        pub.setup()
        scenario_a(pub)
        scenario_b(pub)
        scenario_c(pub)
        print_summary()
    finally:
        pub.teardown()
        print("  Exchange and queue cleaned up.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
