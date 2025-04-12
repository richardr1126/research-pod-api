import logging
import time
import json
import os
from kafka import KafkaConsumer, KafkaProducer, TopicPartition, KafkaAdminClient
from kafka.errors import UnknownTopicOrPartitionError
import redis

logger = logging.getLogger(__name__)

def cleanup_pod_topic(admin_client: KafkaAdminClient, pod_id: str):
    """Delete the Kafka topic for a pod's updates after it's no longer needed."""
    topic = f'pod-updates-{pod_id}'
    try:
        admin_client.delete_topics([topic])
        logger.info(f"Deleted Kafka topic: {topic}")
    except UnknownTopicOrPartitionError:
        logger.debug(f"Topic {topic} doesn't exist or was already deleted")
    except Exception as e:
        logger.error(f"Error deleting Kafka topic {topic}: {str(e)}")

def create_sse_consumer(pod_id: str) -> KafkaConsumer:
    """Create a new Kafka consumer for SSE updates for a specific pod."""
    topic = f'pod-updates-{pod_id}'
    consumer = KafkaConsumer(
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        group_id=f'sse-{pod_id}-{int(time.time())}',  # Unique group ID per connection
        security_protocol='SSL',
        ssl_check_hostname=True,
        ssl_cafile='/etc/kafka/certs/kafka-ca.crt',
    )
    consumer.assign([TopicPartition(topic, 0)])  # Assign to partition 0 of the topic
    return consumer

def send_progress_update(
    redis_client: redis.Redis,
    producer: KafkaProducer,
    consumer_id: str,
    pod_id: str,
    status: str,
    progress: int,
    message: str = None
):
    """Send a progress update to both Redis and Kafka stream."""
    # Update Redis
    update_data = {
        "status": status,
        "progress": progress,
        "consumer": consumer_id,
        "message": message or f"Processing {status.lower()} at {progress}%"
    }

    redis_client.hset(f"pod:{pod_id}", mapping=update_data)

    # Send to Kafka SSE topic
    update = {
        "pod_id": pod_id,
        "status": status,
        "progress": progress,
        "message": update_data["message"]
    }
    producer.send(f'pod-updates-{pod_id}', value=update)
    producer.flush()

