# Exercise 2: Fanout Exchange

## Concept
Fanout exchanges broadcast messages to all bound queues, ignoring routing keys.

## Learning Objectives
- Understand broadcast messaging
- Learn fanout exchange behavior
- Practice pub/sub pattern

## Setup
1. Start RabbitMQ container (see main README)
2. Run multiple consumers (no parameters needed):
   ```bash
   python consumer.py  # Terminal 1 - creates unique queue
   python consumer.py  # Terminal 2 - creates unique queue
   python consumer.py  # Terminal 3 - creates unique queue
   ```
3. Run producer (no parameters needed): `python producer.py`

## Expected Behavior
- All consumers receive every message
- Routing keys are ignored
- Perfect for broadcasting announcements

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `notifications` exchange with type "fanout"
- Click exchange name → see all queue bindings (routing key shows queue name)

**Queues Tab:**
- Multiple auto-generated queues (amq.gen-xxx)
- All queues receive identical message counts
- Each consumer has its own exclusive queue

**What You Should See:**
- All queues bound to fanout exchange (routing key displays queue name)
- Every message delivered to ALL queues simultaneously
- Identical message rates across all consumer queues
- Routing keys are displayed but IGNORED by fanout exchange

**Routing Key Convention:**
- UI shows routing key = queue name (RabbitMQ internal convention)
- Fanout exchanges completely ignore routing key values
- Messages are copied to ALL bound queues regardless of routing key
- Any routing key value would work the same way

## Late Consumer Behavior
**What happens to messages sent before a consumer starts?**

**Current Setup (Exclusive Queues):**
- Consumer creates exclusive, auto-delete queue
- Queue exists ONLY while consumer is connected
- Messages sent before consumer starts are LOST
- No message persistence for late joiners

**Alternative Options for Message Persistence:**

1. **Named Durable Queues:**
   ```python
   channel.queue_declare(queue='notifications_service_a', durable=True)
   ```
   - Queue survives consumer disconnection
   - Messages accumulate for offline consumers
   - Consumer gets all messages when reconnecting

2. **Shared Queues:**
   ```python
   channel.queue_declare(queue='shared_notifications', durable=True)
   ```
   - Multiple consumers share same queue
   - Load balancing instead of broadcasting
   - Each message consumed by only one consumer

3. **Topic Exchange Alternative:**
   - Use topic exchange with wildcard patterns
   - Allows selective subscription with persistence
   - More flexible than fanout for complex scenarios

## Experiment
- Start 3-4 consumers and observe queue creation
- **Test Late Consumer:** Start producer first, then add consumer later
- Watch all queues receive every broadcast message
- Compare message counts - should be identical across queues
- **Observe:** Late consumer misses messages sent before it started