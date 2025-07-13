from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignal
import re
import os

class DataController(BaseController):
    
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576 # convert MB to bytes

    def validate_uploaded_file(self, file: UploadFile):
        
        # Get file extension from filename
        if not file.filename:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
            
        file_ext = os.path.splitext(file.filename)[1][1:].lower()  # Remove dot and make lowercase
        
        # Parse FILE_ALLOWED_TYPES if it's a JSON string
        allowed_types = self.app_settings.FILE_ALLOWED_TYPES
        if isinstance(allowed_types, str):
            import json
            try:
                allowed_types = json.loads(allowed_types)
            except:
                allowed_types = ["pdf", "txt", "docx"]  # fallback
        
        if file_ext not in allowed_types:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size and file.size > self.app_settings.FILE_MAX_SIZE:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value

    def generate_unique_filepath(self, orig_file_name: str, project_id: str):

        random_key = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)

        cleaned_file_name = self.get_clean_file_name(
            orig_file_name=orig_file_name
        )

        new_file_path = os.path.join(
            project_path,
            random_key + "_" + cleaned_file_name
        )

        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(
                project_path,
                random_key + "_" + cleaned_file_name
            )

        return new_file_path, random_key + "_" + cleaned_file_name

    def get_clean_file_name(self, orig_file_name: str):

        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())

        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        return cleaned_file_name


