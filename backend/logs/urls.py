from django.urls import path
from .views import send_image, analyze_result

urlpatterns = [
    path('send-image/', send_image, name='send_image'),
    path('analyze-result/', analyze_result, name='analyze_result'),
]
