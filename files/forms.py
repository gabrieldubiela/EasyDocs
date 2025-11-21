from django import forms
from django.core.exceptions import ValidationError
from .models import FileUpload, PDFTemplate, GeneratedPDF, DocumentFolder
import os

class FileUploadForm(forms.ModelForm):
    """Formulário customizado para upload de arquivos"""
    
    file = forms.FileField(
        label='Selecione o arquivo',
        help_text='Máximo 50MB',
        required=True
    )
    folder = forms.ModelChoiceField(
        queryset=DocumentFolder.objects.none(),
        required=False,
        label="Pasta",
        help_text="Selecione a pasta (opcional)"
    )
    
    class Meta:
        model = FileUpload
        fields = ['file_name', 'file_type', 'description', 'folder']
        widgets = {
            'file_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do arquivo'
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição (opcional)'
            }),
            'folder': forms.Select(attrs={'class': 'form-control'})
        }
        
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and self.request.user.is_authenticated:
            self.fields['folder'].queryset = DocumentFolder.objects.filter(user=self.request.user)
        else:
            self.fields['folder'].queryset = DocumentFolder.objects.none()
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if file:
            if file.size > 50 * 1024 * 1024:
                raise ValidationError('Arquivo muito grande! Máximo 50MB.')
            
            allowed_extensions = ['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'gif']
            file_ext = file.name.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                raise ValidationError(f'Tipo de arquivo não permitido: .{file_ext}')
        
        return file
    
    def clean_file_name(self):
        file_name = self.cleaned_data.get('file_name')
        if not file_name:
            raise ValidationError('Nome do arquivo é obrigatório.')
        return file_name


class PDFTemplateForm(forms.ModelForm):
    """Formulário para templates PDF"""
    
    class Meta:
        model = PDFTemplate
        fields = ['template_name', 'template_type', 'description', 'html_content', 'css_content', 'is_active']
        widgets = {
            'template_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do template'
            }),
            'template_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'html_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'HTML do template'
            }),
            'css_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'CSS customizado (opcional)'
            }),
        }

class PropostaPDFForm(forms.Form):
    cliente_nome = forms.CharField(label='Nome do Cliente', max_length=255)
    cliente_cpf = forms.CharField(label='CPF do Cliente', max_length=20, required=False)
    servico_nome_abreviado = forms.CharField(label='Serviço (abreviado)', max_length=100)
    servico_nome_completo = forms.CharField(label='Serviço (completo)', max_length=255)
    localizacao = forms.CharField(label='Localização', max_length=255)
    proposta_numero = forms.CharField(label='Número da Proposta', max_length=50)
    descricao_servico = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Um item por linha'}),
        required=False,
        label="Descrição do serviço (um por linha)"
    )
    itens_nao_inclusos = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Um item por linha'}),
        required=False,
        label="Itens não inclusos (um por linha)"
    )
    valor_total = forms.CharField(label='Valor Total', max_length=20)
    forma_de_pagamento = forms.CharField(label='Forma de Pagamento', max_length=255)
    forma_prazo_execucao = forms.CharField(label='Forma/prazo de execução', max_length=255)
    data_atual = forms.CharField(label='Data Atual', max_length=40)