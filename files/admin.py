from django.contrib import admin
from django.utils.html import format_html
from .models import FileUpload, PDFTemplate, GeneratedPDF, DocumentFolder, FileTag
from .forms import FileUploadForm, PDFTemplateForm
from .supabase_storage import supabase_storage
import os
import re
import unicodedata

def slugify_filename(filename):
    filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')
    filename = re.sub(r'[^\w.\-]', '_', filename)
    return filename


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    form = FileUploadForm
    list_display = ('file_name', 'user', 'file_type', 'folder', 'formatted_file_size', 'uploaded_at', 'download_link')
    list_filter = ('file_type', 'uploaded_at', 'user', 'folder') 
    search_fields = ('file_name', 'description')
    readonly_fields = ('uploaded_at', 'updated_at', 'file_size', 'file_path', 'file_type')

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
                download_url = f"/files/download/{obj.id}/"
                return format_html('<a class="button" href="{}">Download</a>', download_url)
            except Exception as e:
                print(f"DEBUG: Error creating download link: {str(e)}")
                return "❌ Erro ao obter URL"
        return "N/A"
    download_link.short_description = 'Download'

    def delete_model(self, request, obj):
        print("DEBUG: Entrou no delete_model do FileUploadAdmin!")
        if obj.file_path:
            try:
                print(f"DEBUG: Tentando apagar do storage -> {obj.file_path}")
                from .supabase_storage import supabase_storage
                supabase_storage.delete_file(obj.file_path)
            except Exception as e:
                self.message_user(request, f"Erro ao remover do Storage: {e}", level='error')
        super().delete_model(request, obj)
        
    def delete_queryset(self, request, queryset):
        print("DEBUG: Entrou no delete_queryset do FileUploadAdmin!")
        for obj in queryset:
            if obj.file_path:
                print(f"DEBUG: Tentando apagar do storage -> {obj.file_path}")
                try:
                    supabase_storage.delete_file(obj.file_path)
                    print(f"DEBUG: Delete {obj.file_path} ok")
                except Exception as e:
                    print(f"DEBUG: Erro ao remover {obj.file_path}: {e}")
        queryset.delete()

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
            import uuid
            sanitized_name = slugify_filename(file.name)
            unique_name = f"{uuid.uuid4()}_{sanitized_name}"
            if obj.folder:
                folder_path = obj.folder.folder_name
                file_path = f"{request.user.id}/{folder_path}/{unique_name}"
            else:
                file_path = f"{request.user.id}/{unique_name}"
            try:
                supabase_storage.upload_file(file, file_path)
                obj.file_path = file_path
                self.message_user(request, f'✓ Arquivo "{file.name}" enviado com sucesso para Supabase Storage!')
            except Exception as e:
                self.message_user(request, f'⚠ Arquivo salvo no banco, mas erro no upload: {str(e)}', level=30)
                obj.file_path = file.name
        super().save_model(request, obj, form, change)

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


@admin.register(GeneratedPDF)
class GeneratedPDFAdmin(admin.ModelAdmin):
    list_display = ('pdf_name', 'user', 'status', 'template', 'generated_at', 'download_link')
    list_filter = ('status', 'generated_at', 'user')
    search_fields = ('pdf_name',)
    readonly_fields = ('generated_at', 'completed_at')

    def download_link(self, obj):
        """Botão para download do PDF gerado"""
        if obj.status == 'completed' and obj.pdf_path:
            try:
                url = supabase_storage.get_file_url(obj.pdf_path)
                return format_html(
                    '<a class="button" href="{}" target="_blank">Download</a>',
                    url
                )
            except:
                return "N/A"
        return "N/A"
    download_link.short_description = 'Download'


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
