# Exercise 5: Default Exchange

## Concept
The default exchange is a pre-declared direct exchange with no name ("").
Messages are routed to queues where the routing key equals the queue name.

## Learning Objectives
- Understand default exchange behavior
- Learn implicit queue binding
- Practice simple point-to-point messaging

## Setup
1. Start RabbitMQ container (see main README)
2. Run consumers with specific queue names:
   ```bash
   python consumer.py task_queue     # Terminal 1 - listens to 'task_queue'
   python consumer.py urgent_queue   # Terminal 2 - listens to 'urgent_queue'
   python consumer.py batch_queue    # Terminal 3 - listens to 'batch_queue'
   ```
3. Send messages to specific queues:
   ```bash
   python producer.py task_queue "Process user registration"
   python producer.py urgent_queue "Critical system alert"
   python producer.py batch_queue "Generate monthly report"
   ```

## Key Points
- Exchange name is empty string ""
- Routing key must match queue name exactly
- All queues are automatically bound to default exchange
- Simplest form of messaging in RabbitMQ

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- Default exchange (empty name "") with type "direct"
- All queues automatically bound to default exchange

**Queues Tab:**
- Named queues: `task_queue`, `urgent_queue`, `batch_queue`
- Durable queues persist between restarts
- Messages delivered only to queue matching routing key

**What You Should See:**
- Queues created with exact names specified
- Messages delivered when routing key = queue name
- Default exchange bindings are implicit (not visible)
- Queue durability and message persistence

**Routing Examples:**
- Message to routing key "task_queue" → delivered to task_queue only
- Message to routing key "urgent_queue" → delivered to urgent_queue only
- No pattern matching - exact name matching only

## Experiment
- Send messages to different queue names
- Observe direct point-to-point delivery
- Try sending to non-existent queue names (messages dropped)