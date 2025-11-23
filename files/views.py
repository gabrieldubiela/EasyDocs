# D:\Gabriel\Programs\EasyDocs\files\views.py

from django.http import FileResponse, HttpResponseNotFound, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template import Template, Context
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.paginator import Paginator
from django import forms

from .models import FileCreated, PDFTemplate, DocumentFolder
from .forms import PDFTemplateForm, FileCreatedForm
from .supabase_storage import supabase_storage

from weasyprint import HTML

import requests
import logging
import mimetypes
import os
import io
import re

logger = logging.getLogger(__name__)

##############################################
# Função utilitária para extrair campos do template HTML
def extrair_campos_html(html_content):
    # Regex pega tudo entre {{ ... }}
    campos = re.findall(r'{{\s*([^\s}]+)\s*}}', html_content)
    # Ignora variáveis de loop comuns
    ignore_vars = {'item', 'linha', 'row'}
    campos_unicos = []
    for campo in campos:
        if campo not in campos_unicos and campo not in ignore_vars:
            campos_unicos.append(campo)
    return campos_unicos

def extrair_campos_lista(html_content):
    # Permite nomes com acento, ç, hífen e sublinhado!
    return re.findall(r'\{%\s*for\s+\w+\s+in\s+([\w\-_à-ÿÀ-ßçÇ]+)\s*%\}', html_content, flags=re.UNICODE)

def extrair_todos_campos_ordenados(html_content):
    pattern = re.compile(
        r'{{\s*([^\s}]+)\s*}}|\{%\s*for\s+\w+\s+in\s+([^\s%}]+)\s*%\}',
        re.UNICODE
    )
    encontrados = []
    for match in pattern.finditer(html_content):
        campo_var = match.group(1)
        campo_lista = match.group(2)
        if campo_var and campo_var not in encontrados and campo_var not in {'item', 'linha', 'row'}:
            encontrados.append(campo_var)
        if campo_lista and campo_lista not in encontrados and campo_lista not in {'item', 'linha', 'row'}:
            encontrados.append(campo_lista)
    return encontrados

def extrair_campos_lista(html_content):
    return re.findall(r'\{%\s*for\s+\w+\s+in\s+([^\s%}]+)\s*%\}', html_content, flags=re.UNICODE)

##############################################

@login_required
def download_file(request, file_id):
    try:
        file_obj = FileCreated.objects.get(id=file_id, user=request.user)
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
            return redirect(signed_url)
        else:
            disposition = f'attachment; filename="{original_name}"'
        response_file = FileResponse(
            response.raw,
            content_type=content_type,
        )
        response_file['Content-Disposition'] = disposition
        logger.info(f"File downloaded successfully: {original_name}")
        return response_file
    except FileCreated.DoesNotExist:
        logger.error(f"File not found in database: {file_id}")
        return HttpResponseNotFound("Arquivo não encontrado no banco de dados")
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        return HttpResponseNotFound(f"Erro ao baixar: {str(e)}")

##############################################

@login_required
def pdf_generator_view(request):
    templates = PDFTemplate.objects.filter(user=request.user, is_active=True)
    all_pdfs = FileCreated.objects.filter(user=request.user, is_generated=True).order_by('-created_at')
    paginator = Paginator(all_pdfs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'pdf_generator.html', {
        'templates': templates,
        'page_obj': page_obj,
    })

##############################################

@login_required
def criar_template_view(request):
    if request.method == 'POST':
        form = PDFTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            return redirect('files:pdf_generator')
    else:
        form = PDFTemplateForm()
    return render(request, 'criar_template.html', {'form': form})

##############################################

