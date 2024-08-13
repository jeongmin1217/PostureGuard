from django.urls import path
from .views import send_image

urlpatterns = [
    path('send-image/', send_image, name='send_image'),
]
