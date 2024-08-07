import base64
import json
from kafka import KafkaProducer
import os
import sys
import time

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

def send_image_to_kafka(image_data):
    image_bytes = base64.b64decode(image_data)
    log_message = {
        'message': 'image data is sending',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    log_message_bytes = json.dumps(log_message).encode('utf-8')
    producer.send('image-topic', value=image_bytes, headers=[('log', log_message_bytes)])

if __name__ == '__main__':
    data = json.loads(sys.argv[1])
    image_data = data['image'].split(',')[1]
    send_image_to_kafka(image_data)
