"""
Apply Unique Mobiles Pipeline:
1. Replaces the 200 duplicated items in products.db with 200 genuinely unique smartphone products.
2. Generates rich e-commerce captions and normalized search keywords.
3. Encodes normalized texts with BGE-Large (1024-dim) and updates FAISS index.
4. Encodes 200 unique phone images with CLIP ViT-B/32 (512-dim) and updates CLIP RAM matrix.
"""
import os
import gc
import re
import time
import sqlite3
from pathlib import Path
from PIL import Image

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import (
    AutoTokenizer,
    AutoModel,
    CLIPModel,
    CLIPProcessor,
)
import faiss

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "processed" / "new_mobiles_200.csv"
DB_PATH = ROOT / "data" / "processed" / "products.db"
FAISS_DIR = ROOT / "data" / "processed" / "faiss"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def clean_gpu():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def extract_attributes(name, brand):
    # Extract color
    color_match = re.search(r"\(([^,]+),", name)
    color = color_match.group(1).strip() if color_match else "Standard"

    # Extract storage
    storage_match = re.search(r"(\d+\s*(?:GB|TB))", name, re.IGNORECASE)
    storage = storage_match.group(1).strip() if storage_match else "128 GB"

    # Clean model name
    clean_model = re.sub(r"\([^)]*\)", "", name).replace(brand, "").strip()
    clean_model = re.sub(r"\s+", " ", clean_model)

    return clean_model, color, storage

