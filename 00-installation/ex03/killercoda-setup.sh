#!/bin/bash

# RabbitMQ Kubernetes Setup Script for Killercoda
# This script automates the setup process for the Killercoda environment

set -e

echo "🐇 RabbitMQ Kubernetes Setup for Killercoda"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check cluster connectivity
print_status "Checking Kubernetes cluster connectivity..."
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster"
    exit 1
fi
print_success "Connected to Kubernetes cluster"

# Show cluster info
print_status "Cluster information:"
kubectl cluster-info
echo ""

# Check available storage classes
print_status "Available storage classes:"
kubectl get storageclass
echo ""

# Install RabbitMQ Cluster Operator
print_status "Installing RabbitMQ Cluster Operator..."
kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"

print_status "Waiting for operator to be ready..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=rabbitmq-cluster-operator -n rabbitmq-system --timeout=300s

print_success "RabbitMQ Cluster Operator installed successfully"

# Check operator status
print_status "Operator status:"
kubectl get pods -n rabbitmq-system
echo ""

# Deploy RabbitMQ cluster
print_status "Deploying RabbitMQ cluster..."
kubectl apply -f rabbitmq-cluster.yaml

print_status "Waiting for RabbitMQ cluster to be ready (this may take a few minutes)..."
kubectl wait --for=condition=Ready rabbitmqcluster/rabbitmq-cluster --timeout=600s

print_success "RabbitMQ cluster deployed successfully"

# Check cluster status
print_status "Cluster status:"
kubectl get rabbitmqclusters
kubectl get pods -l app.kubernetes.io/name=rabbitmq-cluster
echo ""

# Get credentials
print_status "Retrieving credentials..."
username=$(kubectl get secret rabbitmq-cluster-default-user -o jsonpath='{.data.username}' | base64 --decode)
password=$(kubectl get secret rabbitmq-cluster-default-user -o jsonpath='{.data.password}' | base64 --decode)

print_success "Credentials retrieved:"
echo "  Username: $username"
echo "  Password: $password"
echo ""

# Deploy test pod
print_status "Deploying test pod..."
kubectl apply -f test-pod.yaml

print_status "Waiting for test pod to be ready..."
kubectl wait --for=condition=Ready pod/rabbitmq-test --timeout=120s

print_success "Test pod deployed successfully"

# Test connection
print_status "Testing RabbitMQ connection..."
sleep 10  # Give some time for pika to install

# Test producer
kubectl exec rabbitmq-test -- python3 -c "
import pika
import os
import sys

try:
    username = os.environ.get('RABBITMQ_USERNAME')
    password = os.environ.get('RABBITMQ_PASSWORD')
    
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='rabbitmq-cluster',
            credentials=pika.PlainCredentials(username, password)
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue='k8s_test')
    channel.basic_publish(exchange='', routing_key='k8s_test', body='Hello from Kubernetes!')
    print('✅ Message sent successfully!')
    connection.close()
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

# Test consumer
kubectl exec rabbitmq-test -- python3 -c "
import pika
import os
import sys

try:
    username = os.environ.get('RABBITMQ_USERNAME')
    password = os.environ.get('RABBITMQ_PASSWORD')
    
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
        print(f'✅ Received: {body.decode()}')
    else:
        print('❌ No messages in queue')
    connection.close()
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

print_success "Connection test completed successfully!"

# Setup port forwarding
print_status "Setting up port forwarding..."

# Kill any existing port forwards
pkill -f "kubectl port-forward" 2>/dev/null || true

# Start port forwards in background
kubectl port-forward service/rabbitmq-cluster 15672:15672 &
kubectl port-forward service/rabbitmq-cluster 5672:5672 &

sleep 2

print_success "Setup completed successfully!"
echo ""
echo "🎉 RabbitMQ is now ready to use!"
echo ""
echo "📋 Access Information:"
echo "  Management UI: http://localhost:15672"
echo "  AMQP Endpoint: localhost:5672"
echo "  Username: $username"
echo "  Password: $password"
echo ""
echo "🧪 Quick Tests:"
echo "  kubectl get rabbitmqclusters"
echo "  kubectl get pods -l app.kubernetes.io/name=rabbitmq-cluster"
echo "  kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl cluster_status"
echo ""
echo "🔧 Useful Commands:"
echo "  kubectl logs rabbitmq-cluster-server-0"
echo "  kubectl exec -it rabbitmq-cluster-server-0 -- rabbitmqctl list_queues"
echo "  kubectl exec rabbitmq-test -- python3 -c \"import pika; print('Pika available')\""
echo ""
echo "🧹 Cleanup:"
echo "  kubectl delete -f test-pod.yaml"
echo "  kubectl delete -f rabbitmq-cluster.yaml"
echo "  kubectl delete -f https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"