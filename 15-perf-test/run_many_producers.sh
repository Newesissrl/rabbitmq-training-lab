#!/bin/bash

echo "👥 RabbitMQ Many Producers Test"
echo "==============================="

docker network create rabbitmq_net 2>/dev/null || true
# Make sure the broker (container "rabbitmq") is reachable from PerfTest
docker network connect rabbitmq_net rabbitmq 2>/dev/null || true

echo "Running many producers test..."
echo "Parameters:"
echo "  - Producers: 50"
echo "  - Consumers: 5"
echo "  - Target rate: 5000 msg/s"
echo "  - Message size: 256 bytes"
echo "  - Duration: 120 seconds (2 minutes)"
echo ""

docker run --rm --network rabbitmq_net pivotalrabbitmq/perf-test:latest \
  --uri amqp://guest:guest@rabbitmq \
  --producers 50 --consumers 5 \
  --rate 5000 --queue many-producers-test \
  --size 256 --time 120

echo ""
echo "✅ Many producers test completed!"