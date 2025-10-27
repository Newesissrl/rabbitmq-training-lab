# Exercise 7: Message TTL and Non-Durable Components

## Concept
Demonstrates message Time-To-Live (TTL) and non-durable exchanges/queues:
- Non-durable exchanges/queues disappear on server restart
- Messages with TTL expire and are discarded if not consumed
- Temporary messaging for ephemeral data

## Learning Objectives
- Understand message TTL behavior
- Learn difference between durable vs non-durable components
- Practice temporary messaging patterns
- Observe message expiration in real-time

## Setup
1. Start RabbitMQ container (see main README)
2. **First - Run producer only (no consumer):**
   ```bash
   python producer.py  # Sends messages with 5-second TTL
   ```
3. **Wait and observe messages expiring in Web UI**
4. **Then run consumer to catch messages before expiry:**
   ```bash
   python consumer.py  # Terminal 2 - consumes before TTL expires
   ```

## Message TTL Behavior
- Messages expire after 5 seconds if not consumed
- Expired messages are automatically discarded
- Non-durable queues exist only while consumers are connected
- Exchange and queues are temporary (auto-delete)

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `temp_exchange` - non-durable, auto-delete exchange
- Exchange disappears when no queues bound

**Queues Tab:**
- `temp_queue` - non-durable, auto-delete queue
- Queue disappears when consumer disconnects
- Watch message count decrease as TTL expires

**What You Should See:**
1. **Producer Only:** Messages accumulate then disappear (TTL expiry)
2. **With Consumer:** Messages consumed before expiration
3. **Consumer Disconnect:** Queue disappears immediately
4. **Server Restart:** All components disappear (non-durable)

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
2. Watch queue disappear from Web UI
3. Stop producer - exchange may disappear if auto-delete

## Key Differences from Previous Exercises
- **Non-durable:** Components don't survive server restart
- **Auto-delete:** Queues/exchanges clean up automatically
- **TTL:** Messages have expiration time
- **Temporary:** Designed for ephemeral messaging patterns