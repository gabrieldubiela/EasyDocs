from django.urls import path
from . import views

app_name = 'files'

urlpatterns = [
    # Download de arquivos enviados e de PDFs gerados (mantém como estava)
    path('download/<int:file_id>/', views.download_file, name='download_file'),

    # Tela principal: listagem de templates, PDFs gerados, ações do gerador de PDF
    path('pdf-generator/', views.pdf_generator_view, name='pdf_generator'),

    # Criar novo template de PDF
    path('criar-template/', views.criar_template_view, name='criar_template'),

    # Preencher um template selecionado (gera PDF)
    path('preencher/<int:template_id>/', views.preencher_template_view, name='preencher_template'),
    
    path('files/', views.file_management_view, name='file_management'),
    path('files/create-folder/', views.create_folder_view, name='create_folder'),
    path('files/upload/', views.upload_file_view, name='upload_file'),
    path('files/delete/<int:file_id>/', views.delete_file_view, name='delete_file'),
    path('files/delete-folder/<int:folder_id>/', views.delete_folder_view, name='delete_folder'),
]
