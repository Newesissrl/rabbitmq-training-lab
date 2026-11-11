# Exercise 11: Connection Pooling and Channels

## Concept
Demonstrates efficient connection management in RabbitMQ:
- **Connection Pooling:** Reuse connections across multiple operations
- **Channels:** Lightweight virtual connections within a single connection
- **Performance:** Compare single vs multiple connections vs channels
- **Resource Management:** Proper connection lifecycle management

## Learning Objectives
- Understand connection vs channel concepts
- Learn when to use connection pooling
- Practice efficient resource management
- Measure performance differences between approaches

## Connection vs Channel
| Aspect | Connection | Channel |
|--------|------------|---------|
| **Resource Cost** | Heavy (TCP connection) | Light (virtual connection) |
| **Thread Safety** | Not thread-safe | Not thread-safe |
| **Multiplexing** | One per TCP connection | Multiple per connection |
| **Use Case** | Long-lived, shared | Per-thread, per-operation |

## Setup
1. Start RabbitMQ container (see main README)
2. No additional dependencies needed (uses built-in threading and time modules)

## Exercises

### Test 1: Single Connection, Single Channel
```bash
python single_connection.py
```

### Test 2: Multiple Connections
```bash
python multiple_connections.py
```

### Test 3: Connection Pool with Channels
```bash
python connection_pool.py
```

### Test 4: Performance Comparison
Each script ends with a summary (total time, throughput, connections, channels).
Run the three scripts one after the other and compare the summaries:
```bash
for s in single_connection multiple_connections connection_pool; do
  echo "== $s"; python $s.py | tail -5
done
```
While a script runs, open the **Connections** and **Channels** tabs of the
Management UI to see how many TCP connections and channels each approach uses.

## Expected Results
- **Single Connection:** Simple but limited concurrency
- **Multiple Connections:** Higher resource usage, more TCP overhead
- **Connection Pool:** Best balance of performance and resource usage
- **Channels:** Efficient multiplexing within connections

## Performance Metrics
Monitor these aspects:
- **Connection Time:** Time to establish connections
- **Message Throughput:** Messages per second
- **Resource Usage:** Memory and TCP connections
- **Error Rates:** Connection failures and timeouts

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Connections Tab:**
- Number of active connections
- Connection details (channels per connection)
- Data rates per connection

**Channels Tab:**
- Number of active channels
- Channel distribution across connections
- Channel activity and message rates

## Best Practices Demonstrated
1. **Connection Reuse:** Share connections across operations
2. **Channel Per Thread:** Use separate channels for thread safety
3. **Proper Cleanup:** Close channels and connections properly
4. **Error Handling:** Handle connection failures gracefully
5. **Pool Management:** Implement connection pooling for high-load scenarios

## Real-World Applications
- **Web Applications:** Connection pools for request handling
- **Microservices:** Shared connections across service instances
- **High-Throughput Systems:** Efficient resource utilization
- **Long-Running Processes:** Connection lifecycle management