@echo off

echo 🚀 RabbitMQ Baseline Performance Test
echo =====================================

REM Start RabbitMQ 4.3 from the repository docker-compose.yml if it is not running
docker ps --format "{{.Names}}" | findstr /x rabbitmq >nul
if errorlevel 1 (
    echo Starting RabbitMQ (docker compose^)...
    docker compose -f "%~dp0..\docker-compose.yml" up -d --wait
)

REM Make sure the broker is reachable from the PerfTest container
docker network create rabbitmq_net 2>nul
docker network connect rabbitmq_net rabbitmq 2>nul

echo Running baseline performance test...
echo Parameters:
echo   - Producers: 10
echo   - Consumers: 10
echo   - Target rate: 2000 msg/s
echo   - Message size: 1024 bytes
echo   - Duration: 300 seconds (5 minutes)
echo.

docker run --rm --network rabbitmq_net pivotalrabbitmq/perf-test:latest --uri amqp://guest:guest@rabbitmq --producers 10 --consumers 10 --rate 2000 --queue perf-test --size 1024 --time 300

echo.
echo ✅ Baseline test completed!
echo Check Management UI: http://localhost:15672