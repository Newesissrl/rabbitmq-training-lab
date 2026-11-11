# RabbitMQ Training Exercises

This repository contains hands-on exercises to learn RabbitMQ exchange types,
messaging patterns and operations. All exercises target **RabbitMQ 4.3**.

You can run the exercises:
- **On your computer** (Option A), if you can install Docker and Python, or
- **In the browser on [Killercoda](https://killercoda.com)** (Option B), if you
  cannot run them locally (company laptop restrictions, no Docker, not enough RAM...).

## Prerequisites (local computer)

- Python 3.10+
- Docker (with the `docker compose` plugin) or Podman
- Git

## Option A: Setup on Your Computer

### 1. Get the Code
```bash
git clone https://github.com/Newesissrl/rabbitmq-training-lab.git
cd rabbitmq-training-lab
```

### 2. Create Python Virtual Environment

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

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```
This installs `pika` (AMQP 0-9-1 client), `rstream` (Stream protocol client,
exercises 11-12) and `msgpack` (exercise 14).

### 4. Start RabbitMQ 4.3

**Recommended - Docker Compose** (from the repository root):
```bash
docker compose up -d
```
This starts a container named `rabbitmq` with the management, Prometheus and
stream plugins enabled ([config/](./config/)) and publishes the ports used by
all exercises:

| Port | Protocol |
|------|----------|
| 5672 | AMQP 0-9-1 (pika) |
| 5552 | Stream protocol (exercises 11-12) |
| 15672 | Management UI and HTTP API |
| 15692 | Prometheus metrics (exercise 18) |

**Alternative - plain Docker or Podman:**
```bash
docker run -d --name rabbitmq \
  -p 5672:5672 -p 5552:5552 -p 15672:15672 -p 15692:15692 \
  rabbitmq:4.3-management

# Streams (exercises 11-12) need the stream plugin:
docker exec rabbitmq rabbitmq-plugins enable rabbitmq_stream rabbitmq_stream_management
```
Replace `docker` with `podman` if you use Podman.

### 5. Access RabbitMQ Management UI

Open http://localhost:15672 in your browser
- Username: `guest`
- Password: `guest`

## Option B: Run the Exercises on Killercoda

[Killercoda](https://killercoda.com) gives you a disposable Linux VM in the
browser, with root access, Docker and Internet access. Nothing is installed on
your computer.

### Free vs PLUS account

| | Free account | PLUS (paid) |
|---|---|---|
| Session length | 1 hour per scenario | up to 4 hours per scenario |
| Concurrent sessions | 1 | up to 3 |
| Other | - | no CAPTCHA, faster load times, remote desktop for playgrounds |

> Plans and limits change over time: check https://killercoda.com/pricing.

**Everything is deleted when the session ends.** With a free account, plan the
1-hour session: run the setup below (about 3 minutes), then do 2-4 exercises.
When the session expires, start a new one and run the setup again.
With PLUS you can do a whole module in one session, and keep a second session
open (for example the Kubernetes playground for exercise `00-installation/ex03`).

### 1. Start an Ubuntu Playground
1. Log in at https://killercoda.com (or create a free account)
2. Open **Playgrounds** → **Ubuntu** (https://killercoda.com/playgrounds/scenario/ubuntu)
3. Wait for the terminal prompt (you are `root`)

### 2. Set Up the Lab (copy and paste)
```bash
# Python virtual environments (the playground runs Ubuntu 24.04 with Python 3.12)
apt update && apt install -y python3.12-venv

# Get the exercises
git clone https://github.com/Newesissrl/rabbitmq-training-lab.git
cd rabbitmq-training-lab

# Python environment and dependencies
python3 -m venv rabbitmq-env
source rabbitmq-env/bin/activate
pip3 install -r requirements.txt

# Start RabbitMQ 4.3
docker compose up -d --wait
```
If `docker` is not available in your playground, install it first with
`curl -fsSL https://get.docker.com | sh` and repeat the last command.

### 3. Open the Management UI
1. Open the menu at the top right of the Killercoda page (☰) → **Traffic / Ports**
2. Type **15672** in the port field and click **Access**: a new browser tab opens
   on a `...killercoda.com` URL
3. Log in with `guest` / `guest`

Use the same menu for other web ports (9090 Prometheus and 3000 Grafana in
exercise 18). Instructions that say "open http://localhost:15672" mean this URL
on Killercoda.

### 4. Work with Several Terminals
Most exercises need a producer and one or more consumers at the same time:
- Open an additional terminal tab, if the playground offers one, **or**
- Run `tmux` (install with `apt install -y tmux` if missing): `Ctrl+b %` splits
  the window, `Ctrl+b` + arrow keys moves between panes, `Ctrl+b c` opens a new window

In **every new terminal** activate the environment again:
```bash
cd ~/rabbitmq-training-lab && source rabbitmq-env/bin/activate
```

### 5. Killercoda Tips
- The VM is small: for the performance tests (exercise 15) use shorter runs
  and lower rates, and watch `docker stats`
- To keep your changes, commit and push them to your own fork before the session ends

### Option C: Kubernetes Exercise on Killercoda
Exercise [00-installation/ex03](./00-installation/ex03/) needs Kubernetes:
use the **Kubernetes** playground (https://killercoda.com/playgrounds/scenario/kubernetes)
instead of Ubuntu, then:
```bash
git clone https://github.com/Newesissrl/rabbitmq-training-lab.git
cd rabbitmq-training-lab/00-installation/ex03
./killercoda-setup.sh
```

## Exercises

| Exercise | Exchange Type | Concept |
|----------|---------------|---------|
| [00-installation](./00-installation/) | N/A | Single container, 3-node cluster with Docker Compose, Kubernetes operator |
| [01-direct](./01-direct/) | Direct | Point-to-point messaging with routing keys |
| [02-fanout](./02-fanout/) | Fanout | Broadcast messaging to all queues |
| [03-topic](./03-topic/) | Topic | Pattern-based routing with wildcards |
| [04-headers](./04-headers/) | Headers | Attribute-based routing |
| [05-default](./05-default/) | Default | Direct exchange behavior |
| [06-dead-letter](./06-dead-letter/) | Direct + DLX | Dead letter exchange handling |
| [07-ttl-non-durable](./07-ttl-non-durable/) | Direct | Message TTL and temporary (auto-delete) queues |
| [08-durability](./08-durability/) | Direct | Durable queues vs persistent messages (and what RabbitMQ 4.3 changed) |
| [09-exchange-to-exchange](./09-exchange-to-exchange/) | Fanout | Exchange-to-exchange binding for message duplication |
| [10-shared-queues](./10-shared-queues/) | Default | Shared queues for load balancing and work distribution |
| [11-streams](./11-streams/) | Streams | Append-only logs, offsets, replay and server-side filtering |
| [12-super-streams](./12-super-streams/) | Super Streams | Partitioned streams and single active consumer |
| [13-connection-pooling](./13-connection-pooling/) | N/A | Connection pooling and channels vs multiple connections |
| [14-message-formats](./14-message-formats/) | N/A | Message formats and serialization with MessagePack |
| [15-perf-test](./15-perf-test/) | N/A | Performance testing with official RabbitMQ PerfTest tool |
| [16-failure-drill](./16-failure-drill/) | N/A | Broker restart, consumer crash and resource alarm drills |
| [17-security](./17-security/) | N/A | Virtual hosts, users, permissions and least privilege |
| [18-monitoring](./18-monitoring/) | N/A | Health checks, HTTP API and Prometheus metrics |

## Running Exercises

Each exercise folder contains:
- `producer.py` - Sends messages
- `consumer.py` - Receives messages
- `README.md` - Specific instructions

Navigate to each exercise folder and follow the README instructions.

### RabbitMQ 4.3 notes
- **Queues shared between connections must be durable.** RabbitMQ 4.3 rejects
  non-durable, non-exclusive queues (`transient_nonexcl_queues` is denied by
  default). Use `durable=True`, or `exclusive=True` / `auto_delete=True` /
  `x-expires` for temporary queues (exercises 07-09).
- **Quorum queues** are the replicated queue type for high availability
  (they replace the old mirrored classic queues).
- All metadata is stored in **Khepri** (Raft based): a cluster needs a majority
  of its nodes online.

## Cleanup

```bash
# Stop RabbitMQ and delete its data (from the repository root)
docker compose down -v

# If you used plain docker run
docker stop rabbitmq && docker rm rabbitmq
# or
podman stop rabbitmq && podman rm rabbitmq

# Deactivate virtual environment
deactivate
```
