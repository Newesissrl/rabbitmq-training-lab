# Exercise 3: Topic Exchange

## Concept
Topic exchanges route messages based on pattern matching with wildcards:
- `*` matches exactly one word (between dots)
- `#` matches zero or more words (between dots)
- Routing keys are dot-separated words (e.g., "user.login.success")
- Pattern matching works on routing key structure, not message content

## Learning Objectives
- Understand pattern-based routing
- Learn wildcard usage (* and #)
- Practice flexible message filtering

## Setup
1. Start RabbitMQ container (see main README)
2. Run consumers with different binding patterns:
   ```bash
   python consumer.py "*.error"      # Terminal 1 - all error messages
   python consumer.py "user.#"       # Terminal 2 - all user-related messages
   python consumer.py "system.*.*"   # Terminal 3 - system messages (3 parts)
   python consumer.py "app.payment.*" # Terminal 4 - payment-related messages
   ```
3. Run producer (no parameters needed): `python producer.py`

## Routing Key Patterns
- `user.login.success` - User login events (3 parts)
- `user.logout.info` - User logout events (3 parts)
- `system.error` - System errors (2 parts)
- `app.error` - App errors (2 parts)
- `database.connection.error` - Database errors (3 parts)

## Example Bindings
- `*.error` - Error messages with exactly 2 parts (something.error)
- `#.error` - Error messages with any number of parts (ends with .error)
- `user.#` - All user-related messages (starts with user.)
- `system.*.*` - System messages with exactly 3 parts

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `topic_logs` exchange with type "topic"
- Click exchange name → see bindings with wildcard patterns

**Queues Tab:**
- Consumer queues with different message delivery patterns
- Queue bound to `*.error` receives all error messages
- Queue bound to `user.#` receives all user.* messages

**What You Should See:**
- Bindings show wildcard patterns (* and #)
- Messages routed based on pattern matching
- Different queues receive different message subsets
- Routing key patterns determine message distribution

**Test Pattern Matching:**
- `*.error` consumer gets: `system.error`, `app.error` (exactly 2 parts)
- `*.error` consumer does NOT get: `database.connection.error` (3 parts, not 2)
- `user.#` consumer gets: `user.login.success`, `user.logout.info`, `user.register.success`
- `system.*.*` consumer gets: `system.memory.warning` (3 parts starting with system)
- `#.error` consumer gets: `system.error`, `app.error`, `database.connection.error` (any parts ending with error)

## Experiment
- Try different binding patterns and observe selective delivery
- Watch how wildcards affect message routing in real-time
- Compare message counts between different pattern consumers