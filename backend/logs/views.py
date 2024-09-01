from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .camera_kafka import send_image_to_kafka  # camera_kafka 파일에서 함수 가져오기
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from google.cloud import bigquery
from datetime import datetime, timedelta
import numpy as np
from .landmark_3d import create_landmark_image

@csrf_exempt
def send_image(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data['image'].split(',')[1]
            send_image_to_kafka(image_data)  # Kafka로 이미지 전송
            return JsonResponse({'status': 'Image sent to Kafka'})
        except Exception as e:
            return JsonResponse({'status': 'Error', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'Invalid request'}, status=400)

@csrf_exempt
def analyze_result(request):
    if request.method == 'POST':
        try:
            # HTTP POST 요청으로 전송된 JSON 데이터를 파싱
            data = json.loads(request.body)

            print(data)

            # Channels의 채널 레이어를 가져오기
            channel_layer = get_channel_layer()

            # logs_group이라는 그룹에 데이터 전송
            async_to_sync(channel_layer.group_send)(
                'logs_group',  # 모든 클라이언트가 이 그룹에 연결됩니다.
                {
                    'type': 'logs_message',  # Consumer에서 처리할 이벤트 타입을 정의합니다.
                    'message': data  # 전송할 메시지를 설정합니다.
                }
            )
            return JsonResponse({'status': 'success', 'data': data})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'failed'}, status=405)

def check_year_data(request):
    year_id = request.GET.get('year_id')

    client = bigquery.Client()
    query = f"""
        SELECT month_id, day_id
        FROM `postureguard-432006.dataset_pg.tb_daily_stat`
        WHERE year_id = {year_id}
        GROUP BY month_id, day_id
    """
    query_job = client.query(query)
    results = query_job.result()

    # days_with_data = [row.day_id for row in results]

    data_by_month = {}
    for row in results:
        if row.month_id not in data_by_month:
            data_by_month[row.month_id] = []
        data_by_month[row.month_id].append(row.day_id)

    return JsonResponse({'data_by_month': data_by_month})

def get_daily_data(request):
    year_id = request.GET.get('year_id')
    month_id = request.GET.get('month_id')
    day_id = request.GET.get('day_id')

    client = bigquery.Client()

    query = f"""
        SELECT cnt, posture_correct, img_filename
        FROM `postureguard-432006.dataset_pg.tb_daily_stat`
        WHERE year_id = {year_id} AND month_id = {month_id} AND day_id = {day_id}
    """
    query_job = client.query(query)
    results = query_job.result()

    if results.total_rows == 0:
        return JsonResponse({'error': 'No data found for this date'}, status=404)

    correct_cnt = 0
    incorrect_cnt = 0
    correct_img_filename = None
    incorrect_img_filename = None

    for row in results:
        if row.posture_correct:
            correct_cnt = row.cnt
            correct_img_filename = f"average_correct_{year_id}-{month_id}-{day_id}.png"
        else:
            incorrect_cnt = row.cnt
            incorrect_img_filename = f"average_incorrect_{year_id}-{month_id}-{day_id}.png"

    if correct_cnt + incorrect_cnt == 0:
        score = 0
    else:
        score = round((correct_cnt / (correct_cnt + incorrect_cnt)) * 100, 2)

    return JsonResponse({
        "score": score,
        "correct_img_filename": correct_img_filename,
        "incorrect_img_filename": incorrect_img_filename
    })

def get_weekly_data(request):
    # 오늘 날짜 계산
    end_date = datetime.today()
    start_date = end_date - timedelta(days=7)

    # 연도, 월, 일을 추출
    end_year = end_date.year
    end_month = end_date.month
    end_day = end_date.day

    start_year = start_date.year
    start_month = start_date.month
    start_day = start_date.day

    client = bigquery.Client()

    # BigQuery 쿼리: 주어진 기간에 걸쳐 있는 모든 데이터를 가져옵니다.
    query = f"""
        SELECT cnt, posture_correct
        FROM `postureguard-432006.dataset_pg.tb_daily_stat`
        WHERE 
            (year_id = {start_year} AND month_id = {start_month} AND day_id >= {start_day}) OR
            (year_id = {end_year} AND month_id = {end_month} AND day_id <= {end_day}) OR
            (year_id = {start_year} AND month_id > {start_month}) OR
            (year_id = {end_year} AND month_id < {end_month}) OR
            (year_id = {start_year} AND year_id = {end_year} AND month_id = {start_month} AND month_id = {end_month} AND day_id >= {start_day} AND day_id <= {end_day})
    """
    query_job = client.query(query)
    results = query_job.result()

    correct_cnt = 0
    incorrect_cnt = 0

    for row in results:
        if row.posture_correct:
            correct_cnt += row.cnt
        else:
            incorrect_cnt += row.cnt

    # 주간 점수 계산
    if correct_cnt + incorrect_cnt == 0:
        score = 0
    else:
        score = round((correct_cnt / (correct_cnt + incorrect_cnt)) * 100,2)

    return JsonResponse({
        "score": score,
    })

