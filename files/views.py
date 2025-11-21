from django.http import FileResponse, HttpResponseNotFound, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import FileUpload, PDFTemplate, GeneratedPDF, DocumentFolder
from .forms import PropostaPDFForm
from weasyprint import HTML
from .supabase_storage import supabase_storage
from django.template import Template, Context
from django.shortcuts import render
from django.conf import settings
import requests
import logging
import mimetypes
import os
import io

logger = logging.getLogger(__name__)

@login_required
def download_file(request, file_id):
    try:
        file_obj = FileUpload.objects.get(id=file_id, user=request.user)
        if file_obj.is_deleted:
            return HttpResponseNotFound("Arquivo foi deletado")
        if not file_obj.file_path:
            logger.error(f"File path not found for file_id: {file_id}")
            return HttpResponseNotFound("Arquivo não encontrado no Supabase")
        signed_url = supabase_storage.get_signed_url(file_obj.file_path, expires_in=300)
        logger.info(f"Downloading file from URL: {signed_url}")
        response = requests.get(signed_url, stream=True, timeout=30)
        if response.status_code != 200:
            logger.error(f"Failed to download file: Status {response.status_code}")
            return HttpResponseNotFound("Erro ao baixar arquivo do Supabase")
        content_type, _ = mimetypes.guess_type(file_obj.file_name)
        if not content_type:
            content_type = 'application/octet-stream'
        original_name = file_obj.file_name
        if '.' not in original_name:
            possible_ext = file_obj.file_path.split('.')[-1]
            if possible_ext and possible_ext != original_name:
                original_name = f"{original_name}.{possible_ext}"
        visualizaveis = ['pdf', 'jpg', 'jpeg', 'png', 'gif']
        ext = original_name.split('.')[-1].lower()
        if ext in visualizaveis:
            disposition = f'inline; filename="{original_name}"'
        else:
            disposition = f'attachment; filename="{original_name}"'
        response_file = FileResponse(
            response.raw,
            content_type=content_type,
        )
        response_file['Content-Disposition'] = disposition
        logger.info(f"File downloaded successfully: {original_name}")
        return response_file
    except FileUpload.DoesNotExist:
        logger.error(f"File not found in database: {file_id}")
        return HttpResponseNotFound("Arquivo não encontrado no banco de dados")
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        return HttpResponseNotFound(f"Erro ao baixar: {str(e)}")

def gerar_proposta_pdf(request, template_id):
    # Caminhos dos arquivos de imagem no Supabase Storage
    logo_path = "documents/1/images_for_proposal/f6dd1126-9262-4ee6-99ca-85174b1b1bcc_cabecalho__3_.png"
    footer_path = "documents/1/images_for_proposal/61f2384b-8fdf-43f7-ad8c-e43b7cee229a_rodape__1_.png"
    watermark_path = "documents/1/images_for_proposal/7e37c619-05c2-48d1-8124-6c143610c473_marca.png"

    # Gera signed URLs para cada imagem (válidas por 10 minutos)
    logo_url = supabase_storage.get_signed_url(logo_path, expires_in=600)
    footer_url = supabase_storage.get_signed_url(footer_path, expires_in=600)
    watermark_url = supabase_storage.get_signed_url(watermark_path, expires_in=600)

    # Dados para preencher o template (exemplo)
    context = {
        "cliente_nome": "Nome do cliente",
        "servico_nome": "Nome do serviço",
        "valor_total": "1.500,00",
        "data_atual": "20/11/2025",
        # URLs das imagens do Supabase
        "logo_url": logo_url,
        "footer_url": footer_url,
        "watermark_url": watermark_url,
        "descricao_servico": [
            "Execução de alvenaria estrutural",
            "Instalação hidráulica",
            "Pintura completa"
        ],
        "itens_nao_inclusos": [
            "Materiais elétricos",
            "Janelas",
            "Portas internas"
        ]
    }

    # Pegue o template do banco (supondo que está no model PDFTemplate)
    template_obj = PDFTemplate.objects.get(id=template_id)
    html_content = template_obj.html_content  # Seu HTML com variáveis

    # Renderização das variáveis no HTML
    html_renderizado = Template(html_content).render(Context(context))
    
    # URL das fontes
    template_dir = os.path.join(os.getcwd(), 'files', 'static')

    # Geração do PDF
    pdf_bytes = HTML(
        string=html_renderizado,
        base_url=template_dir
    ).write_pdf()

    # Retorne o PDF para download
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="proposta.pdf"'
    return response

