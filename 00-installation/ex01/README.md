# Exercise 1: Single Docker Container Setup

## Description
Set up a single RabbitMQ instance using Docker with management UI enabled.

## Prerequisites
- Docker installed and running
- Basic knowledge of Docker commands

## Setup Instructions

### 1. Run RabbitMQ Container
**Linux/macOS:**
```bash
docker run -d \
  --name rabbitmq-single \
  --hostname rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=password123 \
  rabbitmq:4.3-management
```
**Windows:**
```cmd
docker run -d --name rabbitmq-single --hostname rabbitmq -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=password123 rabbitmq:4.3-management
```
**Or use script:**
```bash
./docker-run.sh
```
```cmd
docker-run.cmd
```

### 2. Verify Installation
```bash
# Check container status
docker ps | grep rabbitmq-single

# Check logs
docker logs rabbitmq-single

# Wait for startup (look for "Server startup complete")
docker logs -f rabbitmq-single
```

### 3. Access Management UI
- URL: http://localhost:15672
- Username: admin
- Password: password123

## Testing Connection

### Create Test Script
```bash
# Create test directory
mkdir rabbitmq-test && cd rabbitmq-test

# Create test producer
cat > test_producer.py << 'EOF'
import pika
import sys

try:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            credentials=pika.PlainCredentials('admin', 'password123')
        )
    )
    channel = connection.channel()
    
    channel.queue_declare(queue='test_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='test_queue',
        body='Hello RabbitMQ!'
    )
    
    print(" [x] Sent 'Hello RabbitMQ!'")
    connection.close()
    
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
EOF

# Create test consumer
cat > test_consumer.py << 'EOF'
import pika
import sys

def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

try:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            credentials=pika.PlainCredentials('admin', 'password123')
        )
    )
    channel = connection.channel()
    
    channel.queue_declare(queue='test_queue', durable=True)
    channel.basic_consume(
        queue='test_queue',
        on_message_callback=callback
    )
    
    print(' [*] Waiting for messages. CTRL+C to exit')
    channel.start_consuming()
    
except KeyboardInterrupt:
    print('\n [!] Interrupted')
    channel.stop_consuming()
    connection.close()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
EOF
```

### Run Tests
```bash
# Install pika if needed
pip install pika

# Run producer
python test_producer.py

# Run consumer (in another terminal)
python test_consumer.py
```

## Monitoring

### CLI Commands
```bash
# List queues
docker exec rabbitmq-single rabbitmqctl list_queues

# List exchanges
docker exec rabbitmq-single rabbitmqctl list_exchanges

# Check cluster status
docker exec rabbitmq-single rabbitmqctl cluster_status

# Node status
docker exec rabbitmq-single rabbitmqctl status
```

### Management UI Features
- Overview dashboard
- Connections and channels
- Exchanges and queues
- Admin panel for users and vhosts

## Cleanup
```bash
# Stop and remove container
docker stop rabbitmq-single
docker rm rabbitmq-single

# Remove test files
rm -rf rabbitmq-test
```

## Key Concepts
- Single-node RabbitMQ deployment
- Docker container management
- Basic authentication setup
- Management UI access
- Connection testing