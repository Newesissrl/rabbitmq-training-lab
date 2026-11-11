# Exercise 2: RabbitMQ Cluster with Docker Compose

## Description
Set up a 3-node RabbitMQ cluster using Docker Compose for high availability and load distribution.

## Prerequisites
- Docker and Docker Compose installed
- Understanding of clustering concepts
- Basic knowledge of YAML configuration

## Architecture
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  rabbit-1   │    │  rabbit-2   │    │  rabbit-3   │
│   (main)    │◄──►│  (replica)  │◄──►│  (replica)  │
│ Port: 15672 │    │ Port: 15673 │    │ Port: 15674 │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Setup Instructions

### 1. Start the Cluster
```bash
# Start all nodes
docker compose up -d

# Check cluster status
docker compose logs -f
```

### 2. Verify Cluster Formation
```bash
# Check cluster status on main node
docker exec rabbitmq-cluster-node-1 rabbitmqctl cluster_status

# Check all nodes
docker exec rabbitmq-cluster-node-2 rabbitmqctl cluster_status
docker exec rabbitmq-cluster-node-3 rabbitmqctl cluster_status
```

### 3. Access Management UIs
- Node 1: http://localhost:15672 (admin/cluster123)
- Node 2: http://localhost:15673 (admin/cluster123)  
- Node 3: http://localhost:15674 (admin/cluster123)

## Testing High Availability

### Test Cluster Setup
```bash
# Check cluster is working - all nodes should be listed
docker exec rabbitmq-cluster-node-1 rabbitmqctl cluster_status

# List current queues
docker exec rabbitmq-cluster-node-1 rabbitmqctl list_queues name type

# Create a quorum queue (the replicated, highly available queue type) via the HTTP API
curl -u admin:cluster123 -X PUT http://localhost:15672/api/queues/%2F/test_quorum \
  -H "Content-Type: application/json" \
  -d '{"durable":true,"arguments":{"x-queue-type":"quorum"}}'

# Verify queue creation
docker exec rabbitmq-cluster-node-1 rabbitmqctl list_queues name type arguments

# See the leader and followers (replicas) of the quorum queue
docker exec rabbitmq-cluster-node-1 rabbitmq-queues quorum_status test_quorum
```

> Quorum queues replicate every message to a majority of nodes using Raft. With
> 3 nodes, a quorum queue (and the cluster metadata store, Khepri) keeps working
> while **one** node is down; with two nodes down it becomes unavailable.

### Test Failover
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r ../../requirements.txt

# Create test queue and send messages
python3 test_cluster.py

# Stop one node and verify messages still flow
docker compose stop rabbit-2

# Check cluster status (rabbit-2 is listed as a disc node but not running)
docker exec rabbitmq-cluster-node-1 rabbitmqctl cluster_status

# The quorum queue elected a new leader if needed and is still available
docker exec rabbitmq-cluster-node-1 rabbitmq-queues quorum_status ha_test_queue

# Restart node
docker compose start rabbit-2
```

### Test Reliable Publishing
```bash
# Publisher confirms + mandatory flag: know that the broker stored AND routed a message
python3 test_reliable_publisher.py
```

## Load Balancing Test

### Connection Distribution
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Use the existing test_cluster.py which tests multiple connections
python test_cluster.py

# Check HAProxy stats to see load distribution
echo "Check HAProxy stats at: http://localhost:8080/stats"

# Verify load balancer is working by connecting through port 5671
curl -u admin:cluster123 -X POST http://localhost:15672/api/exchanges/%2F/amq.default/publish \
  -H "Content-Type: application/json" \
  -d '{"properties":{},"routing_key":"test_quorum","payload":"via load balancer","payload_encoding":"string"}'
```

## Monitoring

### Cluster Health
```bash
# Check all nodes health
for i in {1..3}; do
    echo "=== Node $i ==="
    docker exec rabbitmq-cluster-node-$i rabbitmqctl status
done

# Memory and disk usage
docker exec rabbitmq-cluster-node-1 rabbitmqctl status
```

### Queue Distribution
```bash
# Check queue replicas across nodes (for quorum queues)
docker exec rabbitmq-cluster-node-1 rabbitmqctl list_queues name type leader members
```

### Performance Metrics
```bash
# Message rates across cluster
docker exec rabbitmq-cluster-node-1 rabbitmqctl list_queues name messages_ready messages_unacknowledged
```

## Scaling Operations

### Add Node to Cluster
```bash
# Note: This setup doesn't support dynamic scaling
# To add nodes, modify docker-compose.yml and restart
echo "Dynamic scaling requires docker-compose.yml modification"
```

### Remove Node from Cluster
```bash
# Stop node gracefully
docker exec rabbitmq-cluster-node-3 rabbitmqctl stop_app

# Remove from cluster
docker exec rabbitmq-cluster-node-1 rabbitmqctl forget_cluster_node rabbit@rabbit-3

# Stop container
docker compose stop rabbit-3
```

### Alternative: Automatic Cluster Formation
`docker-compose.yml` forms the cluster with explicit `rabbitmqctl join_cluster`
commands, which makes the steps visible. In production, nodes discover each
other through **peer discovery** instead. `rabbitmq.conf` in this folder shows
the classic config backend (a static list of nodes), quorum as the default
queue type and balanced leader placement. To try it, mount it instead of
`rabbitmq-minimal.conf` and remove the `command:` blocks of rabbit-2 and rabbit-3.

## Troubleshooting

### Common Issues
```bash
# Check network connectivity between nodes
docker exec rabbitmq-cluster-node-1 ping rabbit-2

# Check Erlang cookie consistency
docker exec rabbitmq-cluster-node-1 cat /var/lib/rabbitmq/.erlang.cookie
docker exec rabbitmq-cluster-node-2 cat /var/lib/rabbitmq/.erlang.cookie

# Reset node if needed
docker exec rabbitmq-cluster-node-2 rabbitmqctl stop_app
docker exec rabbitmq-cluster-node-2 rabbitmqctl reset
docker exec rabbitmq-cluster-node-2 rabbitmqctl join_cluster rabbit@rabbit-1
docker exec rabbitmq-cluster-node-2 rabbitmqctl start_app
```

### Log Analysis
```bash
# Check logs for clustering issues
docker compose logs rabbit-1 | grep -i cluster
docker compose logs rabbit-2 | grep -i error
```

## Cleanup
```bash
# Stop cluster
docker compose down

# Remove volumes (optional)
docker compose down -v

```

## Key Concepts
- RabbitMQ clustering
- Quorum queues (replicated, highly available)
- Load balancing
- Failover mechanisms
- Cluster monitoring
- Node management