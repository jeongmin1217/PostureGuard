from pyspark.sql import SparkSession
from pyspark.sql.functions import col
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
import pytz

# 한국 시간대 설정
kst = pytz.timezone('Asia/Seoul')

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

# Kafka에서 데이터를 읽어오는 DataFrame 생성
# 210.123.95.211 : 집 IP의 외부 주소
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "210.123.95.211:9093") \
    .option("subscribe", "image-topic") \
    .option("startingOffsets", "earliest") \
    .option("kafka.group.id", "image-consumer-group") \
    .load()

# Kafka 메시지의 key와 value를 바이너리로 변환
df = df.select(col("value").alias("image_bytes"))

# BigQuery 테이블에 데이터를 삽입하는 함수
def insert_into_bigquery(table_id, rows_to_insert):
    table_ref = bq_client.dataset(bq_dataset_id).table(table_id)
    errors = bq_client.insert_rows_json(table_ref, rows_to_insert)
    if errors:
        print(f"Failed to insert into {table_id}: {errors}")
    else:
        print(f"Inserted data into {table_id}")

# 메시지 수신 및 분석 처리 함수
def process_batch(batch_df, batch_id):
    try:
        for row in batch_df.collect():
            image_bytes = row['image_bytes']  # 바이너리 데이터 가져오기

            # 명시적으로 bytes 형식으로 변환
            image_bytes = bytes(image_bytes)

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
            response = requests.post('http://210.123.95.211:8000/logs/analyze-result/', json=result)
            
            
            # 이미지 파일명을 생성
            image_filename = f"image_{uuid.uuid4()}.jpg"

            # GCS에 이미지 업로드
            bucket = gcs_client.bucket(bucket_name)
            blob = bucket.blob(image_filename)
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            print(f"Image uploaded to GCS: {image_filename}")

            # BigQuery에 posture_analysis 데이터 저장            
            posture_id = str(uuid.uuid4())
            current_time = datetime.now(kst)
            current_time_str = current_time.isoformat()
            
            day_id = current_time.day
            week_id = current_time.isocalendar()[1]  # ISO calendar 기준 주 번호
            month_id = current_time.month
            year_id = current_time.year

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
                "timestamp": current_time_str
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
                "capture_time": current_time_str,
                "file_size": file_size
            }]
            insert_into_bigquery(image_table_id, image_rows_to_insert)

            month_value = current_time.strftime('%B')  # ex: 'August'
            day_value = current_time.date().isoformat()  # ex: '2024-08-14'
            
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
    .start()

print(query.status)
query.awaitTermination()