@login_required
def preencher_template_view(request, template_id):
    # 1. Busca template
    template_obj = get_object_or_404(PDFTemplate, id=template_id, user=request.user)
    html_content = template_obj.html_content
    
    html_cabecalho_rodape = '''
    <style>
    @page {
            size: A4;
            margin: 110px 70px 70px 70px;

            @top-left {
                content: url('{{ header_image_url }}');
                margin-left: -110px;
                margin-top: -25px;
            }

            @bottom-center {
                content: url('{{ footer_image_url }}');
            }
        }
    .watermark {
            position: fixed;
            top: -400px;
            left: -227px;
            width: 25.4cm;
            height: 39.7cm;
            opacity: 0.9;
            z-index: -1;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            pointer-events: none;
        }
    </style>
    <div class="watermark" style="background-image: url('{{ watermark_url }}');"></div>
    '''
    
    IGNORAR_CAMPOS = ['header_image_url', 'footer_image_url', 'watermark_url']
    campos = [campo for campo in extrair_todos_campos_ordenados(html_content) if campo not in IGNORAR_CAMPOS]
    campos_lista = extrair_campos_lista(html_content)

    # 2. Cria formulário dinâmico para esses campos
    class DynamicTemplateForm(forms.Form):
        pass
    for campo in campos:
        if campo in campos_lista:
            DynamicTemplateForm.base_fields[campo] = forms.CharField(
                label=campo.replace('_', ' ').capitalize(),
                required=False,
                widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Digite um item por linha'})
            )
        else:
            DynamicTemplateForm.base_fields[campo] = forms.CharField(
                label=campo.replace('_', ' ').capitalize(),
                required=False
            )
    
    folders = DocumentFolder.objects.filter(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'generate')  # default é gerar

        if action == 'delete':
            file_id = request.POST.get('file_id')
            if file_id:
                file = get_object_or_404(FileCreated, id=file_id, user=request.user)
                try:
                    if file.file_path:
                        supabase_storage.delete_file(file.file_path)
                except Exception:
                    pass  # ignora erro se não encontrar no storage
                file.delete()
            # Após excluir, volta ao form "limpo"
            form = DynamicTemplateForm(request.POST)
            return render(request, 'preencher_template.html', {
                "form": form,
                "template_obj": template_obj,
                "folders": folders,
            })

        # --- Ação padrão: gerar PDF ---
        form = DynamicTemplateForm(request.POST)
        if form.is_valid():
            context = form.cleaned_data
            for campo_lista in campos_lista:
                if campo_lista in context and isinstance(context[campo_lista], str):
                    context[campo_lista] = [linha.strip() for linha in context[campo_lista].splitlines() if linha.strip()]
            user_folder = f"{request.user.id}"
            header_path = f"{user_folder}/header.png"
            footer_path = f"{user_folder}/footer.png"
            watermark_path = f"{user_folder}/watermark.png"
            context['header_image_url'] = supabase_storage.get_signed_url(header_path, expires_in=600)
            context['footer_image_url'] = supabase_storage.get_signed_url(footer_path, expires_in=600)
            context['watermark_url'] = supabase_storage.get_signed_url(watermark_path, expires_in=600)
            html_content_final = html_cabecalho_rodape + html_content
            html_renderizado = Template(html_content_final).render(Context(context))
            template_dir = os.path.join(os.getcwd(), 'static')
            pdf_bytes = HTML(
                string=html_renderizado,
                base_url=template_dir
            ).write_pdf()

            # Upload para Supabase e registro no banco
            nome_func = f"nome_pdf_{template_obj.template_name.lower()}"
            file_name = globals()[nome_func](context, template_obj)

            folder_id = request.POST.get('folder_id')
            folder = DocumentFolder.objects.get(id=folder_id, user=request.user)
            pdf_storage_path = f"{folder.folder_name}/{file_name}"
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_file.name = file_name
            supabase_storage.upload_file(pdf_file, pdf_storage_path)
            file_size = pdf_file.getbuffer().nbytes
            file_obj = FileCreated.objects.create(
                user=request.user,
                template=template_obj,
                file_name=file_name,
                file_path=pdf_storage_path,
                status='completed',
                file_size=file_size,
                data_used=context,
                is_generated=True,
                folder=folder,
            )

            pdf_url = supabase_storage.get_signed_url(pdf_storage_path, expires_in=600)
            file_id = file_obj.id

            return render(request, 'preencher_template.html', {
                "form": form,
                "template_obj": template_obj,
                "folders": folders,
                "pdf_url": pdf_url,
                "file_id": file_id,
                'file_name': file_name,
            })
        else:
            # Form inválido
            return render(request, 'preencher_template.html', {
                "form": form,
                "template_obj": template_obj,
                "folders": folders,
            })

    else:
        form = DynamicTemplateForm()
        response = render(request, 'preencher_template.html', {
            'form': form,
            'template_obj': template_obj,
            'folders': folders,
        })
        response['Location'] = request.path + '#pdf-actions'
        response.status_code = 303
        return response

