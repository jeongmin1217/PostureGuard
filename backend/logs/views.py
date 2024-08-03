import subprocess
from django.http import JsonResponse
import os
import signal

log_process = None

def start_log_generation(request):
    global log_process
    if log_process is None:
        # 절대 경로로 수정
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../log_kafka.py')
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
