@echo off

REM RabbitMQ Single Container Setup Script

echo 🐇 Starting RabbitMQ Single Container...

REM Stop existing container if running
docker stop rabbitmq-single 2>nul
docker rm rabbitmq-single 2>nul

REM Build custom RabbitMQ image with proper permissions
echo 🔨 Building custom RabbitMQ image...
docker build -t rabbitmq-single-fixed .

REM Run RabbitMQ container
docker run -d --name rabbitmq-single --hostname rabbitmq-single -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=password123 rabbitmq-single-fixed

echo ⏳ Waiting for RabbitMQ to start...
echo 📋 Initial container logs:
docker logs rabbitmq-single
echo.

REM Wait for RabbitMQ to be ready
set timeout=60
set counter=0

:wait_loop
if %counter% geq %timeout% goto timeout_error

REM Check if container is still running first
docker ps --format "table {{.Names}}" | findstr rabbitmq-single >nul
if errorlevel 1 (
    echo ❌ Container stopped unexpectedly
    docker logs rabbitmq-single
    exit /b 1
)

docker exec rabbitmq-single rabbitmqctl ping >nul 2>&1
if not errorlevel 1 (
    echo ✅ RabbitMQ is ready!
    echo.
    echo 🌐 Management UI: http://localhost:15672
    echo 👤 Username: admin
    echo 🔑 Password: password123
    echo.
    echo 📊 Quick status check:
    docker exec rabbitmq-single rabbitmqctl cluster_status
    exit /b 0
)

timeout /t 2 /nobreak >nul
set /a counter+=2
echo    Still waiting... (%counter%/%timeout% seconds)
goto wait_loop

:timeout_error
echo ❌ Timeout waiting for RabbitMQ to start
echo 📋 Container logs:
docker logs rabbitmq-single
exit /b 1