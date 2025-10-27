# Exercise 6: Dead Letter Exchange (DLX)

## Concept
Dead Letter Exchange handles messages that cannot be processed:
- Message rejected and not requeued
- Message TTL expires
- Queue length limit exceeded

## Learning Objectives
- Understand dead letter exchange pattern
- Learn message TTL and rejection handling
- Practice error handling in messaging

## Setup
1. Start RabbitMQ container (see main README)
2. Run consumer (no parameters needed):
   ```bash
   python consumer.py  # Monitors both main_queue and dead_letters queue
   ```
   The consumer automatically:
   - Processes messages from main_queue
   - Rejects messages containing "rejected"
   - Monitors dead_letters queue for failed messages
3. Run producer (no parameters needed): `python producer.py`
   - Sends 4 test messages with different behaviors
   - Messages expire after 10 seconds if not consumed

## Key Features
- Messages with TTL expire and go to DLX
- Rejected messages (nack with requeue=false) go to DLX
- DLX provides error handling and retry mechanisms

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `dlx` exchange with type "direct" for dead letters
- Default exchange for main queue

**Queues Tab:**
- `main_queue` - with DLX configuration and TTL
- `dead_letters` - receives failed/expired messages
- Queue arguments show x-dead-letter-exchange settings

**What You Should See:**
- main_queue has x-dead-letter-exchange = "dlx"
- main_queue has x-message-ttl = 10000ms
- Messages move to dead_letters after rejection or TTL expiry
- Dead letter messages have additional headers (x-death)

**Dead Letter Scenarios:**
1. **TTL Expiry:** Messages not consumed within 10 seconds → dead_letters
2. **Rejection:** Messages containing "rejected" → dead_letters
3. **Headers:** Dead letters show rejection reason and original queue

## Experiment
- Watch messages expire and move to dead letter queue
- Observe rejection headers in dead letter messages
- Check x-death headers for failure details
- Monitor TTL countdown in main_queue