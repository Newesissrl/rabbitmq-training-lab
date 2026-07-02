# Exercise 12: Super Streams - Partitioned Streams (RabbitMQ 4+ Only)

## Concept
Super Streams are partitioned streams that enable horizontal scaling:
- **Partitioning:** Messages distributed across multiple stream partitions
- **Routing Key:** Determines which partition receives each message
- **Parallel Processing:** Multiple consumers can process different partitions
- **Scalability:** Add more partitions to increase throughput

## Prerequisites
- **RabbitMQ 4.0+** (Super Streams not available in RabbitMQ 3)
- **rstream library** with super stream support
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

## Setup (RabbitMQ 4 Required)

### 1. Start RabbitMQ 4 Container
```bash
# Must use RabbitMQ 4 with super streams support
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -p 5552:5552 \
  rabbitmq:4-management

# Enable streams plugin
docker exec rabbitmq rabbitmq-plugins enable rabbitmq_stream
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

**Streams Tab:**
- `orders_super_stream` with multiple partitions
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

### 2. Multiple Processes / Machines (for horizontal scaling)
To achieve true horizontal scaling, you would run the same `consumer.py` script on multiple different machines or in different containers. The `rstream` library and RabbitMQ handle the coordination, ensuring that different consumer instances process different partitions, thus distributing the load. (Note: The specifics of this coordination are handled by the client library and RabbitMQ server).

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