def main():
    print("=" * 80)
    print("APPLYING 200 UNIQUE SMARTPHONES REPLACEMENT PIPELINE")
    print("=" * 80)

    start_time = time.time()

    # Load 200 unique mobiles
    df = pd.read_csv(CSV_PATH)
    assert len(df) == 200, f"Expected 200 rows, got {len(df)}"

    # ──────────────────────────────────────────────────────────────────────────
    # 1. SQLITE UPDATE
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[Step 1/3] Updating SQLite products.db...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Remove old duplicate mobile rows (ids > 6681)
    cursor.execute("DELETE FROM products WHERE id > 6681")
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM products")
    base_count = cursor.fetchone()[0]
    print(f"  Cleaned database back to {base_count} base products.")
    assert base_count == 6681, f"Expected 6681 base rows, got {base_count}"

    now_ts = time.strftime("%Y-%m-%d %H:%M:%S")
    norm_texts = []
    inserted_pids = []

    for i, row in df.iterrows():
        pid = row["pid"]
        brand = str(row["brand"])
        p_name = str(row["product_name"])
        clean_model, color, storage = extract_attributes(p_name, brand)

        raw_caption = (
            f"{brand} {clean_model} smartphone in {color} finish with {storage} storage. "
            f"Features modern touchscreen display, high-resolution camera system, 5G cellular connectivity, and fast charging."
        )

        norm_text = (
            f"{brand} | {clean_model} | {color} | {storage} | smartphone | mobile phone | 5G | camera | flagship"
        )
        norm_texts.append(norm_text)
        inserted_pids.append(pid)

        db_id = 6682 + i
        cursor.execute("""
            INSERT INTO products (id, pid, image_path, product_name, main_category, brand, retail_price, discounted_price, raw_caption, norm_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            db_id,
            pid,
            str(row["image_path"]),
            p_name,
            "Mobiles",
            brand,
            float(row["retail_price"]),
            float(row["discounted_price"]),
            raw_caption,
            norm_text,
            now_ts
        ))

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM products")
    total_db = cursor.fetchone()[0]
    conn.close()

    print(f"  SUCCESS: products.db now has {total_db} total products (exactly 200 new unique mobiles added).")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. BGE-LARGE TEXT EMBEDDING & FAISS UPDATE
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[Step 2/3] Encoding normalized texts with BGE-Large and updating FAISS...")
    faiss_index_path = FAISS_DIR / "bge_index.faiss"
    faiss_ids_path = FAISS_DIR / "bge_index_ids.npy"

    old_index = faiss.read_index(str(faiss_index_path))
    print(f"  Reconstructing 6681 base vectors from FAISS...")
    base_vectors = old_index.reconstruct_n(0, 6681)  # shape: (6681, 1024)

    print(f"  Loading BGE-Large on {DEVICE}...")
    model_name = "BAAI/bge-large-en-v1.5"
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    model = AutoModel.from_pretrained(model_name, local_files_only=True).to(DEVICE)
    model.eval()

    batch_size = 32
    new_embs = []
    for i in range(0, len(norm_texts), batch_size):
        batch_texts = norm_texts[i:i + batch_size]
        encoded = tokenizer(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            out = model(**encoded)
            cls_embs = out[0][:, 0]
            cls_embs = F.normalize(cls_embs, p=2, dim=1)
            new_embs.append(cls_embs.cpu().numpy().astype(np.float32))

    new_embs_array = np.vstack(new_embs)
    del model
    del tokenizer
    clean_gpu()

    # Build fresh 6881 index
    new_index = faiss.IndexFlatIP(1024)
    new_index.add(base_vectors)
    new_index.add(new_embs_array)
    assert new_index.ntotal == 6881, f"Expected 6881 vectors in FAISS, got {new_index.ntotal}"

    all_ids = np.array(list(range(1, 6882)))
    faiss.write_index(new_index, str(faiss_index_path))
    np.save(str(faiss_ids_path), all_ids)
    print(f"  SUCCESS: FAISS index updated to {new_index.ntotal} vectors!")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. CLIP IMAGE EMBEDDING & RAM MATRIX UPDATE
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[Step 3/3] Encoding 200 unique smartphone images with CLIP ViT-B/32...")
    clip_emb_path = FAISS_DIR / "clip_image_embeddings.npy"
    clip_pids_path = FAISS_DIR / "clip_image_pids.npy"
    clip_ids_path = FAISS_DIR / "clip_image_db_ids.npy"

    base_clip_embs = np.load(str(clip_emb_path))[:6681]
    base_clip_pids = np.load(str(clip_pids_path))[:6681].tolist()
    base_clip_ids = np.load(str(clip_ids_path))[:6681].tolist()

    print(f"  Loading CLIP ViT-B/32 on {DEVICE}...")
    clip_model_name = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(clip_model_name, local_files_only=True)
    clip_model = CLIPModel.from_pretrained(clip_model_name, local_files_only=True).to(DEVICE)
    clip_model.eval()

    new_clip_list = []
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i + batch_size]
        images = []
        for _, r in batch_df.iterrows():
            img_p = Path(r["image_path"])
            img = Image.open(img_p).convert("RGB")
            images.append(img)

        inp = processor(images=images, return_tensors="pt")
        pv = inp["pixel_values"].to(DEVICE)
        with torch.no_grad():
            vis = clip_model.vision_model(pixel_values=pv)
            embs = clip_model.visual_projection(vis.pooler_output)
            norm = torch.norm(embs, p=2, dim=-1, keepdim=True)
            embs = embs / norm.clamp(min=1e-10)
            new_clip_list.append(embs.cpu().numpy().astype(np.float32))

    new_clip_array = np.vstack(new_clip_list)
    del clip_model
    del processor
    clean_gpu()

    final_clip_embs = np.vstack([base_clip_embs, new_clip_array])
    final_clip_pids = np.array(base_clip_pids + inserted_pids)
    final_clip_ids = np.array(base_clip_ids + list(range(6682, 6882)))

    assert final_clip_embs.shape == (6881, 512), f"Expected (6881, 512), got {final_clip_embs.shape}"
    assert len(final_clip_pids) == 6881, f"Expected 6881 PIDs, got {len(final_clip_pids)}"

    np.save(str(clip_emb_path), final_clip_embs)
    np.save(str(clip_pids_path), final_clip_pids)
    np.save(str(clip_ids_path), final_clip_ids)

    print(f"  SUCCESS: CLIP matrix updated to {final_clip_embs.shape}!")

    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"ALL 200 UNIQUE SMARTPHONES INDEXED SUCCESSFULLY IN {total_time:.1f} SECONDS!")
    print("=" * 80)

if __name__ == "__main__":
    main()
