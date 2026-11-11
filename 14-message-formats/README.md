# Exercise 12: Message Formats and Serialization

## Concept
Demonstrates different message serialization formats in RabbitMQ:
- **JSON:** Human-readable, widely supported
- **MessagePack:** Binary, compact, fast
- **Pickle:** Python-specific, supports complex objects
- **Performance:** Compare serialization speed and message size

## Learning Objectives
- Understand message serialization options
- Learn MessagePack benefits and usage
- Practice different data formats
- Measure performance differences

## Serialization Comparison
| Format | Size | Speed | Human Readable | Cross-Language |
|--------|------|-------|----------------|----------------|
| **JSON** | Large | Medium | Yes | Yes |
| **MessagePack** | Small | Fast | No | Yes |
| **Pickle** | Medium | Fast | No | Python only |
| **Plain Text** | Large | Fastest | Yes | Yes |

## Setup
1. Start RabbitMQ container (see main README)
2. MessagePack is installed by the repository `requirements.txt`:
   ```bash
   pip install -r ../requirements.txt
   ```

## Exercises

### Test 1: JSON Serialization
```bash
python json_messages.py            # producer
python json_messages.py consumer   # consumer (Ctrl+C to stop)
```

### Test 2: MessagePack Serialization
```bash
python msgpack_messages.py            # producer
python msgpack_messages.py consumer   # consumer (Ctrl+C to stop)
```

### Test 3: Performance Comparison
```bash
python format_comparison.py
```

### Test 4: Inspect the Payloads in the Management UI
1. Run the producers only (default mode): `python json_messages.py` and `python msgpack_messages.py`
2. In the Management UI open **Queues and Streams** → `json_messages` / `msgpack_messages` → **Get messages**
3. Compare the payloads: JSON is human readable, MessagePack is shown base64-encoded
   (binary); the `content_type` property tells consumers how to decode it
4. Consume them: `python json_messages.py consumer` and `python msgpack_messages.py consumer`

## Expected Results
- **JSON:** Readable but larger messages
- **MessagePack:** Smaller, faster, binary format
- **Performance:** MessagePack typically 2-3x faster and smaller
- **Compatibility:** JSON works everywhere, MessagePack needs library support

## Message Size Comparison
For typical data structures:
- **JSON:** ~100% baseline size
- **MessagePack:** ~60-80% of JSON size
- **Compression:** MessagePack often eliminates need for additional compression

## Performance Metrics
Monitor these aspects:
- **Serialization Time:** Time to encode data
- **Deserialization Time:** Time to decode data
- **Message Size:** Bytes over the wire
- **Throughput:** Messages per second

## Web UI Monitoring
Open http://localhost:15672 (guest/guest) and observe:

**Queues Tab:**
- Message sizes for different formats
- Message rates and throughput
- Queue memory usage

**Exchanges Tab:**
- Message flow rates
- Data transfer rates

## Use Cases by Format

### JSON
- **Web APIs:** REST endpoints, webhooks
- **Configuration:** Settings, metadata
- **Debugging:** Human-readable logs
- **Cross-platform:** Mixed technology stacks

### MessagePack
- **High Performance:** Real-time systems, gaming
- **IoT:** Bandwidth-constrained devices
- **Microservices:** Internal service communication
- **Analytics:** Large data volumes

### Pickle (Python)
- **Python-only:** Internal Python services
- **Complex Objects:** Custom classes, functions
- **Rapid Prototyping:** Quick development
- **Scientific Computing:** NumPy arrays, pandas DataFrames

## Best Practices Demonstrated
1. **Format Selection:** Choose based on requirements
2. **Schema Evolution:** Handle format changes gracefully
3. **Error Handling:** Robust serialization/deserialization
4. **Performance Testing:** Measure actual impact
5. **Compatibility:** Consider consumer requirements