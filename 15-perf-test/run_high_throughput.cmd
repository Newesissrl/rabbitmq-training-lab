@echo off

echo ⚡ RabbitMQ High Throughput Test
echo ===============================

docker network create rabbitmq_net 2>nul

echo Running high throughput test...
echo Parameters:
echo   - Producers: 20
echo   - Consumers: 20
echo   - Target rate: 10000 msg/s
echo   - Message size: 512 bytes
echo   - Duration: 180 seconds (3 minutes)
echo.

docker run --rm --network rabbitmq_net pivotalrabbitmq/perf-test:latest --uri amqp://guest:guest@rabbitmq --producers 20 --consumers 20 --rate 10000 --queue high-throughput-test --size 512 --time 180

echo.
echo ✅ High throughput test completed!