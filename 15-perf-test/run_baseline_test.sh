#!/bin/bash

echo "🚀 RabbitMQ Baseline Performance Test"
echo "====================================="

# Ensure network exists
docker network create rabbitmq_net 2>/dev/null || true

# Check if RabbitMQ is running
if ! docker ps | grep -q rabbitmq; then
    echo "Starting RabbitMQ..."
    docker run -d --name rabbitmq \
      --network rabbitmq_net \
      -p 5672:5672 \
      -p 15672:15672 \
      rabbitmq:3-management
    
    echo "Waiting for RabbitMQ to start..."
    sleep 30
fi

echo "Running baseline performance test..."
echo "Parameters:"
echo "  - Producers: 10"
echo "  - Consumers: 10" 
echo "  - Target rate: 2000 msg/s"
echo "  - Message size: 1024 bytes"
echo "  - Duration: 300 seconds (5 minutes)"
echo ""

docker run --rm --network rabbitmq_net pivotalrabbitmq/perf-test:latest \
  --uri amqp://guest:guest@rabbitmq \
  --producers 10 --consumers 10 \
  --rate 2000 --queue perf-test \
  --size 1024 --time 300

echo ""
echo "✅ Baseline test completed!"
echo "Check Management UI: http://localhost:15672"