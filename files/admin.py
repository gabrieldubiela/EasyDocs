from django.contrib import admin
from django.utils.html import format_html
from .models import FileUpload, PDFTemplate, GeneratedPDF, DocumentFolder, FileTag
from .forms import FileUploadForm, PDFTemplateForm
from .supabase_storage import supabase_storage
import re
import unicodedata
import uuid
import logging

logger = logging.getLogger(__name__)

def slugify_filename(filename):
    filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')
    filename = re.sub(r'[^\w.\-]', '_', filename)
    return filename

@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    form = FileUploadForm
    list_display = (
        'file_name', 'user', 'file_type', 'folder',
        'formatted_file_size', 'uploaded_at', 'download_link'
    )
    list_filter = ('file_type', 'uploaded_at', 'user', 'folder') 
    search_fields = ('file_name', 'description')
    readonly_fields = ('uploaded_at', 'updated_at', 'file_size', 'file_path', 'file_type')

    # ESSENCIAL para funcionar o filtro pela pasta do usuário
    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)
        class CustomForm(Form):
            def __new__(cls, *args, **kw):
                kw['request'] = request
                return Form(*args, **kw)
        return CustomForm

    def get_field_queryset(self, db, db_field, request):
        if db_field.name == 'folder':
            return DocumentFolder.objects.filter(user=request.user)
        return super().get_field_queryset(db, db_field, request)

    def formatted_file_size(self, obj):
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            if size_mb < 1:
                return f"{obj.file_size / 1024:.2f} KB"
            return f"{size_mb:.2f} MB"
        return "N/A"
    formatted_file_size.short_description = 'Tamanho'

    def download_link(self, obj):
        if obj.file_path:
            try:
                signed_url = supabase_storage.get_signed_url(obj.file_path, expires_in=600)
                return format_html(
                    '<a class="button" href="{}" target="_blank">Baixar</a>',
                    signed_url
                )
            except Exception as e:
                logger.error(f"Erro ao gerar signed URL: {e}")
                return "Indisponível"
        return "N/A"
    download_link.short_description = 'Download'

    def delete_model(self, request, obj):
        if obj.file_path:
            try:
                supabase_storage.delete_file(obj.file_path)
            except Exception as e:
                logger.error(f"Erro ao remover do Storage: {e}")
                self.message_user(request, "Erro ao remover do Storage.", level='error')
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.file_path:
                try:
                    supabase_storage.delete_file(obj.file_path)
                except Exception as e:
                    logger.error(f"Erro ao remover {obj.file_path}: {e}")
                    self.message_user(request, f"Erro ao remover {obj.file_name} do storage.", level='error')
        super().delete_queryset(request, queryset)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        if 'file' in form.cleaned_data and form.cleaned_data['file']:
            file = form.cleaned_data['file']
            obj.file_size = file.size
            file_ext = file.name.split('.')[-1].lower()
            ext_to_type = {
                'pdf': 'pdf',
                'doc': 'doc',
                'docx': 'docx',
                'txt': 'txt',
                'xls': 'xls',
                'xlsx': 'xlsx',
                'jpg': 'image',
                'jpeg': 'image',
                'png': 'image',
                'gif': 'image',
            }
            obj.file_type = ext_to_type.get(file_ext, 'other')
            sanitized_name = slugify_filename(file.name)
            unique_name = f"{uuid.uuid4()}_{sanitized_name}"
            if obj.folder:
                folder_path = slugify_filename(obj.folder.folder_name)
                file_path = f"{request.user.id}/{folder_path}/{unique_name}"
            else:
                file_path = f"{request.user.id}/{unique_name}"
            if change and obj.file_path and obj.file_path != file_path:
                try:
                    supabase_storage.delete_file(obj.file_path)
                except Exception as e:
                    logger.warning(f"Falha ao remover arquivo antigo: {e}")
            try:
                supabase_storage.upload_file(file, file_path)
                obj.file_path = file_path
                self.message_user(request, f'Arquivo "{file.name}" enviado com sucesso para Supabase Storage!')
            except Exception as e:
                logger.error(f"Erro no upload para Supabase: {e}")
                self.message_user(request, '⚠ Arquivo salvo no banco, mas erro no upload.', level=30)
                obj.file_path = file.name
        super().save_model(request, obj, form, change)

@admin.register(GeneratedPDF)
class GeneratedPDFAdmin(admin.ModelAdmin):
    list_display = (
        'pdf_name', 'user', 'status', 'template',
        'generated_at', 'download_link'
    )
    list_filter = ('status', 'generated_at', 'user')
    search_fields = ('pdf_name',)
    readonly_fields = ('generated_at', 'completed_at')

    def download_link(self, obj):
        if obj.status == 'completed' and obj.pdf_path:
            try:
                signed_url = supabase_storage.get_signed_url(obj.pdf_path, expires_in=600)
                return format_html(
                    '<a class="button" href="{}" target="_blank">Download</a>',
                    signed_url
                )
            except Exception as e:
                logger.error(f"Erro ao gerar signed URL: {e}")
                return "Indisponível"
        return "N/A"
    download_link.short_description = 'Download'

@admin.register(PDFTemplate)
class PDFTemplateAdmin(admin.ModelAdmin):
    form = PDFTemplateForm
    list_display = ('template_name', 'user', 'template_type', 'is_active', 'created_at')
    list_filter = ('template_type', 'is_active', 'created_at')
    search_fields = ('template_name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)
        
@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    list_display = ('folder_name', 'user', 'parent_folder', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('folder_name',)

@admin.register(FileTag)
class FileTagAdmin(admin.ModelAdmin):
    list_display = ('tag_name', 'user', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('tag_name',)
