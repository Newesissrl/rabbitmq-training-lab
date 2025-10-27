# Exercise 3: RabbitMQ Operator on Kubernetes (Killercoda)

## Description
Deploy RabbitMQ using the official RabbitMQ Cluster Operator on Kubernetes, designed for Killercoda playground environment.

## Prerequisites
- Kubernetes cluster (Killercoda provides this)
- kubectl configured
- Basic understanding of Kubernetes concepts

## Killercoda Setup

### 1. Verify Kubernetes Cluster
**Linux/macOS/Windows:**
```bash
# Check cluster status
kubectl cluster-info

# Check nodes
kubectl get nodes

# Check available storage classes
kubectl get storageclass
```
**Or use setup script:**
```bash
./killercoda-setup.sh
```
```cmd
killercoda-setup.cmd
```

### 2. Install RabbitMQ Cluster Operator
```bash
# Install the operator
kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"

# Wait for operator to be ready
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=rabbitmq-cluster-operator -n rabbitmq-system --timeout=300s

# Check operator status
kubectl get pods -n rabbitmq-system
```

### 3. Deploy RabbitMQ Cluster
```bash
# Apply the RabbitMQ cluster configuration
kubectl apply -f rabbitmq-cluster.yaml

# Wait for cluster to be ready
kubectl wait --for=condition=Ready rabbitmqcluster/rabbitmq-cluster --timeout=600s

# Check cluster status
kubectl get rabbitmqclusters
kubectl get pods -l app.kubernetes.io/name=rabbitmq-cluster
```

## Accessing RabbitMQ

### 1. Get Credentials
```bash
# This configuration uses hardcoded admin user (from rabbitmq-cluster.yaml)
echo "Username: admin"
echo "Password: killercoda123"

# Note: No operator-generated user is created because we override with RABBITMQ_DEFAULT_USER
# The operator only creates default user when no custom user is specified

# Verify only admin user exists
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl list_users
```

### 2. Access Management UI (Killercoda)
```bash
# Killercoda works better with NodePort - use the external service
kubectl get svc rabbitmq-cluster-external

# Get the NodePort for management UI (should be 31672)
NODE_PORT=$(kubectl get svc rabbitmq-cluster-external -o jsonpath='{.spec.ports[?(@.name=="management")].nodePort}')
echo "Management UI available at: https://$(hostname -I | awk '{print $1}'):$NODE_PORT"

# Alternative: If NodePort doesn't work, try port-forward
# kubectl port-forward pod/rabbitmq-cluster-server-0 15672:15672 &

echo "Use admin/killercoda123 for Management UI"
```

### 3. Port Forward for AMQP
```bash
# Forward AMQP port (for external client connections)
kubectl port-forward service/rabbitmq-cluster 5672:5672 &

# Note: For pod-to-pod communication, use service name 'rabbitmq-cluster:5672'
echo "AMQP endpoint: rabbitmq-cluster:5672 (internal) or Killercoda URL (external)"
```

## Testing the Deployment

### 1. Run Test Pod
```bash
# Deploy test pod
kubectl apply -f test-pod.yaml

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/rabbitmq-test --timeout=120s

# Check pod status
kubectl get pod rabbitmq-test
```

### 2. Test Connection from Pod
```bash
# Test producer
kubectl exec rabbitmq-test -- python3 -c "
import pika
import os

# Get credentials from environment
username = os.environ.get('RABBITMQ_USERNAME', 'admin')
password = os.environ.get('RABBITMQ_PASSWORD', 'killercoda123')

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='rabbitmq-cluster',
        credentials=pika.PlainCredentials(username, password)
    )
)
channel = connection.channel()
channel.queue_declare(queue='k8s_test')
channel.basic_publish(exchange='', routing_key='k8s_test', body='Hello from Kubernetes!')
print('Message sent successfully!')
connection.close()
"

# Test consumer
kubectl exec rabbitmq-test -- python3 -c "
import pika
import os

username = os.environ.get('RABBITMQ_USERNAME', 'admin')
password = os.environ.get('RABBITMQ_PASSWORD', 'killercoda123')

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='rabbitmq-cluster',
        credentials=pika.PlainCredentials(username, password)
    )
)
channel = connection.channel()
channel.queue_declare(queue='k8s_test')

method_frame, header_frame, body = channel.basic_get(queue='k8s_test', auto_ack=True)
if method_frame:
    print(f'Received: {body.decode()}')
else:
    print('No messages in queue')
connection.close()
"
```

## Monitoring and Operations

