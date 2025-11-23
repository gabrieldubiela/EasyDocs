from django.urls import path
from . import views

app_name = 'files'

urlpatterns = [
    path('download/<int:file_id>/', views.download_file, name='download_file'),
    path('pdf-generator/', views.pdf_generator_view, name='pdf_generator'),
    path('create-template/', views.create_template_view, name='create_template'),
    path('fill/<int:template_id>/', views.fill_template_view, name='fill_template'),
    path('files/', views.file_management_view, name='file_management'),
    path('files/create-folder/', views.create_folder_view, name='create_folder'),
    path('files/upload/', views.upload_file_view, name='upload_file'),
    path('files/delete/<int:file_id>/', views.delete_file_view, name='delete_file'),
    path('files/delete-folder/<int:folder_id>/', views.delete_folder_view, name='delete_folder'),
]
