from django.http import FileResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from .models import FileUpload
from .supabase_storage import supabase_storage
import requests
import logging
import mimetypes

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
