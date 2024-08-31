import base64
import json
from kafka import KafkaProducer
import os
import sys
import time
import pytz
from datetime import datetime

# 한국 시간대 설정
kst = pytz.timezone('Asia/Seoul')

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

def send_image_to_kafka(image_data):
    # 이미지 데이터를 바이너리로 디코딩
    image_bytes = base64.b64decode(image_data)
    current_time = datetime.now(kst)

    # JSON 형식의 메시지 생성
    message = {
        'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
        'image_data': image_bytes.hex()  # 이미지 데이터를 16진수로 변환하여 JSON에 포함
    }

    # 메시지를 JSON 문자열로 인코딩
    message_bytes = json.dumps(message).encode('utf-8')

    producer.send('image-topic', value=message_bytes)
    producer.flush()

if __name__ == '__main__':
    data = json.loads(sys.argv[1])
    image_data = data['image'].split(',')[1]
    send_image_to_kafka(image_data)
