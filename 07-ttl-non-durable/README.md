# Exercise 7: Message TTL and Temporary Queues

## Concept
Demonstrates message Time-To-Live (TTL) and temporary (auto-delete) queues:
- Messages with TTL expire and are discarded if not consumed in time
- Auto-delete queues disappear when their last consumer disconnects
- Temporary messaging for ephemeral data

> **RabbitMQ 4.3 note:** non-durable (transient) queues that are shared between
> connections are **rejected** by RabbitMQ 4.3 (`transient_nonexcl_queues` is
> denied by default). Temporary queues are now built with one of:
>
> | Option | Queue is deleted when... |
> |--------|--------------------------|
> | `exclusive=True` | the declaring connection closes |
> | `auto_delete=True` (used here) | the last consumer unsubscribes |
> | `x-expires` argument | the queue has been unused for N ms |
>
> Try it: in a Python shell run
> `channel.queue_declare(queue='old_style', durable=False)` and read the error.

## Learning Objectives
- Understand message TTL behavior
- Learn the RabbitMQ 4.3 options for temporary queues
- Practice temporary messaging patterns
- Observe message expiration in real-time

## Setup
1. Start RabbitMQ (see main README)
2. **First - Run producer only (no consumer):**
   ```bash
   python producer.py  # Declares ttl_queue and sends messages with 5-second TTL
   ```
3. **Wait and observe messages expiring in Web UI** (Queues tab → `ttl_queue`)
4. **Then run consumer to catch messages before expiry:**
   ```bash
   python consumer.py  # Terminal 2 - consumes before TTL expires
   ```
5. Stop the consumer (Ctrl+C) and watch `ttl_queue` disappear

## Message TTL Behavior
- Messages expire after 5 seconds if not consumed
- Expired messages are automatically discarded
- `ttl_queue` is auto-delete: it is removed when the last consumer disconnects
- Once the queue is gone, new messages from the producer are **unroutable** and dropped

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `ttl_exchange` - direct exchange for temporary data

**Queues Tab:**
- `ttl_queue` - features column shows `AD` (auto-delete) and `D` (durable)
- Watch the message count stay low: messages expire after 5 seconds
- Queue disappears when the consumer disconnects

**What You Should See:**
1. **Producer Only:** Messages accumulate, then disappear (TTL expiry)
2. **With Consumer:** Messages consumed before expiration
3. **Consumer Disconnect:** Queue disappears immediately
4. **After that:** The producer keeps publishing, but messages are dropped (no queue bound)

## Experiment Scenarios

### Scenario 1: Message Expiration
1. Start producer only
2. Watch messages accumulate in Web UI
3. Observe messages disappearing after 5 seconds
4. Check queue message count decreasing

### Scenario 2: Successful Consumption
1. Start producer and consumer together
2. Observe messages consumed before TTL expires
3. Check consumer terminal for received messages

### Scenario 3: Component Cleanup
1. Stop consumer (Ctrl+C)
2. Watch `ttl_queue` disappear from Web UI
3. Note that the producer is now publishing into the void (Overview → "Unroutable (drop)" rate)

### Scenario 4 (bonus): Queue TTL instead of auto-delete
Change the queue declaration (in **both** producer and consumer) to use
`arguments={'x-expires': 30000}` instead of `auto_delete=True`. Delete the old
queue first in the UI. The queue now disappears 30 seconds after it was last used.

## Key Differences from Previous Exercises
- **Auto-delete:** Queues clean up automatically
- **TTL:** Messages have an expiration time
- **Temporary:** Designed for ephemeral messaging patterns
