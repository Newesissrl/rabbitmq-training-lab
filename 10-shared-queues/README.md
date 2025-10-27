# Exercise 10: Shared Queues - Load Balancing and Work Distribution

## Concept
Demonstrates shared queues where multiple consumers compete for messages:
- **Shared Queue:** Multiple consumers connect to the same named queue
- **Load Balancing:** Messages distributed among available consumers
- **Work Distribution:** Each message processed by only ONE consumer
- **Persistence:** Queue survives consumer disconnections

## Learning Objectives
- Understand work queue pattern vs pub/sub pattern
- Learn load balancing with multiple workers
- Practice fair dispatch and message acknowledgment
- Observe consumer scaling and fault tolerance

## Comparison with Previous Exercises
| Pattern | Queue Type | Message Distribution | Use Case |
|---------|------------|---------------------|----------|
| **Fanout (Ex 2)** | Exclusive per consumer | ALL consumers get ALL messages | Broadcasting, notifications |
| **Shared Queue** | Single shared queue | ONE consumer gets each message | Work distribution, task processing |

## Setup
1. Start RabbitMQ container (see main README)
2. Run multiple workers sharing the same queue:
   ```bash
   python consumer.py worker-1  # Terminal 1 - connects to shared_tasks queue
   python consumer.py worker-2  # Terminal 2 - connects to shared_tasks queue  
   python consumer.py worker-3  # Terminal 3 - connects to shared_tasks queue
   ```
3. Run producer to send tasks: `python producer.py`

## Expected Behavior
- **Load Balancing:** Messages distributed among available workers
- **Fair Dispatch:** Each worker gets roughly equal number of tasks
- **Fault Tolerance:** If worker stops, others continue processing
- **Persistence:** Queue and unprocessed messages survive worker restarts

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- Default exchange ("") used for direct queue delivery

**Queues Tab:**
- `shared_tasks` queue (durable=true)
- **Consumers:** Shows number of active consumers (should match running workers)
- **Message rates:** Shows delivery rate distributed among consumers
- **Ready messages:** Tasks waiting to be processed

**What You Should See:**
- Single `shared_tasks` queue with multiple consumers
- Messages delivered in round-robin fashion to available workers
- Consumer count changes as workers start/stop
- Unprocessed messages accumulate when no workers available

## Worker Scaling Experiment

### Scenario 1: Single Worker
1. Start only one worker: `python consumer.py worker-1`
2. Run producer - observe all messages go to single worker
3. Check Web UI: 1 consumer, all messages to one worker

### Scenario 2: Multiple Workers
1. Start 3 workers in separate terminals
2. Run producer - observe load balancing
3. Check Web UI: 3 consumers, messages distributed

### Scenario 3: Worker Failure
1. Start 3 workers and producer
2. Stop one worker (Ctrl+C)
3. Observe: remaining workers continue processing
4. Check Web UI: consumer count decreases, load redistributes

### Scenario 4: Late Worker Join
1. Start producer with 2 workers running
2. Add third worker while producer is sending
3. Observe: new worker immediately starts receiving messages
4. Check Web UI: consumer count increases, load redistributes

## Message Acknowledgment
- **Manual ACK:** Workers acknowledge after processing
- **Reliability:** Unacknowledged messages redelivered if worker crashes
- **Fair Dispatch:** `basic_qos(prefetch_count=1)` ensures fair distribution

## Real-World Applications
- **Task Processing:** Image resizing, email sending, data processing
- **Microservices:** Distributed work among service instances
- **Batch Jobs:** Large datasets processed by worker pool
- **API Processing:** Background job processing for web applications

## Key Benefits
- **Horizontal Scaling:** Add more workers to increase throughput
- **Fault Tolerance:** System continues if individual workers fail
- **Load Distribution:** Automatic work balancing
- **Resource Efficiency:** Workers process at their own pace