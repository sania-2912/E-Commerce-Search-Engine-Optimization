"""Validation utilities"""
import os
from typing import List

def validate_image_path(path: str) -> bool:
    return os.path.exists(path) and os.path.isfile(path)

def validate_image_format(path: str, supported_formats: List[str]) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in [f.lower() for f in supported_formats]
