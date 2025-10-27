# Exercise 8: Durability - Persistent vs Non-Persistent Components

## Concept
Demonstrates the difference between durable and non-durable exchanges, queues, and messages:
- **Durable:** Survive RabbitMQ server restarts
- **Non-durable:** Lost when RabbitMQ server restarts
- **Persistent messages:** Survive restarts in durable queues
- **Non-persistent messages:** Lost on restart even in durable queues

## Learning Objectives
- Understand durability vs non-durability
- Learn message persistence behavior
- Practice disaster recovery scenarios
- Observe data loss vs data preservation

## Setup Phase 1: Create Components and Messages
1. Start RabbitMQ container (see main README)
2. Run producer to create both durable and non-durable components:
   ```bash
   python producer.py  # Creates exchanges, queues, and sends messages
   ```
3. **DO NOT start consumers yet** - we want messages to accumulate

## Setup Phase 2: Observe Before Restart
1. Check Web UI at http://localhost:15672 (guest/guest)
2. Verify both exchanges and queues exist with messages
3. Note message counts in both durable and non-durable queues

## Setup Phase 3: Restart RabbitMQ Server
**Stop RabbitMQ container:**
```bash
docker stop rabbitmq
# or
podman stop rabbitmq
```

**Start RabbitMQ container again:**
```bash
docker start rabbitmq
# or  
podman start rabbitmq
```

## Setup Phase 4: Observe After Restart
1. Check Web UI again at http://localhost:15672
2. **What You Should See:**
   - `durable_exchange` and `durable_queue` still exist
   - `temp_exchange` and `temp_queue` are GONE
   - Persistent messages in durable_queue are preserved
   - All non-persistent messages are LOST

## Setup Phase 5: Consume Surviving Messages
```bash
python consumer.py  # Consumes only the messages that survived restart
```

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Before Restart:**
- `durable_exchange` (durable=true) with `durable_queue`
- `temp_exchange` (durable=false) with `temp_queue`
- Both queues contain messages

**After Restart:**
- Only `durable_exchange` and `durable_queue` remain
- `temp_exchange` and `temp_queue` completely disappeared
- Only persistent messages in durable_queue survived
- Non-persistent messages in durable_queue are also lost

**Key Observations:**
- Durable exchanges/queues survive restart
- Non-durable exchanges/queues disappear
- Message persistence depends on delivery_mode=2
- Non-persistent messages lost even in durable queues

## Durability Matrix

| Component | Durable | Persistent Messages | Survives Restart? |
|-----------|---------|-------------------|------------------|
| durable_exchange | Yes | Yes | ✅ Exchange + Messages |
| durable_exchange | Yes | No | ✅ Exchange, ❌ Messages |
| temp_exchange | No | Yes | ❌ Everything Lost |
| temp_exchange | No | No | ❌ Everything Lost |

## Experiment Scenarios

### Scenario 1: Full Durability Test
1. Run producer (creates both durable and non-durable components)
2. Observe message counts in Web UI
3. Restart RabbitMQ server
4. Compare before/after message counts
5. Run consumer to verify surviving messages

### Scenario 2: Message Persistence Test
1. Modify producer to send only non-persistent messages
2. Restart server
3. Observe that even durable queues lose non-persistent messages

## Real-World Applications
- **Durable:** Critical business data, financial transactions
- **Non-durable:** Temporary notifications, cache invalidation
- **Persistent messages:** Must survive system failures
- **Non-persistent messages:** Performance over reliability