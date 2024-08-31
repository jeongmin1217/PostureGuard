from kafka import KafkaConsumer
import json
import os
from datetime import datetime
import pytz

# 한국 시간대 설정
kst = pytz.timezone('Asia/Seoul')

# Kafka 컨슈머 설정
consumer = KafkaConsumer(
    'image-topic',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',  # 처음부터 읽기
    enable_auto_commit=True,  # 오프셋 자동 커밋 활성화
    group_id='image-consumer-group-new'
    # Kafka의 오프셋이 각 컨슈머 그룹이 어디까지 메세지를 읽었는지 기억하기 때문에..! 한 번 읽었으면 그것은 다시 읽지 않음
    # 이전 것까지 모두 가져오기 위해서는 새로운 consumer group 이름, 위와 같은 세팅으로 코드 돌리면 수집 가능함.
)

# 저장할 폴더 설정
today_date = datetime.now(kst).strftime('%Y%m%d')
output_folder = f'kafka-data/{today_date}'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 메시지 수신 및 JSON 파일로 저장
json_counter = 0
for message in consumer:
    try:
        # 메시지의 값은 JSON 형식의 문자열
        message_value = message.value.decode('utf-8')
        
        # 파티션 정보 출력
        partition = message.partition
        print(f"Received message from partition: {partition}")

        # JSON 데이터 파싱
        json_data = json.loads(message_value)

        # 파일명 생성 (timestamp를 기반으로 고유한 파일명 생성)
        timestamp = json_data['timestamp'].replace(":", "-").replace(" ", "_")
        file_name = f"kafka_{timestamp}.json"

        # JSON 데이터를 파일로 저장
        with open(os.path.join(output_folder, file_name), 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
        
        print(f"Saved {file_name} in {output_folder}")

        json_counter += 1

        # 메시지 처리 후 오프셋 커밋
        consumer.commit()

    except Exception as e:
        print(f"Error processing message: {e}")
        continue

print(f"Finished saving {json_counter} json files.")
