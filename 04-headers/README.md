# Exercise 4: Headers Exchange

## Concept
Headers exchanges route messages based on message headers instead of routing keys.
Supports "any" (OR) and "all" (AND) matching modes.

## Learning Objectives
- Understand header-based routing
- Learn x-match argument usage
- Practice complex message filtering

## Setup
1. Start RabbitMQ container (see main README)
2. Run consumer (no parameters needed):
   ```bash
   python consumer.py  # Creates 3 queues with different header bindings
   ```
   The consumer automatically creates:
   - `error_queue` - matches messages with type='error'
   - `database_queue` - matches messages with source='database'
   - `production_queue` - matches messages with environment='production' AND service='payment'
3. Run producer (no parameters needed): `python producer.py`

## Header Matching
- `x-match: all` - All specified headers must match
- `x-match: any` - At least one header must match

## Example Headers
- `type: error, source: database`
- `type: info, source: api, priority: high`
- `environment: production, service: payment`

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Exchanges Tab:**
- `headers_exchange` exchange with type "headers"
- Click exchange name → see bindings with header arguments

**Queues Tab:**
- `error_queue` - receives messages with type='error'
- `database_queue` - receives messages with source='database'
- `production_queue` - receives messages with environment='production' AND service='payment'

**What You Should See:**
- Bindings show x-match and header criteria
- Messages routed based on header matching, not routing keys
- Different x-match modes (all vs any) affect delivery
- Message headers visible in queue message details

**Header Matching Examples:**
- `error_queue` gets messages with headers containing type='error'
- `database_queue` gets messages with headers containing source='database'
- `production_queue` only gets messages matching BOTH environment='production' AND service='payment'

## Experiment
- Observe how x-match 'all' vs 'any' affects message delivery
- Check message details to see header content
- Watch selective delivery based on header combinations