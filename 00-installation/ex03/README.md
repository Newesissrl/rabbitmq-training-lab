# Exercise 3: RabbitMQ Operator on Kubernetes (Killercoda)

## Description
Deploy RabbitMQ using the official RabbitMQ Cluster Operator on Kubernetes, designed for Killercoda playground environment.

## Prerequisites
- Kubernetes cluster: on Killercoda use the **Kubernetes playground**
  (https://killercoda.com/playgrounds/scenario/kubernetes), not the Ubuntu one
- Internet access from the cluster (the operator and cert-manager are installed from GitHub)
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

### 2. Install cert-manager
The RabbitMQ Cluster Operator (version 2.20 and later) uses an admission webhook
whose TLS certificate is issued by **cert-manager**. Without cert-manager the
operator pod stays in `ContainerCreating`
(`secret "cluster-operator-webhook-server-cert" not found`).
```bash
kubectl apply -f "https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml"
kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=300s
```

### 3. Install RabbitMQ Cluster Operator
```bash
# Install the operator
kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"

# Wait for operator to be ready
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=rabbitmq-cluster-operator -n rabbitmq-system --timeout=300s

# Check operator status
kubectl get pods -n rabbitmq-system
```

### 4. Deploy RabbitMQ Cluster
```bash
# Apply the RabbitMQ cluster configuration (RabbitMQ 4.3, 1 replica)
kubectl apply -f rabbitmq-cluster.yaml

# Wait for cluster to be ready
# (a RabbitmqCluster has the conditions AllReplicasReady, ClusterAvailable,
#  NoWarnings and ReconcileSuccess - there is no "Ready" condition)
kubectl wait --for=condition=AllReplicasReady rabbitmqcluster/rabbitmq-cluster --timeout=600s

# Check cluster status
kubectl get rabbitmqclusters
kubectl get pods -l app.kubernetes.io/name=rabbitmq-cluster

# Show all conditions (NoWarnings=False explains misconfigurations)
kubectl get rabbitmqcluster rabbitmq-cluster \
  -o jsonpath='{range .status.conditions[*]}{.type}={.status} {.message}{"\n"}{end}'
```

## Accessing RabbitMQ

### 1. Get Credentials
```bash
# This configuration uses hardcoded admin user (from rabbitmq-cluster.yaml)
echo "Username: admin"
echo "Password: killercoda123"

# Note: the operator still stores a generated user in the secret
# rabbitmq-cluster-default-user, but because RABBITMQ_DEFAULT_USER/PASS are set
# in rabbitmq-cluster.yaml, the node is initialised with admin/killercoda123 only.

# Verify only admin user exists
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl list_users
```

### 2. Access Management UI (Killercoda)
```bash
# The NodePort service exposes the Management UI on port 31672 of every node
kubectl get svc rabbitmq-cluster-external
```
In Killercoda open the menu (top right, ☰) → **Traffic / Ports**, enter **31672**
and click **Access**. Log in with `admin` / `killercoda123`.

Alternative, with a port-forward (bound to all interfaces so that the
Killercoda proxy can reach it), then open port **15672** in Traffic / Ports:
```bash
kubectl port-forward --address 0.0.0.0 service/rabbitmq-cluster 15672:15672 &
```
> On your own computer, drop `--address 0.0.0.0` and browse to http://localhost:15672.

### 3. Port Forward for AMQP
```bash
# Forward AMQP port (for client connections from the Killercoda VM)
kubectl port-forward service/rabbitmq-cluster 5672:5672 &

# Note: for pod-to-pod communication, use the service name 'rabbitmq-cluster:5672'
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
channel.queue_declare(queue='k8s_test', durable=True)
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
channel.queue_declare(queue='k8s_test', durable=True)

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

### 2. Scale Down Cluster (not supported)
```bash
# Try to scale down to 1 replica
kubectl patch rabbitmqcluster rabbitmq-cluster --type='merge' -p='{"spec":{"replicas":1}}'

# The operator refuses: pods stay at 3 and ReconcileSuccess becomes False
kubectl get rabbitmqcluster rabbitmq-cluster \
  -o jsonpath='{range .status.conditions[*]}{.type}={.status} {.message}{"\n"}{end}'
# ReconcileSuccess=False Cluster Scale down not supported; tried to scale cluster from 3 nodes to 1 nodes

# Revert to 3 replicas
kubectl patch rabbitmqcluster rabbitmq-cluster --type='merge' -p='{"spec":{"replicas":3}}'
```
Removing nodes would remove replicas of quorum queues and members of the Khepri
metadata store, so the operator does not do it automatically. Removing a node
is a manual, planned operation (`rabbitmq-queues shrink`, `rabbitmqctl forget_cluster_node`).

> **Killercoda:** each replica requests 768Mi of memory. The playground nodes are
> small: if new pods stay `Pending`, `kubectl describe pod rabbitmq-cluster-server-2`
> shows `Insufficient memory`; lower `resources` in `rabbitmq-cluster.yaml`
> (request and limit must stay equal) or stay at fewer replicas.

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
`rabbitmq-config.yaml` is a **merge patch** for the RabbitmqCluster: it replaces
`spec.rabbitmq.additionalConfig` (rabbitmq.conf content). The operator then
performs a rolling restart of the pods.
```bash
# Apply the patch
kubectl patch rabbitmqcluster rabbitmq-cluster --type merge --patch-file rabbitmq-config.yaml

# Watch the rolling restart
kubectl rollout status statefulset/rabbitmq-cluster-server

# Verify configuration update (user-defined config is in 90-userDefinedConfiguration.conf)
kubectl exec -it rabbitmq-cluster-server-0 -- cat /etc/rabbitmq/conf.d/90-userDefinedConfiguration.conf

# Quorum is now the default queue type
kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl eval 'rabbit_queue_type:default_alias().'
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

# Delete operator and cert-manager (optional)
kubectl delete -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"
kubectl delete -f "https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml"

# Stop port forwards
pkill -f "kubectl port-forward"
```

## Troubleshooting

### Common Issues

#### Operator pod stuck in ContainerCreating
```bash
kubectl describe pod -n rabbitmq-system -l app.kubernetes.io/name=rabbitmq-cluster-operator
# MountVolume.SetUp failed ... secret "cluster-operator-webhook-server-cert" not found
# -> cert-manager is missing: install it (step 2), the operator then starts
```

#### Storage Issues (Killercoda)
```bash
# Check if PVC is bound
kubectl get pvc

# If PVC shows "Pending", check storage class
kubectl get storageclass

# Ensure a default storage class exists (local-path on Killercoda and kind)
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