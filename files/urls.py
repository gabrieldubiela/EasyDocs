from django.urls import path
from . import views

app_name = 'files'

urlpatterns = [
    path('download/<int:file_id>/', views.download_file, name='download_file'),
]