def gerar_pdf_view(request):
    if request.method == 'POST':
        form = PropostaPDFForm(request.POST)
        if form.is_valid():
            # 1. Dados recebidos do usuário
            context = form.cleaned_data
            
            # 2. Converte texto em lista (remove linhas vazias)
            desc_list = [linha.strip() for linha in context['descricao_servico'].splitlines() if linha.strip()]
            itens_list = [linha.strip() for linha in context['itens_nao_inclusos'].splitlines() if linha.strip()]
            context['descricao_servico'] = desc_list
            context['itens_nao_inclusos'] = itens_list
            
            # 3. URLs assinadas das imagens
            logo_path = "1/images_for_proposal/f6dd1126-9262-4ee6-99ca-85174b1b1bcc_cabecalho__3_.png"
            footer_path = "1/images_for_proposal/61f2384b-8fdf-43f7-ad8c-e43b7cee229a_rodape__1_.png"
            watermark_path = "1/images_for_proposal/7e37c619-05c2-48d1-8124-6c143610c473_marca.png"
            
            context['header_image_url'] = supabase_storage.get_signed_url(logo_path, expires_in=600)
            context['footer_image_url'] = supabase_storage.get_signed_url(footer_path, expires_in=600)
            context['watermark_url'] = supabase_storage.get_signed_url(watermark_path, expires_in=600)
            
            # 4. Template HTML do banco
            template_obj = PDFTemplate.objects.get(template_name='Proposta Comercial')
            template_html = template_obj.html_content
            
            # 5. Renderiza o HTML
            html_renderizado = Template(template_html).render(Context(context))
            
            # 6. Caminho das fontes
            template_dir = os.path.join(os.getcwd(), 'files', 'static')
            
            # 7. Gera PDF com base_url
            pdf_bytes = HTML(
                string=html_renderizado,
                base_url=template_dir  
            ).write_pdf()
            
            # 8. Nome do arquivo e caminho no bucket (pasta PDFs_gerados para organização)
            num = form.cleaned_data.get('proposta_numero', 'novo').replace('/', '_')
            pdf_name = f"proposta_{num}.pdf"
            pdf_storage_path = f"PDFs_gerados/{pdf_name}"

            # 9. Upload para Supabase Storage
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_file.name = pdf_name  # Necessário para mimetype no SupabaseStorageService
            supabase_storage.upload_file(pdf_file, pdf_storage_path)

            # 10. Tamanho do arquivo
            pdf_size = pdf_file.getbuffer().nbytes

            # 11. Localize ou crie pasta PDFs Gerados do usuário
            try:
                folder = DocumentFolder.objects.get(user=request.user, folder_name="PDFs gerados")
            except DocumentFolder.DoesNotExist:
                folder = DocumentFolder.objects.create(user=request.user, folder_name="PDFs gerados")

            # 12. Registro do PDF gerado
            GeneratedPDF.objects.create(
                user=request.user,
                template=template_obj,
                pdf_name=pdf_name,
                pdf_path=pdf_storage_path,
                status='completed',
                file_size=pdf_size,
                data_used=context
            )

            # 13. Download imediato para o usuário
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
            return response
    else:
        form = PropostaPDFForm()
    return render(request, 'formulario_proposta.html', {'form': form})
