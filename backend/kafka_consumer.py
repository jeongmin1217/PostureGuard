from kafka import KafkaConsumer
import cv2
import numpy as np
import json
import os
import time

# Kafka 컨슈머 설정
consumer = KafkaConsumer(
    'image-topic',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',  # 처음부터 읽기
    enable_auto_commit=True,
    group_id='image-consumer-group'
)

# 저장할 폴더 설정
output_folder = 'received_images'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 메시지 수신 및 이미지 저장
image_counter = 0
for message in consumer:
    image_bytes = message.value
    headers = {k: v.decode('utf-8') for k, v in message.headers}
    log_message = json.loads(headers.get('log', '{}'))
    print(f"Log Message: {log_message}")

    # 이미지 디코딩
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 이미지 파일로 저장
    image_filename = os.path.join(output_folder, f'image_{image_counter}.jpg')
    cv2.imwrite(image_filename, img)
    print(f"Saved {image_filename}")

    image_counter += 1

    # # 테스트를 위해 6개만 저장하고 종료
    # if image_counter >= 6:
    #     break

print("Finished saving images.")
