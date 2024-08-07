import time
import json
from kafka import KafkaProducer

# Kafka Producer 설정
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# 간단한 로그 메시지 생성기
def generate_log(i):
    log_message = {
        'message': f'This is a log message {i}',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    return log_message

def generate_and_send_log():
    i=0
    while True:
        log_message = generate_log(i)
        producer.send('test-topic', {'message': log_message})
        print(f"Sent log: {log_message}")
        i += 1
        time.sleep(1)  # 1초마다 로그 생성 및 전송

if __name__ == "__main__":
    generate_and_send_log()

