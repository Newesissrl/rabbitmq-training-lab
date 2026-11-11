# Exercise 9: Exchange-to-Exchange Binding

## Concept
Demonstrates exchange-to-exchange binding to feed two processing paths from a single publish:
- **Source Exchange (`live_exchange`):** Producers publish here; real-time consumers attach temporary queues
- **Target Exchange (`archive_exchange`):** Receives a copy of every message for reliable, persistent storage
- **Message Flow:** Producer → live_exchange → archive_exchange → archive_queue
- **Use Case:** Real-time processing with a backup/audit trail

## Learning Objectives
- Understand exchange-to-exchange binding
- Learn message duplication across processing paths
- Compare exclusive (temporary) queues with durable queues
- Observe message preservation strategies

## Architecture
```
Producer → live_exchange (fanout) ──e2e binding──→ archive_exchange (fanout)
                ↓                                          ↓
     exclusive queue (amq.gen-…)                    archive_queue (durable)
                ↓                                          ↓
         live consumer(s)                           archive consumer
     (real-time, only while connected)          (reliable, nothing is missed)
```

> **RabbitMQ 4.3 note:** older versions of this exercise used a non-durable
> `temp_queue`. RabbitMQ 4.3 rejects non-durable shared queues, so the live
> path now uses an **exclusive, server-named queue** per consumer: it exists only
> while the consumer is connected, which is exactly the "fast, temporary"
> behaviour we want.

## Setup
1. Start RabbitMQ (see main README)
2. Run producer to create exchanges and bindings:
   ```bash
   python producer.py  # Creates both exchanges, the e2e binding and archive_queue
   ```
3. Run consumers in separate terminals:
   ```bash
   python consumer.py live     # Terminal 2 - real-time processing
   python consumer.py archive  # Terminal 3 - reliable archive processing
   ```
4. Start a second `python consumer.py live`: each live consumer gets its own copy

## Message Flow Behavior
- Producer sends only to `live_exchange`
- Messages automatically copied to `archive_exchange`
- Every live consumer and the archive consumer receive identical messages
- Live consumer processes data quickly (100 ms)
- Archive consumer processes data slowly (1 s), so archive_queue builds a backlog

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `live_exchange` - source exchange
- `archive_exchange` - target exchange
- Click `live_exchange` → see binding to `archive_exchange` and to the `amq.gen-…` queues

**Queues Tab:**
- `amq.gen-…` queues (features `Excl`) - one per live consumer
- `archive_queue` (features `D`) - reliable storage

**What You Should See:**
- Exchange-to-exchange binding in live_exchange bindings
- Messages appear in all queues simultaneously
- Exclusive queues disappear when a live consumer is stopped

## Durability Test
**Test message preservation across a restart:**

1. **Send messages** with producer running and both consumers running
2. **Stop both consumers** (Ctrl+C), let the producer run for ~30 seconds, then stop it
3. **Check the Web UI:** the live `amq.gen-…` queue is already gone; `archive_queue` has a backlog
4. **Restart RabbitMQ server:**
   ```bash
   docker restart rabbitmq
   ```
5. **Check Web UI after restart:** `archive_queue` and its persistent messages are still there
6. **Run archive consumer** to process surviving messages:
   ```bash
   python consumer.py archive
   ```

## Real-World Applications

**Real-time + Reliable Pattern:**
- **Live path:** Real-time dashboards, notifications, cache updates
- **Archive path:** Audit logs, compliance records, analytics

**Examples:**
- **E-commerce:** Live order dashboard + reliable order history
- **IoT:** Real-time alerts + long-term sensor data storage
- **Financial:** Immediate transaction response + audit trail
- **Logging:** Live log tail + persistent log storage

## Key Benefits
- **Performance:** Live path does not accumulate a backlog
- **Reliability:** Archive path keeps every message
- **Flexibility:** Different processing logic per path
- **Compliance:** Automatic audit trail creation
