#!/bin/bash

echo "📦 RabbitMQ Large Messages Test"
echo "==============================="

docker network create rabbitmq_net 2>/dev/null || true

echo "Running large messages test..."
echo "Parameters:"
echo "  - Producers: 5"
echo "  - Consumers: 5"
echo "  - Target rate: 500 msg/s"
echo "  - Message size: 10240 bytes (10KB)"
echo "  - Duration: 180 seconds (3 minutes)"
echo ""

docker run --rm --network rabbitmq_net pivotalrabbitmq/perf-test:latest \
  --uri amqp://guest:guest@rabbitmq \
  --producers 5 --consumers 5 \
  --rate 500 --queue large-messages-test \
  --size 10240 --time 180

echo ""
echo "✅ Large messages test completed!"