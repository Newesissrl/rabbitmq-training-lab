# Exercise 8: Durability - Persistent vs Non-Persistent

## Concept
Demonstrates what survives a RabbitMQ restart:
- **Durable queues:** Survive RabbitMQ server restarts
- **Persistent messages** (`delivery_mode=2`): Survive restarts in durable queues
- **Non-persistent messages** (`delivery_mode=1`): Lost on restart, even in durable queues
- **Non-durable components:** How RabbitMQ 4.3 treats `durable=False`

> **What changed in RabbitMQ 4.x**
> - RabbitMQ 4.3 stores all metadata (exchanges, queues, bindings, users...) in
>   **Khepri**, a Raft-based on-disk store. Transient (non-durable) entities are
>   being phased out.
> - A **non-durable, non-exclusive queue is rejected** (`transient_nonexcl_queues`
>   is denied by default). The producer shows the error.
> - A **non-durable exchange is still accepted**, but you will observe that it
>   survives a restart.
> - What still matters is **message persistence**: non-persistent messages are
>   dropped on restart.

## Learning Objectives
- Understand queue durability vs message persistence
- Learn message persistence behavior
- Practice disaster recovery scenarios
- Observe data loss vs data preservation
- Learn what RabbitMQ 4.3 changed for transient entities

## Setup Phase 1: Create Components and Messages
1. Start RabbitMQ (see main README)
2. Run producer:
   ```bash
   python producer.py  # Creates exchanges and queue, sends messages, tries a transient queue
   ```
3. **DO NOT start the consumer yet** - we want messages to accumulate

## Setup Phase 2: Observe Before Restart
1. Check Web UI at http://localhost:15672 (guest/guest)
2. `durable_queue` has **7 messages** (5 persistent + 2 non-persistent)
3. `transient_exchange` is listed in the Exchanges tab (features column has no `D`)
4. There is **no** `temp_queue`: the broker refused it (see the producer output)

## Setup Phase 3: Restart RabbitMQ Server
```bash
docker restart rabbitmq
# or
podman restart rabbitmq
```
Wait ~15 seconds until the Web UI is reachable again.

## Setup Phase 4: Observe After Restart
1. Check Web UI again at http://localhost:15672
2. **What You Should See:**
   - `durable_exchange` and `durable_queue` still exist
   - `durable_queue` has **5 messages**: the 2 non-persistent ones are gone
   - `transient_exchange` is **still listed** (RabbitMQ 4.3 / Khepri behaviour)

## Setup Phase 5: Consume Surviving Messages
```bash
python consumer.py  # Consumes only the messages that survived restart
```

## Durability Matrix (RabbitMQ 4.3)

| Queue | Message `delivery_mode` | Survives restart? |
|-------|-------------------------|-------------------|
| durable | 2 (persistent) | ✅ Queue + messages |
| durable | 1 (non-persistent) | ✅ Queue, ❌ messages |
| non-durable, non-exclusive | any | ⛔ Cannot be declared |
| exclusive | any | ❌ Deleted when the connection closes |

| Exchange | Survives restart? |
|----------|-------------------|
| `durable=True` | ✅ |
| `durable=False` | ✅ in practice on 4.3 (do not rely on it; declare exchanges durable) |

> Quorum queues and streams are always durable and always store messages on
> disk; `delivery_mode` only makes a difference for classic queues.

## Experiment Scenarios

### Scenario 1: Full Durability Test
1. Run producer
2. Observe message counts in Web UI
3. Restart RabbitMQ server
4. Compare before/after message counts
5. Run consumer to verify surviving messages

### Scenario 2: Message Persistence Test
1. Modify producer to send only non-persistent messages
2. Restart server
3. Observe that the durable queue is now empty

### Scenario 3: Quorum Queue
1. Change `durable_queue` into a quorum queue: delete it in the UI, then add
   `arguments={'x-queue-type': 'quorum'}` to its declaration in producer **and** consumer
2. Repeat Scenario 2: all 7 messages survive (quorum queues always persist messages)

## Real-World Applications
- **Durable queues + persistent messages:** Critical business data, financial transactions
- **Exclusive / auto-delete queues + non-persistent messages:** Temporary notifications, cache invalidation
- **Persistent messages:** Must survive system failures
- **Non-persistent messages:** Performance over reliability
