# Exercise 16: Failure Drill

## Concept
Break things on purpose and check that no message is lost:
- **Broker restart** while producing and consuming
- **Consumer crash** with unacknowledged messages in flight
- **Resource alarm** (disk) that blocks publishers

The scripts implement the reliability patterns from the previous exercises:
- `resilient_producer.py`: publisher confirms, persistent messages, quorum queue, automatic reconnection
- `resilient_consumer.py`: manual acks, prefetch, automatic reconnection, report of duplicates and gaps

## Learning Objectives
- Verify **at-least-once** delivery: no gaps, duplicates are possible
- See redelivery of unacknowledged messages
- Recognise a blocked publisher and the alarm that causes it
- Practise the diagnostic commands you need during an incident

## Setup
1. Start RabbitMQ from the repository root: `docker compose up -d`
2. Activate the virtual environment (see main README)

Each drill takes about 5 minutes.

## Drill 1: Broker Restart Under Load
```bash
python resilient_consumer.py                          # Terminal 1
python resilient_producer.py --count 300 --rate 10    # Terminal 2
docker restart rabbitmq                               # Terminal 3, while messages flow
```
**Observe:**
- Both clients print `Connection lost ... retry` and then `Reconnected`
- The producer resumes from the first **unconfirmed** message
- When the producer has finished, stop the consumer (Ctrl+C) and read the report:
  `Gaps (lost): none`. Duplicates are possible: a message can be stored by the
  broker while its confirm is lost in the restart, so the producer sends it again.

**Discuss:** what would happen with `delivery_mode=1` on a classic queue
(see exercise 08)? With a quorum queue every message is persisted anyway.

## Drill 2: Consumer Crash
```bash
python resilient_producer.py --count 50 --rate 100   # fill the queue
python resilient_consumer.py --crash-after 15         # dies after 15 messages
python resilient_consumer.py                          # restart it, then Ctrl+C
```
**Observe:**
- The first consumer had up to `--prefetch` (10) messages delivered but not acknowledged
- After the crash these messages are delivered again with the `REDELIVERED` flag
- Report of the second run: `Gaps (lost): none`

**Discuss:** your consumer must be **idempotent**, because a redelivered message may
already have been processed before the crash. Try `--prefetch 1` and compare.

## Drill 3: Disk Alarm Blocks Publishers
```bash
python resilient_producer.py                                      # Terminal 1

# Terminal 2: pretend the disk is almost full (limit above the free space)
docker exec rabbitmq rabbitmqctl set_disk_free_limit 1000GB
```
**Observe (wait ~10-15 seconds, the disk is checked periodically):**
- The producer stops printing `Confirmed`: the broker has **blocked** the publishing connection
- The alarm is visible from the CLI, the HTTP API and the Management UI (red disk box on the Overview page):
  ```bash
  docker exec rabbitmq rabbitmq-diagnostics alarms
  docker exec rabbitmq rabbitmq-diagnostics check_alarms; echo "exit code: $?"   # 69 = alarm
  curl -u guest:guest http://localhost:15672/api/health/checks/alarms
  ```
- Connections tab: the producer connection state is `blocked`
- Consumers keep working: alarms block **publishers** only

**Recover:**
```bash
docker exec rabbitmq rabbitmqctl set_disk_free_limit 50MB    # back to the default
```
The producer resumes and prints the `BLOCKED` / `UNBLOCKED` notifications (pika's
`BlockingConnection` delivers them once the pending publish returns).

> The same happens with a **memory alarm** (`vm_memory_high_watermark`). Never let a
> publisher wait forever in production: set `blocked_connection_timeout` in pika
> and alert on `rabbitmq_alarms_*` metrics (see exercise 18).

## Cleanup
```bash
docker exec rabbitmq rabbitmqctl set_disk_free_limit 50MB   # in case drill 3 was interrupted
docker exec rabbitmq rabbitmqctl delete_queue drill_orders
```

## Key Takeaways
| Failure | Protection |
|---------|------------|
| Broker restart | Durable/quorum queue + persistent messages + publisher confirms + reconnect |
| Consumer crash | Manual acks (never `auto_ack=True` for important work) + idempotent processing |
| Resource alarm | Monitoring of alarms + `blocked_connection_timeout` in clients |
