import os
from supabase import create_client, Client
from django.conf import settings

class SupabaseStorageService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.bucket_name = settings.SUPABASE_BUCKET
    
    def upload_file(self, file, file_path):
        """Upload a file to Supabase Storage"""
        try:
            response = self.supabase.storage.from_(self.bucket_name).upload(
                file_path,
                file.read()
            )
            return response
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")
    
    def get_file_url(self, file_path):
        """Get the public URL of a file"""
        url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
        return url
    
    def delete_file(self, file_path):
        """Delete a file from Supabase Storage"""
        try:
            self.supabase.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            raise Exception(f"Delete failed: {str(e)}")

# Instância global
supabase_storage = SupabaseStorageService()
