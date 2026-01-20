# ===== src/stream_bus.py =====
import json
try:
    from kafka import KafkaProducer, KafkaConsumer
    HAS_KAFKA = True
except (ImportError, Exception):
    HAS_KAFKA = False

KAFKA_SERVER = "localhost:9092"
TOPIC = "radar-stream"

def get_producer():
    if not HAS_KAFKA:
        return None
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=1000,
            max_block_ms=1000
        )
    except Exception:
        return None

def get_consumer():
    if not HAS_KAFKA:
        return None
    try:
        return KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_SERVER,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest"
        )
    except Exception:
        return None
