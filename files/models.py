from django.db import models
from django.conf import settings
from django.utils import timezone

class DocumentFolder(models.Model):
    """Model para organizar documentos em pastas"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='document_folders')
    folder_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent_folder = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['folder_name']
        verbose_name = 'Pasta de Documentos'
        verbose_name_plural = 'Pastas de Documentos'
        unique_together = ('user', 'folder_name', 'parent_folder')

    def __str__(self):
        return self.folder_name

class FileUpload(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
        ('xlsx', 'Excel'),
        ('image', 'Image'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='pdf')
    file_size = models.BigIntegerField()
    file_path = models.CharField(max_length=500)
    folder = models.ForeignKey(DocumentFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name='files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Arquivo Enviado'
        verbose_name_plural = 'Arquivos Enviados'

    def __str__(self):
        return self.file_name

class PDFTemplate(models.Model):
    """Model para templates de geração de PDF"""

    TEMPLATE_TYPE_CHOICES = [
        ('contract', 'Contrato'),
        ('report', 'Relatório'),
        ('proposal', 'Proposta'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pdf_templates')
    template_name = models.CharField(max_length=255, unique=False)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, default='proposal')
    description = models.TextField(blank=True, null=True)
    html_content = models.TextField()
    css_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    logo_url = models.URLField(blank=True, null=True)
    header_image_url = models.URLField(blank=True, null=True)
    footer_image_url = models.URLField(blank=True, null=True)
    watermark_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Template PDF'
        verbose_name_plural = 'Templates PDF'

    def __str__(self):
        return self.template_name

class GeneratedPDF(models.Model):
    """Model para PDFs gerados a partir de templates"""

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('completed', 'Concluído'),
        ('failed', 'Falha'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generated_pdfs')
    template = models.ForeignKey(PDFTemplate, on_delete=models.SET_NULL, null=True, related_name='generated_pdfs')
    pdf_name = models.CharField(max_length=255)
    pdf_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_size = models.BigIntegerField(null=True, blank=True)
    data_used = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'PDF Gerado'
        verbose_name_plural = 'PDFs Gerados'

    def __str__(self):
        return self.pdf_name

class FileTag(models.Model):
    """Model para tags/categorias de arquivos"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='file_tags')
    tag_name = models.CharField(max_length=100)
    color_hex = models.CharField(max_length=7, default='#3B82F6')
    files = models.ManyToManyField(FileUpload, related_name='tags', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['tag_name']
        verbose_name = 'Tag de Arquivo'
        verbose_name_plural = 'Tags de Arquivos'
        unique_together = ('user', 'tag_name')

    def __str__(self):
        return self.tag_name