def get_weekly_average_landmarks(request):
    # 오늘 날짜 계산
    end_date = datetime.today()
    start_date = end_date - timedelta(days=7)

    # 연도, 월, 일을 추출
    end_year = end_date.year
    end_month = end_date.month
    end_day = end_date.day

    start_year = start_date.year
    start_month = start_date.month
    start_day = start_date.day

    client = bigquery.Client()

    # BigQuery 쿼리: posture_correct가 True인 경우의 주어진 기간에 걸쳐 있는 평균 좌표 데이터를 가져옴
    query_true = f"""
        SELECT AVG(avg_left_shoulder_x) as avg_left_shoulder_x, AVG(avg_left_shoulder_y) as avg_left_shoulder_y, AVG(avg_left_shoulder_z) as avg_left_shoulder_z,
               AVG(avg_right_shoulder_x) as avg_right_shoulder_x, AVG(avg_right_shoulder_y) as avg_right_shoulder_y, AVG(avg_right_shoulder_z) as avg_right_shoulder_z,
               AVG(avg_left_ear_x) as avg_left_ear_x, AVG(avg_left_ear_y) as avg_left_ear_y, AVG(avg_left_ear_z) as avg_left_ear_z,
               AVG(avg_right_ear_x) as avg_right_ear_x, AVG(avg_right_ear_y) as avg_right_ear_y, AVG(avg_right_ear_z) as avg_right_ear_z,
               AVG(avg_c7_x) as avg_c7_x, AVG(avg_c7_y) as avg_c7_y, AVG(avg_c7_z) as avg_c7_z
        FROM `postureguard-432006.dataset_pg.tb_daily_stat`
        WHERE posture_correct = True
        AND (year_id = {start_year} AND month_id = {start_month} AND day_id >= {start_day}) OR
            (year_id = {end_year} AND month_id = {end_month} AND day_id <= {end_day}) OR
            (year_id = {start_year} AND month_id > {start_month}) OR
            (year_id = {end_year} AND month_id < {end_month}) OR
            (year_id = {start_year} AND year_id = {end_year} AND month_id = {start_month} AND month_id = {end_month} AND day_id >= {start_day} AND day_id <= {end_day})
    """

    query_false = f"""
        SELECT AVG(avg_left_shoulder_x) as avg_left_shoulder_x, AVG(avg_left_shoulder_y) as avg_left_shoulder_y, AVG(avg_left_shoulder_z) as avg_left_shoulder_z,
               AVG(avg_right_shoulder_x) as avg_right_shoulder_x, AVG(avg_right_shoulder_y) as avg_right_shoulder_y, AVG(avg_right_shoulder_z) as avg_right_shoulder_z,
               AVG(avg_left_ear_x) as avg_left_ear_x, AVG(avg_left_ear_y) as avg_left_ear_y, AVG(avg_left_ear_z) as avg_left_ear_z,
               AVG(avg_right_ear_x) as avg_right_ear_x, AVG(avg_right_ear_y) as avg_right_ear_y, AVG(avg_right_ear_z) as avg_right_ear_z,
               AVG(avg_c7_x) as avg_c7_x, AVG(avg_c7_y) as avg_c7_y, AVG(avg_c7_z) as avg_c7_z
        FROM `postureguard-432006.dataset_pg.tb_daily_stat`
        WHERE posture_correct = False
        AND (year_id = {start_year} AND month_id = {start_month} AND day_id >= {start_day}) OR
            (year_id = {end_year} AND month_id = {end_month} AND day_id <= {end_day}) OR
            (year_id = {start_year} AND month_id > {start_month}) OR
            (year_id = {end_year} AND month_id < {end_month}) OR
            (year_id = {start_year} AND year_id = {end_year} AND month_id = {start_month} AND month_id = {end_month} AND day_id >= {start_day} AND day_id <= {end_day})
    """

    query_job_true = client.query(query_true)
    query_job_false = client.query(query_false)

    results_true = query_job_true.result()
    results_false = query_job_false.result()

    # 평균 좌표 계산
    weekly_avg_landmarks_true = {}
    weekly_avg_landmarks_false = {}

    for row in results_true:
        weekly_avg_landmarks_true = {
            'left_shoulder': {'x': row.avg_left_shoulder_x, 'y': row.avg_left_shoulder_y, 'z': row.avg_left_shoulder_z},
            'right_shoulder': {'x': row.avg_right_shoulder_x, 'y': row.avg_right_shoulder_y, 'z': row.avg_right_shoulder_z},
            'left_ear': {'x': row.avg_left_ear_x, 'y': row.avg_left_ear_y, 'z': row.avg_left_ear_z},
            'right_ear': {'x': row.avg_right_ear_x, 'y': row.avg_right_ear_y, 'z': row.avg_right_ear_z},
            'c7': {'x': row.avg_c7_x, 'y': row.avg_c7_y, 'z': row.avg_c7_z}
        }

    for row in results_false:
        weekly_avg_landmarks_false = {
            'left_shoulder': {'x': row.avg_left_shoulder_x, 'y': row.avg_left_shoulder_y, 'z': row.avg_left_shoulder_z},
            'right_shoulder': {'x': row.avg_right_shoulder_x, 'y': row.avg_right_shoulder_y, 'z': row.avg_right_shoulder_z},
            'left_ear': {'x': row.avg_left_ear_x, 'y': row.avg_left_ear_y, 'z': row.avg_left_ear_z},
            'right_ear': {'x': row.avg_right_ear_x, 'y': row.avg_right_ear_y, 'z': row.avg_right_ear_z},
            'c7': {'x': row.avg_c7_x, 'y': row.avg_c7_y, 'z': row.avg_c7_z}
        }

    return weekly_avg_landmarks_true, weekly_avg_landmarks_false

def get_weekly_average_landmarks_image(request):
    # get_weekly_average_landmarks 함수로부터 주간 평균 좌표를 가져옴
    weekly_avg_landmarks_true, weekly_avg_landmarks_false = get_weekly_average_landmarks(request)

    # 평균 좌표를 바탕으로 이미지를 생성하고, 이를 base64로 인코딩
    img_str_true = create_landmark_image(weekly_avg_landmarks_true)
    img_str_false = create_landmark_image(weekly_avg_landmarks_false)

    return JsonResponse({
        "image_true": img_str_true,
        "image_false": img_str_false,
    })
