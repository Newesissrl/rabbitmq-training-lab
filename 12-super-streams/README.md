# Exercise 12: Super Streams - Partitioned Streams

## Concept
Super Streams are partitioned streams that enable horizontal scaling:
- **Partitioning:** Messages distributed across multiple stream partitions
- **Routing Key:** Determines which partition receives each message
- **Parallel Processing:** Multiple consumers can process different partitions
- **Scalability:** Add more partitions to increase throughput

## Prerequisites
- **RabbitMQ 4.3** with the `rabbitmq_stream` plugin enabled (included in the repository `docker-compose.yml`)
- **rstream library** with super stream support (installed by `requirements.txt`)
- **Understanding of Exercise 11** (basic streams)

## Learning Objectives
- Understand partitioned vs single streams
- Learn partition routing strategies
- Practice parallel consumer patterns
- Observe horizontal scaling benefits

## Super Streams vs Regular Streams

| Feature | Regular Stream | Super Stream |
|----------------|----------------|--------------|
| **Partitions** | Single stream | Multiple partitioned streams |
| **Routing** | All messages to one stream | Messages routed by key to partitions |
| **Consumers** | Sequential processing | Parallel processing per partition |
| **Scaling** | Vertical (faster hardware) | Horizontal (more partitions) |
| **Ordering** | Global ordering | Per-partition ordering |

## Setup

### 1. Start RabbitMQ with streams enabled
```bash
# From the repository root: streams plugin + port 5552 included
docker compose up -d
```
If you started RabbitMQ with plain `docker run`, publish port 5552 and run:
```bash
docker exec rabbitmq rabbitmq-plugins enable rabbitmq_stream rabbitmq_stream_management
```

### 2. Run Exercise
```bash
# Start the producer to publish to the partitioned super stream
python producer.py

# In a separate terminal, start the consumer
# The consumer will automatically subscribe to all partitions of the super stream
python consumer.py
```

## Partitioning Strategy

### Routing Key Based Partitioning
- **User Events:** Route by user_id → consistent partition per user
- **Order Events:** Route by customer_id → related orders in same partition
- **System Events:** Route by service_name → service events grouped

### Benefits
- **Parallel Processing:** Each partition processed independently
- **Ordering Guarantees:** Messages with same routing key stay ordered
- **Load Distribution:** Even distribution across partitions
- **Fault Tolerance:** Partition failures don't affect others

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Queues and Streams Tab:**
- Partition streams `orders_super_stream-0/1/2`

**Exchanges Tab:**
- `orders_super_stream` (type `direct`) routing to the partitions
- Individual partition statistics
- Message distribution across partitions

**What You Should See:**
- Multiple stream partitions (orders_super_stream-0, orders_super_stream-1, etc.)
- Messages distributed based on routing key
- Independent consumer offsets per partition
- Parallel processing metrics

## Partition Consumer Patterns

The `SuperStreamConsumer` class used in this exercise is a high-level client that simplifies consumption from a super stream. It automatically discovers all partitions and consumes from them concurrently within a single process.

### 1. Single Application, All Partitions
The provided `consumer.py` script demonstrates this pattern. When you run it, a single consumer process connects to the super stream and starts fetching messages from all its partitions in parallel.

```bash
# A single consumer process subscribes to all partitions
python consumer.py
```

### 2. Multiple Processes / Machines (horizontal scaling with Single Active Consumer)
Running `python consumer.py` twice makes **both** instances read **all**
partitions (every message is processed twice). To split the partitions between
instances, start them with `--sac`:

```bash
python consumer.py --sac   # Terminal 2 - becomes ACTIVE on all 3 partitions
python consumer.py --sac   # Terminal 3 - the broker moves one or more partitions here
```

With `--sac` every instance joins the consumer group `orders-app` with
**Single Active Consumer** enabled on the super stream. The broker keeps exactly
one active consumer per partition and rebalances partitions when instances join
or leave. Watch the `[~] ... now ACTIVE / standby` lines, then stop one instance
(Ctrl+C) and see the other one take its partitions back.

Inspect the group from the CLI:
```bash
docker exec rabbitmq rabbitmq-streams list_stream_group_consumers \
  --stream orders_super_stream-0 --reference orders-app
```

## Real-World Applications

### E-commerce Order Processing
- **Partition by:** customer_id
- **Benefit:** All orders from same customer processed in sequence
- **Scaling:** Add partitions as customer base grows

### IoT Sensor Data
- **Partition by:** device_id or location
- **Benefit:** Device data processed in chronological order
- **Scaling:** Add partitions for new device deployments

### Financial Transactions
- **Partition by:** account_id
- **Benefit:** Account transactions processed sequentially
- **Scaling:** Distribute load across multiple partitions

## Key Considerations

### Partition Count Planning
- **Start Small:** Begin with 3-5 partitions
- **Growth Strategy:** Plan for future scaling needs
- **Rebalancing:** Adding partitions requires careful planning

### Routing Key Design
- **Even Distribution:** Avoid hot partitions
- **Logical Grouping:** Related messages in same partition
- **Consistency:** Same entity always routes to same partition

### Consumer Scaling
- **Max Consumers:** One consumer per partition maximum
- **Load Balancing:** Distribute partitions among consumer instances
- **Fault Tolerance:** Handle partition consumer failures

## Limitations
- **Complexity:** More complex than single streams
- **Partition Management:** Requires partition planning
- **Cross-Partition Ordering:** No global ordering guarantees
- **Rebalancing:** Adding partitions affects existing data distribution
