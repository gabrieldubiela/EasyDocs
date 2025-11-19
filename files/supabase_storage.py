from supabase import create_client, Client
from django.conf import settings
import logging
import mimetypes

logger = logging.getLogger(__name__)

class SupabaseStorageService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.bucket_name = settings.SUPABASE_BUCKET
        logger.info(f"Supabase Storage initialized - Bucket: {self.bucket_name}")

    def upload_file(self, file, file_path):
        try:
            file.seek(0)
            file_content = file.read()
            content_type, _ = mimetypes.guess_type(file.name)
            if not content_type:
                content_type = "application/octet-stream"
            options = {
                "content-type": content_type
            }
            response = self.supabase.storage.from_(self.bucket_name).upload(
                file_path,
                file_content,
                options
            )
            logger.info(f"Upload successful: {response}")
            return response
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            raise Exception(f"Upload failed: {str(e)}")

    def get_file_url(self, file_path):
        """Get the public URL of a file"""
        try:
            logger.info(f"Getting URL for: {file_path}")
            url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
            logger.info(f"URL generated: {url}")
            if isinstance(url, dict) and 'publicUrl' in url:
                url = url['publicUrl']
            return url
        except Exception as e:
            logger.error(f"Get URL failed: {str(e)}", exc_info=True)
            raise Exception(f"Get URL failed: {str(e)}")

    def get_signed_url(self, file_path, expires_in=3600):   # <--- COLOQUE AQUI DENTRO!
        try:
            response = self.supabase.storage.from_(self.bucket_name).create_signed_url(file_path, expires_in)
            if isinstance(response, dict) and 'signedUrl' in response:
                return response['signedUrl']
            return response
        except Exception as e:
            logger.error(f"Signed URL error: {str(e)}", exc_info=True)
            raise Exception(f"Signed URL error: {str(e)}")

    def delete_file(self, file_path):
        """Delete a file from Supabase Storage"""
        try:
            print(f"DEBUG: Tentando apagar do storage -> {file_path}")
            self.supabase.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            raise Exception(f"Delete failed: {str(e)}")

supabase_storage = SupabaseStorageService()
