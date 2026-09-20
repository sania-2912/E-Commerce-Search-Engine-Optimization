"""Query intent parsing and normalization using Qwen2.5-0.5B LoRA"""
import re
import json
import logging
from typing import Dict, Optional
import Retrieval_Pipeline.models.model_loader as ml

logger = logging.getLogger(__name__)

NORM_SYSTEM_PROMPT = (
    "You are an e-commerce query understanding model. "
    "Given a user search query, extract essential product keywords and attributes. "
    "Output valid JSON ONLY. Schema:\n"
    '{"semantic_query": string, "category_hint": string|null, "color": string|null, '
    '"gender": "men"|"women"|"unisex"|null, "brand": string|null, '
    '"min_price": number|null, "max_price": number|null, "intent_summary": string}'
)

def parse_text_query(query: str) -> dict:
    clean_q = query.strip()
    if ml.qwen_norm_model is None or ml.qwen_norm_tokenizer is None:
        return {
            "original_query": clean_q,
            "semantic_query": clean_q,
            "category_hint": None,
            "color": None,
            "gender": None,
            "brand": None,
            "min_price": None,
            "max_price": None,
            "attributes": [],
            "intent_summary": clean_q,
        }

    msgs = [
        {"role": "system", "content": NORM_SYSTEM_PROMPT},
        {"role": "user", "content": f"Query: {clean_q}\nJSON:"},
    ]
    try:
        text = ml.qwen_norm_tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = ml.qwen_norm_tokenizer([text], return_tensors="pt").to(ml.DEVICE)
        with ml.torch.no_grad():
            out = ml.qwen_norm_model.generate(**inputs, max_new_tokens=96, do_sample=False, temperature=0.0)
        raw_output = ml.qwen_norm_tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        
        raw_clean = re.sub(r"```(?:json)?\s*", "", raw_output).strip()
        match = re.search(r"\{.*\}", raw_clean, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return {
                "original_query": clean_q,
                "semantic_query": parsed.get("semantic_query", clean_q),
                "category_hint": parsed.get("category_hint"),
                "color": parsed.get("color"),
                "gender": parsed.get("gender"),
                "brand": parsed.get("brand"),
                "min_price": parsed.get("min_price"),
                "max_price": parsed.get("max_price"),
                "attributes": parsed.get("attributes", []),
                "intent_summary": parsed.get("intent_summary", clean_q),
            }
    except Exception as e:
        logger.warning(f"Qwen norm parsing fallback ({e})")

    return {
        "original_query": clean_q,
        "semantic_query": clean_q,
        "category_hint": None,
        "color": None,
        "gender": None,
        "brand": None,
        "min_price": None,
        "max_price": None,
        "attributes": [],
        "intent_summary": clean_q,
    }
