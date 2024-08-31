'''
실시간 스트리밍 데이터를 json 형태로 GCS로 보내놓았던 것을 불러와서,
GCS와 BigQuery에 형태에 맞게 저장하는 코드
'''
from google.cloud import bigquery, storage
import json
import uuid
from datetime import datetime
import time

# BigQuery 클라이언트 생성
bq_client = bigquery.Client()
# GCS 클라이언트 생성
gcs_client = storage.Client()

# BigQuery와 GCS 설정
bucket_name = 'posture-guard'
bq_dataset_id = 'dataset_pg'
posture_table_id = 'tb_posture'
image_table_id = 'tb_image'
user_table_id = 'tb_user'
year_table_id = 'tb_year'
month_table_id = 'tb_month'
week_table_id = 'tb_week'
day_table_id = 'tb_day'

# BigQuery 테이블에 데이터를 삽입하는 함수
def insert_into_bigquery(table_id, rows_to_insert):
    table_ref = bq_client.dataset(bq_dataset_id).table(table_id)
    errors = bq_client.insert_rows_json(table_ref, rows_to_insert)
    if errors:
        print(f"Failed to insert into {table_id}: {errors}")
    else:
        pass

# GCS에서 JSON 파일 읽기
def process_gcs_json_files():
    try:
        bucket = gcs_client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix="unprocessed-json/"))

        # 폴더에 파일이 있는지 확인
        file_count = len([blob for blob in blobs if not blob.name.endswith('/')])
        
        if file_count == 0:  # 실제로 파일이 없을 경우
            print("no files in folder")
            return

        for blob in blobs:
            # 폴더 자체를 건너뛰기 위해 추가된 조건문
            if blob.name == "unprocessed-json/":
                continue

            json_data = json.loads(blob.download_as_string())

            image_data = json_data['image_data']
            timestamp_str = json_data['timestamp']
            analysis_result = json_data['analysis_result']

            # 문자열을 datetime 객체로 변환
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f %z')
            
            # 이미지 파일명을 생성 및 GCS에 저장
            image_bytes = bytes.fromhex(image_data)
            image_filename = f"image_{uuid.uuid4()}.jpg"
            image_blob = bucket.blob(f"original-data/{image_filename}")
            image_blob.upload_from_string(image_bytes, content_type='image/jpeg')
            print(f"Image uploaded : {image_filename}")

            # BigQuery에 posture_analysis 데이터 저장            
            posture_id = str(uuid.uuid4())            
            day_id = timestamp.day
            week_id = timestamp.isocalendar()[1]  # ISO calendar 기준 주 번호
            month_id = timestamp.month
            year_id = timestamp.year

            posture_rows_to_insert = [{
                "posture_id": posture_id,
                "img_filename": image_filename,
                "cva_left_value": analysis_result["cva_left"],
                "cva_right_value": analysis_result["cva_right"],
                "fha_left_value": analysis_result["fha_left"],
                "fha_right_value": analysis_result["fha_right"],
                "posture_status": analysis_result["posture_correct"],
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

            # JSON 파일 처리 후 삭제
            blob.delete()

    except Exception as e:
        print(f'Error in processing batch: {e}')

# 3초마다 실행
while True:
    process_gcs_json_files()
    time.sleep(3)
