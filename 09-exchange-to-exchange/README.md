# Exercise 9: Exchange-to-Exchange Binding

## Concept
Demonstrates exchange-to-exchange binding to preserve messages across durability boundaries:
- **Source Exchange:** Non-durable for fast, temporary processing
- **Target Exchange:** Durable for reliable, persistent storage
- **Message Flow:** Producer → Non-durable → Durable → Multiple consumers
- **Use Case:** Fast processing with backup/audit trail

## Learning Objectives
- Understand exchange-to-exchange binding
- Learn message duplication across durability levels
- Practice hybrid messaging patterns
- Observe message preservation strategies

## Architecture
```
Producer → temp_exchange (non-durable) → archive_exchange (durable)
                ↓                              ↓
         temp_consumer                  archive_consumer
         (fast processing)              (reliable storage)
```

## Setup
1. Start RabbitMQ container (see main README)
2. Run producer to create exchanges and bindings:
   ```bash
   python producer.py  # Creates both exchanges and binding
   ```
3. Run consumers in separate terminals:
   ```bash
   python consumer.py temp     # Terminal 1 - fast temp processing
   python consumer.py archive  # Terminal 2 - reliable archive processing
   ```

## Message Flow Behavior
- Producer sends to `temp_exchange` (non-durable)
- Messages automatically copied to `archive_exchange` (durable)
- Both consumers receive identical messages
- Temp consumer processes ephemeral data quickly
- Archive consumer stores data reliably

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `temp_exchange` (durable=false) - source exchange
- `archive_exchange` (durable=true) - target exchange
- Click `temp_exchange` → see binding to `archive_exchange`

**Queues Tab:**
- `temp_queue` (non-durable) - fast processing
- `archive_queue` (durable) - reliable storage
- Both queues receive identical message counts

**What You Should See:**
- Exchange-to-exchange binding in temp_exchange bindings
- Messages appear in both queues simultaneously
- Identical message flow to both consumers
- Different durability properties for each queue

## Durability Test
**Test message preservation across restart:**

1. **Send messages** with producer running
2. **Stop consumers** (let messages accumulate)
3. **Restart RabbitMQ server:**
   ```bash
   docker stop rabbitmq && docker start rabbitmq
   ```
4. **Check Web UI after restart:**
   - `temp_exchange` and `temp_queue` are GONE
   - `archive_exchange` and `archive_queue` survive
   - Only persistent messages in archive_queue remain

5. **Run archive consumer** to process surviving messages:
   ```bash
   python consumer.py archive
   ```

## Real-World Applications

**Fast + Reliable Pattern:**
- **Temp path:** Real-time notifications, cache updates
- **Archive path:** Audit logs, compliance records, analytics

**Examples:**
- **E-commerce:** Fast order processing + reliable order history
- **IoT:** Real-time alerts + long-term sensor data storage
- **Financial:** Immediate transaction response + audit trail
- **Logging:** Fast log processing + persistent log storage

## Key Benefits
- **Performance:** Non-durable path for speed
- **Reliability:** Durable path for data safety
- **Flexibility:** Different processing logic per path
- **Compliance:** Automatic audit trail creation