from django.urls import path
from .views import send_image, analyze_result, check_year_data, get_daily_data, get_weekly_data, get_weekly_average_landmarks_image

urlpatterns = [
    path('send-image/', send_image, name='send_image'),
    path('analyze-result/', analyze_result, name='analyze_result'),
    path('check-date-data/', check_year_data, name='check_year_data'),
    path('get-daily-data/', get_daily_data, name='get_daily_data'),
    path('get-weekly-data/', get_weekly_data, name='get_weekly_data'),
    path('get-weekly-average-landmarks-image/', get_weekly_average_landmarks_image, name='get_weekly_average_landmarks_image'),    
]
