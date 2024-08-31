from google.cloud import storage, bigquery
from pyspark.sql import SparkSession
import io
import cv2
import mediapipe as mp
import os
import matplotlib.pyplot as plt
import numpy as np
import time
import uuid
# from datetime import datetime
# import pytz

# 한국 시간대 설정
# kst = pytz.timezone('Asia/Seoul')

# 시간 측정 시작
start_time = time.time()

# Spark 세션 생성 및 BigQuery 데이터 로드
spark = SparkSession.builder \
    .appName("Posture Analysis") \
    .config("spark.jars", "path_to_bigquery_connector_jar") \
    .config("spark.executor.instances", "7") \
    .config("spark.executor.cores", "4") \
    .config("spark.executor.memory", "11g") \
    .config("spark.executor.memoryOverhead", "1536m") \
    .config("spark.driver.memory", "5g") \
    .config("spark.dynamicAllocation.enabled", "false") \
    .config("spark.sql.files.maxPartitionBytes", "1572864") \
    .config("spark.network.timeout", "800s") \
    .config("spark.executor.heartbeatInterval", "60s") \
    .config("spark.rpc.askTimeout", "600s") \
    .config("spark.task.maxFailures", "4") \
    .config("spark.rpc.retry.wait", "10s") \
    .config("spark.rpc.retry.maxRetries", "10") \
    .getOrCreate()

table = "postureguard-432006.dataset_pg.tb_posture"

# year, month, day 설정
# time_kst = datetime.now(kst)
# year_id = time_kst.year
# month_id = time_kst.month
# day_id = time_kst.day

year_id = 2024
month_id = 8
day_id = 15

# year_id=2024, month_id=8, day_id=16, posture_status=True/False 조건으로 각각 필터링
df_correct = spark.read \
    .format("bigquery") \
    .option("table", table) \
    .load() \
    .filter(f"year_id = {year_id} AND month_id = {month_id} AND day_id = {day_id} AND posture_status = TRUE")

df_incorrect = spark.read \
    .format("bigquery") \
    .option("table", table) \
    .load() \
    .filter(f"year_id = {year_id} AND month_id = {month_id} AND day_id = {day_id} AND posture_status = FALSE")

# 필터링된 파일명 리스트 가져오기
img_filenames_correct = df_correct.select("img_filename").rdd.flatMap(lambda x: x).collect()
img_filenames_incorrect = df_incorrect.select("img_filename").rdd.flatMap(lambda x: x).collect()

# GCS 클라이언트 초기화 및 Mediapipe 초기화
client = storage.Client()
bucket_name = "posture-guard"
bucket = client.bucket(bucket_name)

# Mediapipe 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Mediapipe의 PoseLandmark Enum 가져오기
landmark_indices = [
    mp_pose.PoseLandmark.LEFT_SHOULDER.value,
    mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
    mp_pose.PoseLandmark.LEFT_EAR.value,
    mp_pose.PoseLandmark.RIGHT_EAR.value
]

# 분석 결과 저장용 리스트 초기화
landmark_data_correct = []
landmark_data_incorrect = []

# 이미지 좌표 분석
def process_images(img_filenames, landmark_data):
    for filename in img_filenames:
        blob = bucket.blob(f"original-data/{filename}")
        image_data = np.asarray(bytearray(blob.download_as_bytes()), dtype="uint8")
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        
        # 이미지를 RGB로 변환하여 Mediapipe에 전달
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        if results.pose_landmarks:
            # 선택한 랜드마크 좌표만 리스트로 저장
            landmarks = [(results.pose_landmarks.landmark[idx].x, 
                          results.pose_landmarks.landmark[idx].y, 
                          results.pose_landmarks.landmark[idx].z) 
                         for idx in landmark_indices]
            # 왼쪽 어깨와 오른쪽 어깨의 중간 지점을 C7으로 추정하여 추가
            left_shoulder = landmarks[0]
            right_shoulder = landmarks[1]
            c7 = [(left_shoulder[0] + right_shoulder[0]) / 2,
                (left_shoulder[1] + right_shoulder[1]) / 2,
                (left_shoulder[2] + right_shoulder[2]) / 2]
            
            # C7을 포함하여 데이터 저장
            landmarks.append(c7)
            landmark_data.append(landmarks)

# 이미지 처리
process_images(img_filenames_correct, landmark_data_correct)
process_images(img_filenames_incorrect, landmark_data_incorrect)

# mean_landmarks, x_coords, y_coords를 계산하고 저장하는 함수
def compute_and_store_mean_landmarks(landmark_data):
    mean_landmarks = np.mean(landmark_data, axis=0)
    # X, Y 좌표를 분리
    x_coords = [point[0] for point in mean_landmarks]
    y_coords = [point[1] for point in mean_landmarks]
    z_coords = [point[2] for point in mean_landmarks]
    return x_coords, y_coords, z_coords

# 평균 좌표를 저장할 딕셔너리
mean_landmark_results = {}
mean_landmark_results['correct'] = compute_and_store_mean_landmarks(landmark_data_correct)
mean_landmark_results['incorrect'] = compute_and_store_mean_landmarks(landmark_data_incorrect)

# correct/incorrect 별 데이터 수
len_data_correct = len(landmark_data_correct)
len_data_incorrect = len(landmark_data_incorrect)

# 분석된 이미지 gcs에 저장
def save_image_to_gcs(image_data, filename):
    blob = bucket.blob(f"daily-average-image/{filename}")
    blob.upload_from_string(image_data.getvalue(), content_type="image/png")
    print(f"Image {filename} uploaded to posture-guard/daily-average-image/")

