'''
 외부에서 로컬 카프카로 수집해놓은 이미지 & 시간 데이터를
 매일 밤 Spark를 통해 분석하고 GCS와 BigQuery에 저장하는 코드
'''

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType
import cv2
import numpy as np
import os
import json
import time
from neck_angle_detection import analyze_posture
import requests
from google.cloud import bigquery, storage
import uuid
from datetime import datetime
import asyncio
import aiohttp

# BigQuery 클라이언트 생성
bq_client = bigquery.Client()
# GCS 클라이언트 생성
gcs_client = storage.Client()

# BigQuery와 GCS 설정
bq_dataset_id = 'dataset_pg'
bucket_name = 'posture-guard'
posture_table_id = 'tb_posture'
image_table_id = 'tb_image'
user_table_id = 'tb_user'
year_table_id = 'tb_year'
month_table_id = 'tb_month'
week_table_id = 'tb_week'
day_table_id = 'tb_day'

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("Kafka-Batch-Processing") \
    .getOrCreate()

# JSON 스키마 정의
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
       .withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss.SSSSSS Z"))

# 실시간 데이터 처리 성능 향상을 위한 비동기 함수 정의
async def send_analyze_result(result):
    async with aiohttp.ClientSession() as session:
        async with session.post('http://210.123.95.211:8000/logs/analyze-result/', json=result) as response:
            return await response.json()

# BigQuery 테이블에 데이터를 삽입하는 함수
def insert_into_bigquery(table_id, rows_to_insert):
    table_ref = bq_client.dataset(bq_dataset_id).table(table_id)
    errors = bq_client.insert_rows_json(table_ref, rows_to_insert)
    if errors:
        print(f"Failed to insert into {table_id}: {errors}")
    else:
        pass

# 메시지 수신 및 분석 처리 함수
def process_batch(batch_df, batch_id):
    try:
        for row in batch_df.collect():
            image_data = row['image_data']  # 16진수 인코딩된 이미지 데이터
            timestamp = row['timestamp']  # 타임스탬프 데이터

            # 문자열을 datetime 객체로 변환
            # timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f %z')            
            # test
            # print(timestamp, f": datatype {type(timestamp)}")

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
            
            # 이미지 파일명을 생성
            image_filename = f"image_{uuid.uuid4()}.jpg"

            # GCS에 이미지 업로드
            bucket = gcs_client.bucket(bucket_name)
            blob = bucket.blob(f"original-data/{image_filename}")
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            print(f"Image uploaded : {image_filename}")

            # BigQuery에 posture_analysis 데이터 저장            
            posture_id = str(uuid.uuid4())
            timestamp_str = timestamp.isoformat()
            
            day_id = timestamp.day
            week_id = timestamp.isocalendar()[1]  # ISO calendar 기준 주 번호
            month_id = timestamp.month
            year_id = timestamp.year

            posture_rows_to_insert = [{
                "posture_id": posture_id,
                "img_filename": image_filename,
                "cva_left_value": cva_left,
                "cva_right_value": cva_right,
                "fha_left_value": fha_left,
                "fha_right_value": fha_right,
                "posture_status": posture,
                "user_id": 'jeongmin1217',
                "day_id": day_id,
                "week_id": week_id,
                "month_id": month_id,
                "year_id": year_id,
                "timestamp": timestamp_str
            }]

            insert_into_bigquery(posture_table_id, posture_rows_to_insert)

            # 사용자 정보 (우선 하드코딩)
            user_id = 'jeongmin1217'
            user_name = 'Jeongmin'
            user_age = 25
            user_gender = 'Male'

            # BigQuery에 tb_user 데이터 저장
            user_rows_to_insert = [{
                "user_id": user_id,
                "user_name": user_name,
                "user_age": user_age,
                "user_gender": user_gender
            }]
            insert_into_bigquery(user_table_id, user_rows_to_insert)

            # 이미지 파일 크기 계산
            file_size = len(image_bytes)
            img_id = str(uuid.uuid4())

            # BigQuery에 tb_image 데이터 저장
            image_rows_to_insert = [{
                "img_id": img_id,
                "img_filename": image_filename,
                "capture_time": timestamp_str,
                "file_size": file_size
            }]
            insert_into_bigquery(image_table_id, image_rows_to_insert)

            month_value = timestamp.strftime('%B')  # ex: 'August'
            day_value = timestamp.date().isoformat()  # ex: '2024-08-14'
            
            # tb_year에 데이터 삽입
            year_rows_to_insert = [{
                "year_id": year_id,
                "year_value": year_id
            }]
            insert_into_bigquery(year_table_id, year_rows_to_insert)
            # tb_week에 데이터 삽입
            week_rows_to_insert = [{
                "week_id": week_id,
                "week_value": week_id,
                "year_id": year_id
            }]
            insert_into_bigquery(week_table_id, week_rows_to_insert)
            # tb_month에 데이터 삽입
            month_rows_to_insert = [{
                "month_id": month_id,
                "month_value": month_value,
                "year_id": year_id
            }]
            insert_into_bigquery(month_table_id, month_rows_to_insert)
            # tb_day에 데이터 삽입
            day_rows_to_insert = [{
                "day_id": day_id,
                "day_value": day_value,
                "month_id": month_id,
                "week_id": week_id
            }]
            insert_into_bigquery(day_table_id, day_rows_to_insert)
    
    except Exception as e:
        print(f'Error in processing batch: {e}')


# 스트리밍 데이터를 배치별로 처리
query = df.writeStream \
    .foreachBatch(process_batch) \
    .trigger(processingTime='1 second') \
    .start()

print(query.status)
query.awaitTermination()