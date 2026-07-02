# Exercise 11: RabbitMQ Streams (RabbitMQ 4+ Only)

## Concept
RabbitMQ Streams are append-only logs optimized for high-throughput scenarios:
- **Append-only:** Messages stored in order, never deleted automatically
- **Offset-based:** Consumers track position in stream
- **Replay:** Consumers can read from any point in stream history
- **High-throughput:** Optimized for millions of messages per second

## Prerequisites
- **RabbitMQ 4.0+** (Streams not available in RabbitMQ 3)
- **rstream library** (different from pika)

## Learning Objectives
- Understand streams vs traditional queues
- Learn offset-based consumption
- Practice replay and time-travel scenarios
- Observe high-throughput messaging patterns
- Learn server-side stream filtering for efficiency

## Streams vs Queues Comparison

| Feature | Traditional Queues | RabbitMQ Streams |
|---------|-------------------|------------------|
| **Message Storage** | Deleted after consumption | Persistent append-only log |
| **Consumption** | Destructive (message removed) | Non-destructive (offset tracking) |
| **Replay** | Not possible | Full replay from any offset |
| **Multiple Consumers** | Competing consumers | Independent offset tracking |
| **Use Case** | Task distribution | Event sourcing, analytics |

## Setup (RabbitMQ 4 Required)

### 1. Start RabbitMQ 4 Container
```bash
# Must use RabbitMQ 4 - streams not available in v3
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -p 5552:5552 \
  rabbitmq:4-management

# Enable streams plugin (should be enabled by default in v4)
docker exec rabbitmq rabbitmq-plugins enable rabbitmq_stream
```

### 2. Install Stream Dependencies
```bash
pip install rstream
```

### 3. Run Exercise

**Option A: Full Featured (may have connection issues on some systems):**
```bash
python producer.py   # Publishes events to stream
python consumer.py   # Consumes from beginning
python consumer.py --offset latest  # Consumes only new messages
python consumer.py --filter error    # Server-side filtering for error events
python consumer.py --filter payment  # Server-side filtering for payment events
```

**Option B: Simple Version (more compatible):**
```bash
python simple_producer.py   # Publishes 10 events then exits
python simple_consumer.py   # Consumes from stream
```

## Stream Features Demonstrated

### 1. Persistent Event Log
- All messages stored permanently
- Stream acts as event history
- No message deletion after consumption

### 2. Offset-Based Consumption
- Consumers track their position (offset)
- Multiple consumers can read independently
- Replay from any point in history

### 3. Time-Travel Queries
- Read messages from specific timestamp
- Replay events for debugging/analysis
- Historical data always available

### 4. Server-Side Filtering
- Filter messages at server level (not client)
- Reduces network traffic and client processing
- Efficient for selective consumption patterns

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Streams Tab:** (New in RabbitMQ 4)
- `events_stream` with message count
- Stream size and retention policy
- Consumer offset tracking

**What You Should See:**
- Stream grows continuously (messages not deleted)
- Multiple consumers with independent offsets
- Message rate and throughput metrics
- Stream segment information

## Real-World Applications

### Event Sourcing
- Store all business events permanently
- Replay events to rebuild application state
- Audit trail for compliance

### Analytics & Monitoring
- High-throughput metrics collection
- Real-time and historical analysis
- Multiple analytics consumers

### Data Replication
- Stream changes to multiple systems
- Each system consumes at own pace
- Guaranteed message ordering

## Limitations & Considerations
- **RabbitMQ 4+ Only:** Not available in RabbitMQ 3
- **Different Protocol:** Uses Stream protocol, not AMQP
- **Storage:** Streams consume more disk space
- **Complexity:** More complex than traditional queues

## Troubleshooting

**If you get connection errors:**
1. **Use Simple Version:** Try `simple_producer.py` and `simple_consumer.py` first
2. **Check RabbitMQ Version:** Ensure you're using RabbitMQ 4+
3. **Verify Stream Plugin:** `docker exec rabbitmq rabbitmq-plugins list | grep stream`
4. **Check Port:** `docker port rabbitmq 5552`
5. **Test Connection:** `telnet 127.0.0.1 5552`

**Common Issues:**
- **DNS Resolution:** The simple versions use IP addresses to avoid hostname issues
- **Connection Pooling:** The simple versions avoid complex connection management
- **API Compatibility:** The simple versions use basic rstream API calls

## Note
This exercise requires RabbitMQ 4 and demonstrates advanced streaming concepts. If you're using RabbitMQ 3, skip this exercise and focus on the traditional AMQP patterns in exercises 1-10.

If the full-featured versions don't work due to connection issues, use the simple versions which are more compatible across different environments.