# 평균 이미지 생성 및 저장 함수
def generate_and_save_average_image(filename, correct_or_incorrect):

    x_coords, y_coords, z_coords = mean_landmark_results[correct_or_incorrect]

    # 랜드마크 이름
    landmark_names = ['Left Shoulder', 'Right Shoulder', 'Left Ear', 'Right Ear', 'C7']

    # C7의 좌표 (리스트의 마지막 요소)
    c7_x, c7_y, c7_z = x_coords[-1], y_coords[-1], z_coords[-1]

    # X축의 범위를 좁히기 위해 현재 X 좌표들의 범위를 확인
    y_min, y_max = min(y_coords), max(y_coords)
    y_range = y_max - y_min

    # 시각화 설정
    fig = plt.figure(figsize=(6, 7))
    ax = fig.add_subplot(111, projection='3d')  # 3D 축 추가
    ax.set_facecolor('#8871e6')  # 배경색 설정

    # C7을 기준으로 모든 포인트 연결
    for i in range(len(x_coords) - 1):  # C7은 마지막 요소이므로 제외
        ax.plot([c7_x, x_coords[i]], [c7_y, y_coords[i]], [c7_z, z_coords[i]], color='#ddddf5', linewidth=2)

    # 각 랜드마크를 점으로 표시
    plt.scatter(x_coords, y_coords, z_coords, color='yellow')

    # 각 랜드마크의 이름을 그래프에 표시
    for i, name in enumerate(landmark_names):
        ax.text(x_coords[i], y_coords[i], z_coords[i], name, fontsize=10, color='white', ha='center', va='bottom',
            bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', pad=1.5)
        )

    # Y축의 범위를 조정 (예: 범위를 60% 정도로 확대/축소)
    adjust_factor = 0.6  # 이 값을 조절해서 범위를 더 좁히거나 넓힐 수 있음
    ax.set_ylim([y_min - y_range * adjust_factor, y_max + y_range * adjust_factor])

    # y축 반전 및 눈금 제거
    ax.invert_zaxis()  # Z축을 반전하여 사람이 서있는 것처럼 보이게 함
    ax.invert_yaxis()  # Y축 반전

    # 시점 설정 (필요에 따라 조정)
    ax.view_init(elev=30, azim=-34)  # 시점 조정 (elev: 높이, azim: 좌우 회전)

    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False) #눈금 없애기

    # 바깥 border 선 없애기
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    image_buffer = io.BytesIO()
    plt.savefig(image_buffer, format='png', bbox_inches='tight', pad_inches=0.1)
    image_buffer.seek(0)
    
    save_image_to_gcs(image_buffer, filename)
    
    plt.close()

# 평균 이미지 생성 및 저장
generate_and_save_average_image(f"average_correct_{year_id}-{month_id}-{day_id}.png", 'correct')
generate_and_save_average_image(f"average_incorrect_{year_id}-{month_id}-{day_id}.png", 'incorrect')

# BigQuery에 결과 저장
def save_results_to_bigquery(year_id, month_id, day_id, x_coords, y_coords, z_coords, posture_correct, img_filename, cnt, table_id = 'postureguard-432006.dataset_pg.tb_daily_stat'):
    client = bigquery.Client()
    
    # 소수점 3째 자리까지만 반올림
    x_coords = [round(coord, 3) for coord in x_coords]
    y_coords = [round(coord, 3) for coord in y_coords]
    z_coords = [round(coord, 3) for coord in z_coords]

    primary_key = str(uuid.uuid4())

    rows_to_insert = [
        {
            "daily_stat_id": primary_key,
            "year_id": year_id,
            "month_id": month_id,
            "day_id": day_id,
            "avg_left_shoulder_x": x_coords[0],
            "avg_left_shoulder_y": y_coords[0],
            "avg_left_shoulder_z": z_coords[0],
            "avg_right_shoulder_x": x_coords[1],
            "avg_right_shoulder_y": y_coords[1],
            "avg_right_shoulder_z": z_coords[1],
            "avg_left_ear_x": x_coords[2],
            "avg_left_ear_y": y_coords[2],
            "avg_left_ear_z": z_coords[2],
            "avg_right_ear_x": x_coords[3],
            "avg_right_ear_y": y_coords[3],
            "avg_right_ear_z": z_coords[3],
            "avg_c7_x": x_coords[4],
            "avg_c7_y": y_coords[4],
            "avg_c7_z": z_coords[4],
            "posture_correct": posture_correct,
            "img_filename": img_filename,
            "cnt": cnt
        }
    ]

    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors == []:
        print(f"Data inserted successfully into {table_id}")
    else:
        print(f"Encountered errors while inserting rows: {errors}")

def calculate_and_save_results(correct_or_incorrect, posture_correct, length, year_id, month_id, day_id):
    x_coords, y_coords, z_coords = mean_landmark_results[correct_or_incorrect]
    
    img_filename = f"average_{'correct' if posture_correct else 'incorrect'}_{year_id}-{month_id}-{day_id}.png"
    
    save_results_to_bigquery(year_id, month_id, day_id, x_coords, y_coords, z_coords, posture_correct, img_filename, length)

# 결과 계산 및 BigQuery 저장
calculate_and_save_results('correct', True, len_data_correct, year_id, month_id, day_id)
calculate_and_save_results('incorrect', False, len_data_incorrect, year_id, month_id, day_id)

# 시간 측정 종료
end_time = time.time()

# 걸린 시간 출력
elapsed_time = end_time - start_time
print(f"분석에 걸린 시간: {elapsed_time:.5f}초")