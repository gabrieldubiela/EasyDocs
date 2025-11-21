from django.urls import path
from . import views
from .views import gerar_pdf_view

app_name = 'files'

urlpatterns = [
    path('download/<int:file_id>/', views.download_file, name='download_file'),
    path('gerar-pdf-proposta/', gerar_pdf_view, name='gerar_pdf_proposta'),
]