##############################################

@login_required
def file_management_view(request):
    root_folders = DocumentFolder.objects.filter(user=request.user, parent_folder__isnull=True)
    files = FileCreated.objects.filter(user=request.user)
    return render(request, 'management.html', {
        'folders': root_folders,
        'files': files,
    })

###############################################

@login_required
def create_folder_view(request):
    if request.method == 'POST':
        folder_name = request.POST.get('folder_name', '').strip()
        parent_id = request.POST.get('parent_folder')

        # CHECAGEM EXTRA para evitar duplicação
        parent_folder = DocumentFolder.objects.filter(id=parent_id).first() if parent_id else None

        # Evita criar se já existe pasta com mesmo nome e mesmo parent para o usuário
        exists = DocumentFolder.objects.filter(
            user=request.user,
            folder_name=folder_name,
            parent_folder=parent_folder
        ).exists()

        logger.warning(f'CRIANDO PASTA: nome={folder_name!r} | parent={parent_folder} | já existe={exists}')

        if folder_name and not exists:
            DocumentFolder.objects.create(
                user=request.user,
                folder_name=folder_name,
                parent_folder=parent_folder
            )
        return redirect('files:file_management')

    folders = DocumentFolder.objects.filter(user=request.user)
    return render(request, 'create_folder.html', {'folders': folders})

###############################################

@login_required
def upload_file_view(request):
    if request.method == 'POST':
        form = FileCreatedForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            # Nome e tamanho do arquivo
            instance.file_name = form.cleaned_data['file'].name
            instance.file_size = form.cleaned_data['file'].size

            # Definir file_type automaticamente:
            ext = os.path.splitext(instance.file_name)[1].lower()
            if ext == ".pdf":
                instance.file_type = "pdf"
            elif ext in [".doc", ".docx"]:
                instance.file_type = "docx"
            elif ext == ".txt":
                instance.file_type = "txt"
            elif ext in [".xls", ".xlsx"]:
                instance.file_type = "xlsx"
            elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                instance.file_type = "image"
            else:
                instance.file_type = "txt"  # ou algum valor padrão

            instance.file_path = supabase_storage.upload_file(
                form.cleaned_data['file'],
                f"{instance.folder.folder_name}/{form.cleaned_data['file'].name}"
            )
            instance.is_generated = False
            instance.save()
            return redirect('files:file_management')
    else:
        form = FileCreatedForm(request=request)
    return render(request, 'upload_file.html', {'form': form})

#################################################
@login_required
def delete_file_view(request, file_id):
    file = get_object_or_404(FileCreated, id=file_id, user=request.user)
    file.delete()  # Remove do banco de dados
    return redirect('files:file_management')

##############################################

@login_required
def delete_folder_view(request, folder_id):
    folder = get_object_or_404(DocumentFolder, id=folder_id, user=request.user)

    # EXCLUI ARQUIVOS DA PASTA, DO BANCO E DO STORAGE
    files = FileCreated.objects.filter(folder=folder)
    for file in files:
        try:
            if file.file_path:
                supabase_storage.delete_file(file.file_path)
        except Exception as e:
            logger.error(f"Erro ao apagar do storage: {file.file_path} - {str(e)}")
        file.delete()  # Exclui do banco

    # EXCLUI TODOS OS ARQUIVOS DIRETO DO STORAGE (inclui registros órfãos)
    supabase_storage.delete_folder_from_storage(folder.folder_name + '/')

    # EXCLUI SUBPASTAS E TUDO DENTRO DELAS RECURSIVAMENTE
    subfolders = DocumentFolder.objects.filter(parent_folder=folder)
    for subfolder in subfolders:
        delete_folder_view(request, subfolder.id)

    # EXCLUI A PRÓPRIA PASTA
    folder.delete()

    return redirect('files:file_management')


##########################################################

def nome_pdf_proposta(context, template_obj):
    # Aqui você define a lógica exclusiva do template "Proposal"
    numero = context.get('número_da_proposta', 'novo').replace('/', '-').replace('\\', '-').replace(' ', '_')
    return f"{template_obj.template_name}_{numero}.pdf"
