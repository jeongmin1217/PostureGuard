from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import cv2
import numpy as np
import os
import json
import time
from neck_angle_detection import analyze_posture
import requests

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("Kafka-Batch-Processing") \
    .getOrCreate()

# Kafka에서 데이터를 읽어오는 DataFrame 생성
# 210.123.95.211 : 집 IP의 외부 주소
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "210.123.95.211:9093") \
    .option("subscribe", "image-topic") \
    .option("startingOffsets", "earliest") \
    .option("kafka.group.id", "image-consumer-group1") \
    .load()

# Kafka 메시지의 key와 value를 바이너리로 변환
df = df.select(col("value").alias("image_bytes"))

# 메시지 수신 및 분석 처리 함수
def process_batch(batch_df, batch_id):
    try:
        for row in batch_df.collect():
            image_bytes = row['image_bytes']  # 바이너리 데이터 가져오기
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # 목 각도 및 자세 분석
            cva_left, cva_right, fha_left, fha_right, posture = analyze_posture(img)
            print(f'cva_left : {cva_left}, cva_right : {cva_right}, fha_left : {fha_left}, fha_right : {fha_right}, posture : {posture}')

            # 결과를 저장하거나 추가적인 작업 수행 가능
            result = {
                "cva_left": cva_left,
                "cva_right": cva_right,
                "fha_left": fha_left,
                "fha_right": fha_right,
                "posture_correct": posture
            }

            # # JSON 파일로 저장
            # output_folder = 'analyzed_results'
            # if not os.path.exists(output_folder):
            #     os.makedirs(output_folder)
            # with open(os.path.join(output_folder, f'result_{int(time.time())}.json'), 'w') as f:
            #     json.dump(result, f)


            # Django 백엔드로 결과 전송
            response = requests.post('http://210.123.95.211:8000/logs/analyze-result/', json=result)
    
    except Exception as e:
        print(f'Error in processing batch: {e}')


# 스트리밍 데이터를 배치별로 처리
query = df.writeStream \
    .foreachBatch(process_batch) \
    .start()

print(query.status)
query.awaitTermination()