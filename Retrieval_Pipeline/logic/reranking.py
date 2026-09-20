"""Visual Cross-Modal Reranking using CLIP in-memory matrix"""
from typing import List
import numpy as np
import torch
import Retrieval_Pipeline.models.model_loader as ml

def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec, axis=1, keepdims=True)
    return vec / np.clip(norm, 1e-10, None)

def encode_text_clip(query: str) -> np.ndarray:
    if ml.clip_model is None or ml.clip_tokenizer is None:
        raise RuntimeError("CLIP model not loaded.")
    inp = ml.clip_tokenizer([query], padding=True, truncation=True, return_tensors="pt").to(ml.DEVICE)
    with torch.no_grad():
        out = ml.clip_model.text_model(**inp)
        emb = ml.clip_model.text_projection(out.pooler_output)
    return _l2_normalize(emb.cpu().float().numpy())

def rerank_with_clip(query: str, candidates: List[dict], top_k: int = 10) -> List[dict]:
    if not candidates or ml.clip_model is None:
        return candidates[:top_k]

    query_emb = encode_text_clip(query)

    # In-Memory precomputed CLIP matrix multiplication (< 3ms)
    if ml.clip_image_embeddings is not None and ml.pid_to_clip_idx:
        valid_candidates = []
        cand_indices = []
        for c in candidates:
            idx = ml.pid_to_clip_idx.get(str(c["pid"]))
            if idx is not None:
                valid_candidates.append(c)
                cand_indices.append(idx)

        if valid_candidates:
            cand_embs = ml.clip_image_embeddings[cand_indices]
            clip_scores = np.dot(cand_embs, query_emb.T).squeeze(-1)
            for c, c_score in zip(valid_candidates, clip_scores):
                c["clip_score"] = float(c_score)
                sem = c.get("semantic_score", 0.5)
                c["final_score"] = round(float(0.35 * sem + 0.65 * c_score), 4)

            reranked = sorted(valid_candidates, key=lambda x: x["final_score"], reverse=True)
            return reranked[:top_k]

    return candidates[:top_k]
