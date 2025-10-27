# RabbitMQ Training Exercises

This repository contains hands-on exercises to learn RabbitMQ exchange types and messaging patterns.

## Prerequisites

- Python 3.7+
- Docker or Podman

## Setup

### 1. Create Python Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv rabbitmq-env
source rabbitmq-env/bin/activate
```

**Windows:**
```cmd
python -m venv rabbitmq-env
rabbitmq-env\Scripts\activate
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start RabbitMQ Container

**Using Docker:**
```bash
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

**Using Podman:**
```bash
podman run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

### 4. Access RabbitMQ Management UI

Open http://localhost:15672 in your browser
- Username: `guest`
- Password: `guest`

## Exercises

| Exercise | Exchange Type | Concept |
|----------|---------------|---------|
| [01-direct](./01-direct/) | Direct | Point-to-point messaging with routing keys |
| [02-fanout](./02-fanout/) | Fanout | Broadcast messaging to all queues |
| [03-topic](./03-topic/) | Topic | Pattern-based routing with wildcards |
| [04-headers](./04-headers/) | Headers | Attribute-based routing |
| [05-default](./05-default/) | Default | Direct exchange behavior |
| [06-dead-letter](./06-dead-letter/) | Direct + DLX | Dead letter exchange handling |
| [07-ttl-non-durable](./07-ttl-non-durable/) | Direct | Message TTL and non-durable components |
| [08-durability](./08-durability/) | Direct | Persistent vs non-persistent components |
| [09-exchange-to-exchange](./09-exchange-to-exchange/) | Fanout | Exchange-to-exchange binding for message duplication |
| [10-shared-queues](./10-shared-queues/) | Default | Shared queues for load balancing and work distribution |
| [13-connection-pooling](./13-connection-pooling/) | N/A | Connection pooling and channels vs multiple connections |
| [14-message-formats](./14-message-formats/) | N/A | Message formats and serialization with MessagePack |
| [15-perf-test](./15-perf-test/) | N/A | Performance testing with official RabbitMQ PerfTest tool |

## Running Exercises

Each exercise folder contains:
- `producer.py` - Sends messages
- `consumer.py` - Receives messages  
- `README.md` - Specific instructions

Navigate to each exercise folder and follow the README instructions.

## Cleanup

```bash
# Stop and remove container
docker stop rabbitmq && docker rm rabbitmq
# or
podman stop rabbitmq && podman rm rabbitmq

# Deactivate virtual environment
deactivate
```