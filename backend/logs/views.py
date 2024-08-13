from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .camera_kafka import send_image_to_kafka  # camera_kafka 파일에서 함수 가져오기
    
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

