# Exercise 18: Monitoring and Health Checks

## Concept
Know the state of the broker before your users do:
- **Health checks** (CLI and HTTP API) for liveness/readiness probes and scripts
- **Management HTTP API** for queue depth, rates, consumers
- **Prometheus metrics** (`rabbitmq_prometheus` plugin, port 15692) for dashboards and alerting

## Learning Objectives
- Use the right health check for the right question
- Read the key queue indicators: ready, unacked, consumers, rates
- Query RabbitMQ metrics with PromQL
- Spot the classic problems: backlog, missing consumers, resource alarms

## Setup
1. Start RabbitMQ from the repository root: `docker compose up -d`
   (the compose file publishes the Prometheus port 15692)
2. Activate the virtual environment (see main README)

## Part 1: Health Checks (5 min)
```bash
# Is the node process up? (liveness)
docker exec rabbitmq rabbitmq-diagnostics -q ping

# Is the RabbitMQ application running? Are the listeners accepting connections? (readiness)
docker exec rabbitmq rabbitmq-diagnostics -q check_running
docker exec rabbitmq rabbitmq-diagnostics -q check_port_connectivity

# Are there memory/disk alarms? (exit code 69 when an alarm is active)
docker exec rabbitmq rabbitmq-diagnostics -q check_alarms; echo "exit code: $?"

# Are all virtual hosts running?
docker exec rabbitmq rabbitmq-diagnostics -q check_virtual_hosts

# Would stopping this node make a quorum queue lose its majority? (useful before maintenance in a cluster)
docker exec rabbitmq rabbitmq-diagnostics -q check_if_node_is_quorum_critical

# The same information over HTTP (200 = ok, 503 = failing)
curl -s -u guest:guest http://localhost:15672/api/health/checks/alarms
curl -s -u guest:guest http://localhost:15672/api/health/checks/virtual-hosts
```
> **RabbitMQ 4.3 note:** `rabbitmq-diagnostics check_local_alarms` is deprecated and
> is a **no-op**: it always reports "no local alarms". Use `check_alarms` or
> `rabbitmq-diagnostics alarms`.

## Part 2: Queue Monitor on the HTTP API (10 min)
```bash
python queue_monitor.py                 # Terminal 1 (refreshes every 3 s)
```
Create the classic problems and watch the alerts:
```bash
# Backlog + no consumers: fill a queue without consumers
python ../16-failure-drill/resilient_producer.py --count 300 --rate 200

# Consumers catch up: alerts disappear, deliver/s goes up
python ../16-failure-drill/resilient_consumer.py     # Ctrl+C when the queue is empty

# Resource alarm: publishers are blocked (wait ~10-15 s)
docker exec rabbitmq rabbitmqctl set_disk_free_limit 1000GB
docker exec rabbitmq rabbitmqctl set_disk_free_limit 50MB      # restore!
```
Streams are not flagged: their messages stay in the log after consumption.

## Part 3: Prometheus Metrics (10 min)
```bash
# Aggregated metrics (recommended in production: cheap, one series per metric)
curl -s http://localhost:15692/metrics | grep -E "^rabbitmq_(queues|connections|alarms)"

# Per-object metrics (one series per queue/connection: useful in a lab,
# expensive with thousands of queues)
curl -s http://localhost:15692/metrics/per-object | grep "^rabbitmq_queue_messages_ready"
```

### Optional: Prometheus + Grafana
```bash
docker compose -f docker-compose.monitoring.yml up -d
```
- Prometheus: http://localhost:9090 → Status → Targets: `rabbitmq` and `rabbitmq-per-object` are `UP`
- Try these queries in the Prometheus **Graph** page:

| Question | PromQL |
|----------|--------|
| Messages ready per queue | `rabbitmq_queue_messages_ready{job="rabbitmq-per-object"}` |
| Queues with a backlog | `rabbitmq_queue_messages_ready{job="rabbitmq-per-object"} > 100` |
| Publish rate (msg/s) | `sum(rate(rabbitmq_global_messages_received_total{job="rabbitmq"}[1m]))` |
| Open connections | `rabbitmq_connections{job="rabbitmq"}` |
| Disk alarm active | `rabbitmq_alarms_free_disk_space_watermark{job="rabbitmq"} == 1` |
| Memory alarm active | `rabbitmq_alarms_memory_used_watermark{job="rabbitmq"} == 1` |

- Grafana: http://localhost:3000 (anonymous admin, training only) → Dashboards →
  New → Import → dashboard ID **10991** ("RabbitMQ-Overview", published by the
  RabbitMQ team) → select the `prometheus` data source
- Re-run the producer and the disk alarm from Part 2 and watch the dashboard

> **Killercoda:** open ports 15672, 9090 and 3000 from the Traffic / Ports menu.

## What to Alert On
| Signal | Why |
|--------|-----|
| Any memory/disk alarm | Publishers are blocked |
| Ready messages growing for N minutes | Consumers too slow or down |
| Queue with messages and 0 consumers | Consumer crashed or not deployed |
| Unacked messages growing | Consumers stuck (deadlock, slow downstream) |
| Node down / health check failing | Capacity and quorum at risk |
| File descriptors / connections near the limit | Connection leak (see exercise 13) |

## Cleanup
```bash
docker compose -f docker-compose.monitoring.yml down
docker exec rabbitmq rabbitmqctl set_disk_free_limit 50MB
docker exec rabbitmq rabbitmqctl delete_queue drill_orders
```
