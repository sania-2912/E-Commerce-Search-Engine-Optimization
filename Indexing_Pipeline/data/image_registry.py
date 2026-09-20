"""Image ID mapping registry"""
from typing import Dict, Optional

class ImageRegistry:
    def __init__(self):
        self.id_to_path: Dict[int, str] = {}
        self.path_to_id: Dict[str, int] = {}

    def register(self, image_id: int, image_path: str):
        self.id_to_path[image_id] = image_path
        self.path_to_id[image_path] = image_id

    def get_path(self, image_id: int) -> Optional[str]:
        return self.id_to_path.get(image_id)

    def get_id(self, image_path: str) -> Optional[int]:
        return self.path_to_id.get(image_path)