### 1. Check Cluster Health
```bash
# Check RabbitMQ cluster status
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl cluster_status

# Check node health
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl status

# List queues
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl list_queues

# Check user permissions
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl list_users
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl list_user_permissions admin

# Note: No operator-generated user exists in this configuration
# Only the hardcoded admin user is available
echo "Only admin user exists (no operator-generated user)"
```

### 2. Monitor Resources
```bash
# Check pod resources
kubectl top pods -l app.kubernetes.io/name=rabbitmq-cluster

# Check persistent volumes
kubectl get pv,pvc

# Check services
kubectl get svc -l app.kubernetes.io/name=rabbitmq-cluster
```

### 3. View Logs
```bash
# Check operator logs
kubectl logs -n rabbitmq-system -l app.kubernetes.io/name=rabbitmq-cluster-operator

# Check RabbitMQ logs
kubectl logs rabbitmq-cluster-server-0

# Follow logs
kubectl logs -f rabbitmq-cluster-server-0
```

## Scaling Operations

### 1. Scale Up Cluster
```bash
# Edit cluster to add more replicas
kubectl patch rabbitmqcluster rabbitmq-cluster --type='merge' -p='{"spec":{"replicas":3}}'

# Wait for new pods
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=rabbitmq-cluster --timeout=300s

# Verify scaling
kubectl get pods -l app.kubernetes.io/name=rabbitmq-cluster
```

### 2. Scale Down Cluster
```bash
# Scale down to 1 replica
kubectl patch rabbitmqcluster rabbitmq-cluster --type='merge' -p='{"spec":{"replicas":1}}'

# Monitor scaling down
kubectl get pods -l app.kubernetes.io/name=rabbitmq-cluster -w
```

## High Availability Testing

### 1. Pod Failure Simulation
```bash
# Delete a pod to test recovery
kubectl delete pod rabbitmq-cluster-server-0

# Watch pod recreation
kubectl get pods -l app.kubernetes.io/name=rabbitmq-cluster -w

# Verify cluster health after recovery
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl cluster_status
```

### 2. Node Failure Simulation (if multi-node)
```bash
# Cordon a node
kubectl cordon <node-name>

# Drain the node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Watch pod rescheduling
kubectl get pods -l app.kubernetes.io/name=rabbitmq-cluster -o wide -w
```

## Configuration Management

### 1. Update RabbitMQ Configuration
```bash
# Create custom configuration
kubectl apply -f rabbitmq-config.yaml

# Update cluster to use custom config
kubectl patch rabbitmqcluster rabbitmq-cluster --type='merge' -p='{"spec":{"rabbitmq":{"additionalConfig":"custom-rabbitmq-config"}}}'

# Verify configuration update
kubectl exec -it rabbitmq-cluster-server-0 -- cat /etc/rabbitmq/rabbitmq.conf
```

### 2. Plugin Management
```bash
# Enable additional plugins
kubectl patch rabbitmqcluster rabbitmq-cluster --type='merge' -p='{"spec":{"rabbitmq":{"additionalPlugins":["rabbitmq_shovel","rabbitmq_federation"]}}}'

# Check enabled plugins
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmq-plugins list
```

## Cleanup
```bash
# Delete test resources
kubectl delete -f test-pod.yaml

# Delete RabbitMQ cluster
kubectl delete -f rabbitmq-cluster.yaml

# Delete operator (optional)
kubectl delete -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"

# Stop port forwards
pkill -f "kubectl port-forward"
```

## Troubleshooting

### Common Issues

#### Storage Issues (Killercoda)
```bash
# Check if PVC is bound
kubectl get pvc

# If PVC shows "Pending", check storage class
kubectl get storageclass

# Ensure using correct storage class (local-path for Killercoda)
kubectl describe pvc rabbitmq-cluster-server-0

# Check pod events for storage issues
kubectl describe pod rabbitmq-cluster-server-0
```

#### General Issues
```bash
# Check operator events
kubectl get events -n rabbitmq-system --sort-by='.lastTimestamp'

# Check cluster events
kubectl get events --field-selector involvedObject.name=rabbitmq-cluster

# Check pod events
kubectl describe pod rabbitmq-cluster-server-0
```

### Resource Issues
```bash
# Check resource limits
kubectl describe rabbitmqcluster rabbitmq-cluster

# Check node resources
kubectl describe nodes

# Check storage class
kubectl describe storageclass
```

## Key Concepts
- Kubernetes Operators
- Custom Resource Definitions (CRDs)
- StatefulSets for stateful applications
- Persistent Volume Claims (PVCs)
- Service discovery in Kubernetes
- Pod lifecycle management
- Cluster scaling and healing