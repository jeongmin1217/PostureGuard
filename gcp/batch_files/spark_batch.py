from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, input_file_name, from_utc_timestamp
import cv2
import numpy as np
from gcp.neck_angle_detection import analyze_posture
from google.cloud import bigquery, storage
import uuid
import time
from google.api_core.exceptions import ServiceUnavailable

# 소요 시간 측정
start_time = time.time()
print(f"start_time : {start_time}")

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("GCS-local-JSON-Batch-Processing") \
    .config("spark.executor.instances", "7") \
    .config("spark.executor.cores", "4") \
    .config("spark.executor.memory", "11g") \
    .config("spark.executor.memoryOverhead", "1536m") \
    .config("spark.driver.memory", "4g") \
    .config("spark.dynamicAllocation.enabled", "false") \
    .config("spark.sql.files.maxPartitionBytes", "1572864") \
    .config("spark.network.timeout", "800s") \
    .config("spark.executor.heartbeatInterval", "60s")  \
    .config("spark.rpc.askTimeout", "600s")  \
    .config("spark.task.maxFailures", "4") \
    .config("spark.rpc.retry.wait", "10s") \
    .config("spark.rpc.retry.maxRetries", "10") \
    .getOrCreate()

# BigQuery 클라이언트 생성
bq_client = bigquery.Client()

# BigQuery 설정
bq_dataset_id = 'dataset_pg'
posture_table_id = 'tb_posture'
image_table_id = 'tb_image'
user_table_id = 'tb_user'
year_table_id = 'tb_year'
month_table_id = 'tb_month'
week_table_id = 'tb_week'
day_table_id = 'tb_day'

# GCS 클라이언트 생성
gcs_client = storage.Client()

# GCS 설정
bucket_name = 'posture-guard'
prefix = 'local-batch-json/20240822/'
bucket = gcs_client.bucket(bucket_name)
blobs = bucket.list_blobs(prefix=prefix)

# JSON 파일 경로 리스트 생성
json_files = []
for blob in blobs:
    if blob.name.endswith('.json'):
        json_files.append('gs://' + bucket_name + '/' + blob.name)
        if len(json_files) >= 10000:
            break

# partiton 설정
num_of_json_files = 10000
total_size_mb = num_of_json_files * 60 / 1024  # 총 데이터 크기를 MB로 계산 (하나당 60KB 가정)
target_partition_size_mb =1.5  # 목표 파티션 크기
num_partitions = max(int(total_size_mb / target_partition_size_mb), 1)  # 파티션 수 계산, 최소 1

