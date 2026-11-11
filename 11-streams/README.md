# Exercise 11: RabbitMQ Streams

## Concept
RabbitMQ Streams are append-only logs optimized for high-throughput scenarios:
- **Append-only:** Messages stored in order, never deleted automatically
- **Offset-based:** Consumers track position in stream
- **Replay:** Consumers can read from any point in stream history
- **High-throughput:** Optimized for millions of messages per second

## Prerequisites
- **RabbitMQ 4.3** with the `rabbitmq_stream` plugin enabled (the repository
  `docker-compose.yml` enables it and publishes port 5552)
- **rstream library** (different from pika, installed by `requirements.txt`)

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

## Setup

### 1. Start RabbitMQ with streams enabled
```bash
# From the repository root (recommended): streams plugin + port 5552 included
docker compose up -d
```
If you started RabbitMQ with plain `docker run` (see main README), make sure
port 5552 is published and enable the plugin:
```bash
docker exec rabbitmq rabbitmq-plugins enable rabbitmq_stream rabbitmq_stream_management
```

### 2. Install Stream Dependencies
```bash
pip install -r ../requirements.txt   # includes rstream
```

### 3. Run Exercise

**Option A: Full featured:**
```bash
python producer.py                    # Terminal 1 - publishes an event every 2 s
python consumer.py                    # Terminal 2 - replays from the first message
python consumer.py --offset next      # Only messages published from now on
python consumer.py --offset 5         # Start reading at offset 5
python consumer.py --filter error     # Server-side filtering: error events only
python consumer.py --filter payment   # Server-side filtering: payment events only
```

**Option B: Simple version:**
```bash
python simple_producer.py   # Publishes 10 events then exits
python simple_consumer.py   # Consumes from simple_stream
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

### 3. Replay
- Start from `first`, `last`, `next` or a specific numeric offset
- Run several consumers with different offsets at the same time
- Replay events for debugging/analysis (rstream also supports `OffsetType.TIMESTAMP`)

### 4. Server-Side Filtering
- The producer attaches a *filter value* (the category) to each message
- The broker only sends chunks that contain the requested value
- The consumer also applies a predicate, because filtering is done per chunk
- Reduces network traffic for selective consumers

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Queues and Streams Tab:**
- `events_stream` with type `stream` and message count

**Stream Connections Tab** (from `rabbitmq_stream_management`):
- One connection per running producer/consumer
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
- **Different Protocol:** Uses the Stream protocol (port 5552); streams can also be read over AMQP 0-9-1 with `x-stream-offset`
- **Retention:** Messages are removed by retention policies (`x-max-age`, `x-max-length-bytes`), not by consumers
- **Storage:** Streams consume more disk space
- **Complexity:** More complex than traditional queues

## Troubleshooting

**If you get connection errors:**
1. **Use Simple Version:** Try `simple_producer.py` and `simple_consumer.py` first
2. **Verify Stream Plugin:** `docker exec rabbitmq rabbitmq-plugins list | grep stream`
3. **Check Port:** `docker port rabbitmq 5552`
4. **Test Connection:** `nc -vz 127.0.0.1 5552`

**Common Issues:**
- **Host name resolution:** The scripts use `load_balancer_mode=True` so the client keeps using `127.0.0.1` instead of the host name advertised by the broker
- **Filter shows nothing:** Messages published before the filter value extractor existed have no filter value. Delete the stream (`docker exec rabbitmq rabbitmqctl delete_queue events_stream`) and run the producer again
