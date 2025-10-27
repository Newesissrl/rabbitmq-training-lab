#!/bin/bash

# RabbitMQ Single Container Setup Script

echo "🐇 Starting RabbitMQ Single Container..."

# Stop existing container if running
docker stop rabbitmq-single 2>/dev/null || true
docker rm rabbitmq-single 2>/dev/null || true



# Build custom RabbitMQ image with proper permissions
echo "🔨 Building custom RabbitMQ image..."
docker build -t rabbitmq-single-fixed .

# Run RabbitMQ container
docker run -d \
  --name rabbitmq-single \
  --hostname rabbitmq-single \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=password123 \
  rabbitmq-single-fixed

echo "⏳ Waiting for RabbitMQ to start..."
echo "📋 Initial container logs:"
docker logs rabbitmq-single
echo ""

# Wait for RabbitMQ to be ready
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    # Check if container is still running first
    if ! docker ps --format "table {{.Names}}" | grep -q "rabbitmq-single"; then
        echo "❌ Container stopped unexpectedly"
        docker logs rabbitmq-single
        exit 1
    fi
    
    if docker exec rabbitmq-single rabbitmqctl ping >/dev/null 2>&1; then
        echo "✅ RabbitMQ is ready!"
        echo ""
        echo "🌐 Management UI: http://localhost:15672"
        echo "👤 Username: admin"
        echo "🔑 Password: password123"
        echo ""
        echo "📊 Quick status check:"
        docker exec rabbitmq-single rabbitmqctl cluster_status
        exit 0
    fi
    sleep 2
    counter=$((counter + 2))
    echo "   Still waiting... ($counter/$timeout seconds)"
done

echo "❌ Timeout waiting for RabbitMQ to start"
echo "📋 Container logs:"
docker logs rabbitmq-single
exit 1