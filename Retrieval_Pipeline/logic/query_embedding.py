"""Query embedding logic using BGE-Large (1024-dim)"""
import numpy as np
import torch
import torch.nn.functional as F
import Retrieval_Pipeline.models.model_loader as ml

def encode_bge_text(text: str) -> np.ndarray:
    if ml.bge_model is None or ml.bge_tokenizer is None:
        raise RuntimeError("BGE model not loaded.")
    inputs = ml.bge_tokenizer(
        [text.strip()],
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    ).to(ml.DEVICE)
    with torch.no_grad():
        out = ml.bge_model(**inputs)
        cls_vec = out[0][:, 0]
        cls_vec = F.normalize(cls_vec, p=2, dim=1)
    return cls_vec.cpu().float().numpy().astype(np.float32)