# GCS 경로에서 JSON 파일 읽기
# json_gcs_path = 'gs://posture-guard/local-batch-json/20240823/*.json'
df = spark.read.option("multiLine", True).json(json_files) \
    .withColumn("file_name", input_file_name()) \
    .withColumn("timestamp", from_utc_timestamp(to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss.SSSSSS Z"), "Asia/Seoul"))

df = df.repartition(num_partitions)

# df 예시 20개 출력
df.show()

# BigQuery 테이블에 데이터를 삽입하는 함수
def insert_into_bigquery(table_id, rows_to_insert):
    table_ref = bq_client.dataset(bq_dataset_id).table(table_id)
    errors = bq_client.insert_rows_json(table_ref, rows_to_insert)
    if errors:
        print(f"Failed to insert into {table_id}: {errors}")
    else:
        pass

# GCS 파일 삭제 함수
def delete_gcs_files(files_to_delete):
    bucket = gcs_client.bucket(bucket_name)
    for file_path in files_to_delete:
        blob = bucket.blob(file_path)
        blob.delete()
        print(f"Deleted file: {file_path}")

# GCS 파일 업로드를 위한 함수에 재시도 로직 추가
def upload_to_gcs_with_retry(bucket, blob_name, image_bytes, max_retries=5):
    retry_count = 0
    while retry_count < max_retries:
        try:
            blob = bucket.blob(blob_name)
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            print(f"Image uploaded : {blob_name}")
            return
        except ServiceUnavailable as e:
            retry_count += 1
            wait_time = 2 ** retry_count  # Exponential backoff
            print(f"Upload failed (attempt {retry_count}/{max_retries}), retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Upload failed due to an unexpected error: {e}")
            break
    print(f"Failed to upload {blob_name} after {max_retries} attempts.")


# 배치 데이터를 처리하는 함수
def process_batch(batch_df):
    try:
        # image_data가 None이 아닌 행만 필터링
        filtered_df = batch_df.filter(batch_df.image_data.isNotNull())
        files_to_delete = []  # 삭제할 파일 경로를 저장할 리스트

        for row in filtered_df.collect():
            image_data = row['image_data']  # 16진수 인코딩된 이미지 데이터
            timestamp = row['timestamp']  # 타임스탬프 데이터
            file_name = row['file_name']

            # 명시적으로 bytes 형식으로 변환
            # 이미지 데이터를 디코딩
            try:
                image_bytes = bytes.fromhex(image_data)
            except TypeError:
                print(f"Skipping row due to invalid image_data at {file_name}")
                continue
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # 목 각도 및 자세 분석
            cva_left, cva_right, fha_left, fha_right, posture = analyze_posture(img)
            print(f'cva_left : {cva_left}, cva_right : {cva_right}, fha_left : {fha_left}, fha_right : {fha_right}, posture : {posture}')
            
            timestamp_str = timestamp.isoformat()
            day_id = timestamp.day
            week_id = timestamp.isocalendar()[1]  # ISO calendar 기준 주 번호
            month_id = timestamp.month
            year_id = timestamp.year

            # 사용자 정보 (우선 하드코딩)
            user_id = 'jeongmin1217'
            user_name = 'Jeongmin'
            user_age = 25
            user_gender = 'Male'

            # 이미지 파일 크기 계산
            file_size = len(image_bytes)

            month_value = timestamp.strftime('%B')  # ex: 'August'
            day_value = timestamp.date().isoformat()  # ex: '2024-08-14'

            # for i in range(10):

            # 이미지 파일명을 생성
            image_filename = f"image_{uuid.uuid4()}.jpg"

            # GCS에 이미지 업로드 - 재시도 로직 사용
            upload_to_gcs_with_retry(gcs_client.bucket(bucket_name), f"original-data/{image_filename}", image_bytes)

            # GCS에 이미지 업로드
            # bucket = gcs_client.bucket(bucket_name)
            # blob = bucket.blob(f"original-data/{image_filename}")
            # blob.upload_from_string(image_bytes, content_type='image/jpeg')
            #print(f"Image uploaded : original-data/{image_filename}_{i}")

            # BigQuery에 posture_analysis 데이터 저장            
            posture_id = str(uuid.uuid4())

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

            # BigQuery에 tb_user 데이터 저장
            user_rows_to_insert = [{
                "user_id": user_id,
                "user_name": user_name,
                "user_age": user_age,
                "user_gender": user_gender
            }]
            insert_into_bigquery(user_table_id, user_rows_to_insert)

            img_id = str(uuid.uuid4())

            # BigQuery에 tb_image 데이터 저장
            image_rows_to_insert = [{
                "img_id": img_id,
                "img_filename": image_filename,
                "capture_time": timestamp_str,
                "file_size": file_size
            }]
            insert_into_bigquery(image_table_id, image_rows_to_insert)

            
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

            # 처리된 JSON 파일을 삭제 목록에 추가
            files_to_delete.append(file_name.replace("gs://posture-guard/", ""))
        
        # GCS에서 처리된 파일 삭제
        delete_gcs_files(files_to_delete)

    except Exception as e:
        print(f'Error in processing batch: {e}')

# 배치 데이터를 바로 처리
process_batch(df)

# Spark 세션 종료
spark.stop()

# End the timer
end_time = time.time()
print(f"end time : {end_time}")
# Calculate total time taken
total_time = end_time - start_time
print(f"Total time taken: {total_time} seconds")
