# Exercise 1: Direct Exchange

## Concept
Direct exchanges route messages to queues based on exact routing key matches.

## Learning Objectives
- Understand point-to-point messaging
- Learn routing key matching
- Practice selective message delivery

## Setup
1. Start RabbitMQ container (see main README)
2. Run consumers with specific routing keys:
   ```bash
   python consumer.py error    # Terminal 1 - receives only error messages
   python consumer.py info     # Terminal 2 - receives only info messages  
   python consumer.py warning  # Terminal 3 - receives only warning messages
   ```
3. Run producer (no parameters needed): `python producer.py`

## Expected Behavior
- Messages with routing key "error" go to error queue
- Messages with routing key "info" go to info queue
- Messages with routing key "warning" go to warning queue
- Each consumer only receives messages for their routing key

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `logs_direct` exchange with type "direct"
- Click exchange name → see bindings to consumer queues

**Queues Tab:**
- Auto-generated queue names (amq.gen-xxx) for each consumer
- Message rates and queue lengths
- Click queue name → see bindings and messages

**What You Should See:**
- Each consumer creates a unique queue
- Queues bound to exchange with specific routing keys
- Messages delivered only to matching routing key queues
- Real-time message flow and delivery rates

## Experiment
- Start multiple consumers with different routing keys
- Observe selective message delivery in real-time
- Check queue bindings and message routing in Web UI