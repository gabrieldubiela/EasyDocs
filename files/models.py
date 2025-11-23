from django.db import models
from django.conf import settings

class DocumentFolder(models.Model):
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

class FileCreated(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
        ('xlsx', 'Excel'),
        ('image', 'Image'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('completed', 'Concluído'),
        ('failed', 'Falha'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='pdf')
    file_size = models.BigIntegerField()
    file_path = models.CharField(max_length=500)
    folder = models.ForeignKey(DocumentFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name='files')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    is_generated = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    data_used = models.JSONField(default=dict, blank=True)
    template = models.ForeignKey('PDFTemplate', on_delete=models.SET_NULL, null=True, blank=True, related_name='files')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Arquivo'
        verbose_name_plural = 'Arquivos'

    def __str__(self):
        return self.file_name

class PDFTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = [
        ('contract', 'Contrato'),
        ('report', 'Relatório'),
        ('proposal', 'Proposta'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pdf_templates')
    template_name = models.CharField(max_length=255)
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