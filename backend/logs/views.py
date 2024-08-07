import subprocess
from django.http import JsonResponse
import os
import signal
import base64
from django.views.decorators.csrf import csrf_exempt
import json
from .camera_kafka import send_image_to_kafka  # camera_kafka 파일에서 함수 가져오기

log_process = None

def start_log_generation(request):
    global log_process
    if log_process is None:
        # 절대 경로로 수정
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log_kafka.py')
        script_path = os.path.abspath(script_path)
        print(f"Starting log generation with script at: {script_path}")
        log_process = subprocess.Popen(['python', script_path]) #creationflags=subprocess.CREATE_NEW_CONSOLE
        return JsonResponse({'status': 'Log generation started'})
    else:
        return JsonResponse({'status': 'Log generation already running'})

def stop_log_generation(request):
    global log_process
    if log_process is not None:
        log_process.terminate()
        log_process = None
        return JsonResponse({'status': 'Log generation stopped'})
    else:
        return JsonResponse({'status': 'Log generation not running'})
    
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

