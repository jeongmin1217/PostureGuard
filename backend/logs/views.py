from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .camera_kafka import send_image_to_kafka  # camera_kafka 파일에서 함수 가져오기
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
