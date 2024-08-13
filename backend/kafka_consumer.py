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
    enable_auto_commit=True,  # 오프셋 자동 커밋 활성화
    group_id='image-consumer-group'
    # Kafka의 오프셋이 각 컨슈머 그룹이 어디까지 메세지를 읽었는지 기억하기 때문에..! 한 번 읽었으면 그것은 다시 읽지 않음
    # 이전 것까지 모두 가져오기 위해서는 새로운 consumer group 이름, 위와 같은 세팅으로 코드 돌리면 수집 가능함.
)

# 저장할 폴더 설정
output_folder = 'received_images'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 메시지 수신 및 이미지 저장
image_counter = 0
for message in consumer:
    try:
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

        # 메시지 처리 후 오프셋 커밋
        consumer.commit()

        # # 테스트를 위해 6개만 저장하고 종료
        # if image_counter >= 6:
        #     break
    except Exception as e:
        print(f"Error processing message: {e}")
        continue

print("Finished saving images.")
