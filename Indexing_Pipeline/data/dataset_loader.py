"""Dataset loading utilities"""
import os
from pathlib import Path
from typing import List
from Indexing_Pipeline.utils.validation import validate_image_path, validate_image_format
from Indexing_Pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)

class DatasetLoader:
    def __init__(self, image_dir: str, supported_formats: List[str] = None):
        self.image_dir = image_dir
        self.supported_formats = supported_formats or [".jpg", ".jpeg", ".png", ".webp"]
        self.image_paths = []

    def load_images(self) -> List[str]:
        image_paths = []
        for file_path in Path(self.image_dir).rglob("*"):
            if file_path.is_file():
                str_path = str(file_path)
                if validate_image_path(str_path) and validate_image_format(str_path, self.supported_formats):
                    image_paths.append(str_path)
        self.image_paths = sorted(image_paths)
        logger.info(f"Loaded {len(self.image_paths)} valid images from {self.image_dir}")
        return self.image_paths
