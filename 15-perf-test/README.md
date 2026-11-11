# Exercise 15: Performance Testing with RabbitMQ PerfTest

## Concept
Uses the official RabbitMQ PerfTest tool to benchmark message throughput:
- **Load Testing:** High-volume message production and consumption
- **Performance Metrics:** Messages per second, latency, resource usage
- **Scalability Testing:** Multiple producers and consumers
- **Baseline Measurements:** Establish performance baselines

## Learning Objectives
- Learn to use RabbitMQ PerfTest tool
- Understand performance testing methodology
- Measure throughput and latency under load
- Analyze performance bottlenecks

## Prerequisites
- Docker with network support
- RabbitMQ running in Docker network
- Basic understanding of performance metrics

## Setup

### 1. Start RabbitMQ in the `rabbitmq_net` Network
The repository `docker-compose.yml` already creates the `rabbitmq_net` network
and attaches the `rabbitmq` container to it:
```bash
# From the repository root
docker compose up -d
```

### 2. (Only if you started RabbitMQ with plain `docker run`)
```bash
docker network create rabbitmq_net
docker network connect rabbitmq_net rabbitmq
```

### 3. Run Performance Test
```bash
docker run --rm --network rabbitmq_net pivotalrabbitmq/perf-test:latest \
  --uri amqp://guest:guest@rabbitmq \
  --producers 10 --consumers 10 \
  --rate 2000 --queue perf-test \
  --size 1024 --time 300
```

## Test Parameters Explained
- `--producers 10`: 10 concurrent message producers
- `--consumers 10`: 10 concurrent message consumers  
- `--rate 2000`: Target 2000 messages per second
- `--queue perf-test`: Use queue named "perf-test"
- `--size 1024`: Each message is 1024 bytes
- `--time 300`: Run test for 300 seconds (5 minutes)

## Performance Scenarios

### Scenario 1: Baseline Test
**Linux/macOS:**
```bash
./run_baseline_test.sh
```
**Windows:**
```cmd
run_baseline_test.cmd
```

### Scenario 2: High Throughput
**Linux/macOS:**
```bash
./run_high_throughput.sh
```
**Windows:**
```cmd
run_high_throughput.cmd
```

### Scenario 3: Many Producers
**Linux/macOS:**
```bash
./run_many_producers.sh
```
**Windows:**
```cmd
run_many_producers.cmd
```

### Scenario 4: Large Messages
**Linux/macOS:**
```bash
./run_large_messages.sh
```
**Windows:**
```cmd
run_large_messages.cmd
```

### Scenario 5: Classic vs Quorum Queue
Quorum queues are the replicated, data-safe queue type of RabbitMQ 4.x. They
always persist messages, so compare them with persistent messages on a classic
queue:
```bash
# Classic queue, persistent messages
docker run --rm --network rabbitmq_net pivotalrabbitmq/perf-test:latest \
  --uri amqp://guest:guest@rabbitmq --producers 5 --consumers 5 \
  --queue perf-classic --flag persistent --size 1024 --time 60

# Quorum queue
docker run --rm --network rabbitmq_net pivotalrabbitmq/perf-test:latest \
  --uri amqp://guest:guest@rabbitmq --producers 5 --consumers 5 \
  --queue perf-quorum --quorum-queue --flag persistent --size 1024 --time 60
```
On a single node, the quorum queue has no replicas to wait for. Run it against the
3-node cluster of `00-installation/ex02` to see the replication cost.
Delete `perf-quorum` afterwards (quorum queues are not auto-deleted).

> **Running on Killercoda?** The playground VM is small. Use shorter tests
> (`--time 60`) and lower rates, and keep `docker stats` open in a second tab.

## Expected Metrics
- **Throughput:** Messages per second (target: 2000 msg/s)
- **Latency:** Message delivery time (typically < 10ms)
- **CPU Usage:** Monitor RabbitMQ container CPU
- **Memory Usage:** Monitor queue memory consumption
- **Network I/O:** Bandwidth utilization

## Monitoring During Test

### RabbitMQ Management UI
Open http://localhost:15672 and monitor:
- **Overview:** Message rates and queue depths
- **Queues:** perf-test queue statistics
- **Connections:** Active producer/consumer connections
- **Nodes:** Resource usage and performance

### Docker Stats
```bash
docker stats rabbitmq
```

## Performance Analysis
After running tests, analyze:
1. **Achieved vs Target Rate:** Did we reach 2000 msg/s?
2. **Resource Utilization:** CPU, memory, network usage
3. **Bottlenecks:** Identify limiting factors
4. **Scalability:** How performance changes with load

## Cleanup
```bash
# Delete the test queues that are not auto-deleted
docker exec rabbitmq rabbitmqctl delete_queue perf-quorum

# Stop RabbitMQ (from the repository root)
docker compose down
```
