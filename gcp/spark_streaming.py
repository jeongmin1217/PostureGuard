from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType
import cv2
import numpy as np
import json
from neck_angle_detection import analyze_posture
# import requests
from google.cloud import storage
import uuid
import asyncio
import aiohttp

# GCS 클라이언트 생성
gcs_client = storage.Client()
# GCS 설정
bucket_name = 'posture-guard'

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("Kafka-Spark-Streaming-Processing") \
    .getOrCreate()

# Kafka message JSON 스키마 정의
schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("image_data", StringType(), True)
])

# Kafka에서 데이터를 읽어오는 DataFrame 생성
# 210.123.95.211 : 집 IP의 외부 주소
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "210.123.95.211:9093") \
    .option("subscribe", "image-topic") \
    .option("startingOffsets", "earliest") \
    .option("kafka.group.id", "image-consumer-group") \
    .load()

# Kafka 메시지의 key와 value를 JSON으로 변환 및 파싱
df = df.selectExpr("CAST(value AS STRING)") \
       .select(from_json(col("value"), schema).alias("json_data")) \
       .select("json_data.*") \

# 실시간 데이터 처리 성능 향상을 위한 비동기 함수 정의
async def send_analyze_result(result):
    async with aiohttp.ClientSession() as session:
        async with session.post('http://210.123.95.211:8000/logs/analyze-result/', json=result) as response:
            return await response.json()

# 메시지 수신 및 분석 처리 함수
def process_batch(batch_df, batch_id):
    try:
        for row in batch_df.collect():
            image_data = row['image_data']  # 16진수 인코딩된 이미지 데이터
            timestamp = row['timestamp']  # 타임스탬프 데이터 (문자열)

            # 명시적으로 bytes 형식으로 변환
            image_bytes = bytes.fromhex(image_data)

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # 목 각도 및 자세 분석
            cva_left, cva_right, fha_left, fha_right, posture = analyze_posture(img)
            print(f'cva_left : {cva_left}, cva_right : {cva_right}, fha_left : {fha_left}, fha_right : {fha_right}, posture : {posture}')
            
            # 실시간 데이터 전송을 가장 먼저 진행
            result = {
                "cva_left": cva_left,
                "cva_right": cva_right,
                "fha_left": fha_left,
                "fha_right": fha_right,
                "posture_correct": posture
            }

            # Django 백엔드로 결과 전송
            # response = requests.post('http://210.123.95.211:8000/logs/analyze-result/', json=result)
            asyncio.run(send_analyze_result(result))

            # GCS에 JSON 파일 형태로 저장
            bucket = gcs_client.bucket(bucket_name)
            json_data = {
                "image_data": image_data,
                "timestamp": timestamp,
                "analysis_result": result
            }
            blob = bucket.blob(f"unprocessed-json/{uuid.uuid4()}.json")
            blob.upload_from_string(json.dumps(json_data), content_type='application/json')
            print(f"JSON data uploaded to GCS")
    
    except Exception as e:
        print(f'Error in processing batch: {e}')

# 스트리밍 데이터를 가능한 한 빠르게 처리
query = df.writeStream \
    .foreachBatch(process_batch) \
    .start()

print(query.status)
query.awaitTermination()