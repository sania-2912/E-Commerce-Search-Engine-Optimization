"""
Incremental Indexing Pipeline for Mobile Phones Catalog Addition (+200 Mobiles).
Processes:
  Phase A: Qwen2-VL-2B AI Image Captioning (throttled for thermal safety)
  Phase B: Qwen2.5-0.5B Text Keyword Normalization
  Phase C: SQLite Database Append & Master Checkpoint Update
  Phase D: BGE-Large Dense Embedding & FAISS Update
  Phase E: CLIP Image Embedding & In-Memory Matrix Update
"""
import os
import gc
import json
import time
import sqlite3
from pathlib import Path
from PIL import Image

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import (
    AutoProcessor,
    AutoTokenizer,
    AutoModel,
    AutoModelForCausalLM,
    Qwen2VLForConditionalGeneration,
    CLIPModel,
    CLIPProcessor,
)
from qwen_vl_utils import process_vision_info
import faiss

ROOT = Path(__file__).resolve().parents[2]
NEW_CSV_PATH = ROOT / "data" / "processed" / "new_mobiles_200.csv"
CAPTIONS_CHECKPOINT = ROOT / "data" / "processed" / "new_mobiles_captions.json"
NORMALIZED_CHECKPOINT = ROOT / "data" / "processed" / "new_mobiles_normalized.json"
DB_PATH = ROOT / "data" / "processed" / "products.db"
FAISS_DIR = ROOT / "data" / "processed" / "faiss"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def clean_gpu():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# ==============================================================================
# PHASE A: QWEN2-VL-2B IMAGE CAPTIONING
# ==============================================================================
def run_phase_a():
    print("\n" + "=" * 80)
    print("PHASE A: AI Image Captioning with Qwen2-VL-2B (Mobile Phones)")
    print("=" * 80)

    df = pd.read_csv(NEW_CSV_PATH)
    total_items = len(df)

    captions = {}
    if CAPTIONS_CHECKPOINT.exists():
        try:
            with open(CAPTIONS_CHECKPOINT, "r", encoding="utf-8") as f:
                captions = json.load(f)
            print(f"Loaded existing checkpoint: {len(captions)}/{total_items} already captioned.")
        except Exception:
            captions = {}

    pending_df = df[~df["pid"].isin(captions.keys())]
    if len(pending_df) == 0:
        print("All 200 mobile images already captioned! Skipping Phase A.")
        return captions

    print(f"Loading Qwen2-VL-2B on {DEVICE}...")
    model_name = "Qwen/Qwen2-VL-2B-Instruct"
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="cuda:0" if DEVICE == "cuda" else None,
        local_files_only=True,
    )
    processor = AutoProcessor.from_pretrained(model_name, local_files_only=True)
    if DEVICE == "cpu":
        model.to(DEVICE)
    model.eval()

    prompt = (
        "You are a professional e-commerce product image caption generator. "
        "Describe the product in ONE clear, short sentence. "
        "Include ONLY: smartphone brand, model name, color, and key visible features "
        "(such as camera layout, screen, finish, or foldable design). "
        "Do NOT guess or infer. Describe only what is visible."
    )

    t0 = time.time()
    count = 0

    for idx, row in pending_df.iterrows():
        pid = row["pid"]
        img_path = ROOT / "data" / "images" / f"{pid}.jpg"
        if not img_path.exists():
            print(f"Warning: image not found {img_path}")
            continue

        try:
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": str(img_path),
                        "min_pixels": 256 * 28 * 28,
                        "max_pixels": 512 * 28 * 28,
                    },
                    {"type": "text", "text": prompt},
                ],
            }]
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(
                text=[text], images=image_inputs, videos=video_inputs,
                padding=True, return_tensors="pt"
            ).to(DEVICE)

            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=96)
            trimmed = [o[len(i):] for i, o in zip(inputs.input_ids, out)]
            caption = processor.batch_decode(
                trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0].strip()
            captions[pid] = caption
        except Exception as e:
            print(f"Error captioning {pid}: {e}")
            captions[pid] = f"{row['brand']} {row['product_name']} smartphone"

        time.sleep(1.0)
        count += 1
        if count % 10 == 0 or count == len(pending_df):
            with open(CAPTIONS_CHECKPOINT, "w", encoding="utf-8") as f:
                json.dump(captions, f, indent=2, ensure_ascii=False)
            elapsed = time.time() - t0
            rate = count / max(elapsed, 0.001)
            eta_mins = (len(pending_df) - count) / max(rate, 0.001) / 60
            print(f"  [Captioning] {len(captions)}/{total_items} done ({rate:.2f} img/s, ETA: {eta_mins:.1f}m)")

    # Unload model
    del model
    del processor
    clean_gpu()
    print("Phase A Completed! Qwen2-VL unloaded from GPU.")
    return captions

# ==============================================================================
# PHASE B: QWEN2.5-0.5B KEYWORD NORMALIZATION
# ==============================================================================
def run_phase_b(captions):
    print("\n" + "=" * 80)
    print("PHASE B: Text Keyword Normalization with Qwen2.5-0.5B (Mobile Phones)")
    print("=" * 80)

    df = pd.read_csv(NEW_CSV_PATH)
    total_items = len(df)

    normalized = {}
    if NORMALIZED_CHECKPOINT.exists():
        try:
            with open(NORMALIZED_CHECKPOINT, "r", encoding="utf-8") as f:
                normalized = json.load(f)
            print(f"Loaded existing checkpoint: {len(normalized)}/{total_items} already normalized.")
        except Exception:
            normalized = {}

    pending_pids = [pid for pid in df["pid"] if pid not in normalized]
    if len(pending_pids) == 0:
        print("All 200 items already normalized! Skipping Phase B.")
        return normalized

    print(f"Loading Qwen2.5-0.5B on {DEVICE}...")
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="cuda:0" if DEVICE == "cuda" else None,
        local_files_only=True,
    )
    if DEVICE == "cpu":
        model.to(DEVICE)
    model.eval()

    system_prompt = (
        "You are an e-commerce product text normalization model. "
        "Extract ONLY essential product keywords from the input. "
        "Rules: "
        "1. Extract product type (smartphone, mobile phone, phone). "
        "2. Extract brand and model name (e.g. Apple iPhone 15 Pro, Samsung Galaxy S23 Ultra, OnePlus 12). "
        "3. Extract colors, camera specs, and design features if mentioned. "
        "4. Do NOT guess or add information. "
        "5. Output ONLY keywords separated by ' | '. "
        "6. Keep output minimal and consistent. "
        "Example Input: A natural titanium Apple iPhone 15 Pro smartphone with triple camera system. "
        "Example Output: Apple | iPhone 15 Pro | natural titanium | triple camera | smartphone"
    )

    t0 = time.time()
    count = 0

    for pid in pending_pids:
        raw_cap = captions.get(pid, "")
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract product keywords from: {raw_cap}\n\nKeywords:"},
            ]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer([text], return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                out = model.generate(
                    **inputs, max_new_tokens=48, do_sample=False, repetition_penalty=1.2
                )
            trimmed = [o[len(i):] for i, o in zip(inputs.input_ids, out)]
            norm_text = tokenizer.batch_decode(trimmed, skip_special_tokens=True)[0].strip()
            norm_text = norm_text.replace("\n", " ").strip()
            normalized[pid] = norm_text
        except Exception as e:
            print(f"Error normalizing {pid}: {e}")
            normalized[pid] = raw_cap

        time.sleep(0.2)
        count += 1
        if count % 25 == 0 or count == len(pending_pids):
            with open(NORMALIZED_CHECKPOINT, "w", encoding="utf-8") as f:
                json.dump(normalized, f, indent=2, ensure_ascii=False)
            elapsed = time.time() - t0
            rate = count / max(elapsed, 0.001)
            eta_mins = (len(pending_pids) - count) / max(rate, 0.001) / 60
            print(f"  [Normalizing] {len(normalized)}/{total_items} done ({rate:.1f} items/s, ETA: {eta_mins:.1f}m)")

    # Unload model
    del model
    del tokenizer
    clean_gpu()
    print("Phase B Completed! Qwen2.5-0.5B unloaded from GPU.")
    return normalized

# ==============================================================================
# PHASE C: SQLITE & METADATA APPEND
# ==============================================================================
def run_phase_c(captions, normalized):
    print("\n" + "=" * 80)
    print("PHASE C: Appending Mobiles to SQLite Database & Master Checkpoints")
    print("=" * 80)

    df = pd.read_csv(NEW_CSV_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT pid FROM products")
    existing_db_pids = set(row[0] for row in cursor.fetchall())
    print(f"Current rows in products.db: {len(existing_db_pids)}")

    new_inserts = 0
    now_ts = time.strftime("%Y-%m-%d %H:%M:%S")

    for _, row in df.iterrows():
        pid = row["pid"]
        if pid in existing_db_pids:
            continue

        raw_cap = captions.get(pid, "")
        norm_text = normalized.get(pid, raw_cap)
        retail_p = float(row["retail_price"]) if pd.notna(row.get("retail_price")) else None
        disc_p = float(row["discounted_price"]) if pd.notna(row.get("discounted_price")) else None
        brand = str(row["brand"]) if pd.notna(row.get("brand")) else "Unknown"

        cursor.execute("""
            INSERT INTO products (pid, image_path, product_name, main_category, brand, retail_price, discounted_price, raw_caption, norm_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid,
            str(ROOT / "data" / "images" / f"{pid}.jpg"),
            str(row["product_name"]),
            str(row["main_category"]),
            brand,
            retail_p,
            disc_p,
            raw_cap,
            norm_text,
            now_ts,
        ))
        new_inserts += 1

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM products")
    total_db_rows = cursor.fetchone()[0]
    conn.close()

    print(f"Inserted {new_inserts} new rows! Total rows in products.db now: {total_db_rows}")

    # Merge master checkpoints
    master_cap_path = ROOT / "data" / "processed" / "captions_checkpoint.json"
    if master_cap_path.exists():
        try:
            with open(master_cap_path, "r", encoding="utf-8") as f:
                master_cap = json.load(f)
            master_cap.update(captions)
            with open(master_cap_path, "w", encoding="utf-8") as f:
                json.dump(master_cap, f, indent=2, ensure_ascii=False)
            print(f"Updated master captions_checkpoint.json: {len(master_cap)} total entries.")
        except Exception as e:
            print(f"Warning merging captions: {e}")

    master_norm_path = ROOT / "data" / "processed" / "normalized_checkpoint.json"
    if master_norm_path.exists():
        try:
            with open(master_norm_path, "r", encoding="utf-8") as f:
                master_norm = json.load(f)
            master_norm.update(normalized)
            with open(master_norm_path, "w", encoding="utf-8") as f:
                json.dump(master_norm, f, indent=2, ensure_ascii=False)
            print(f"Updated master normalized_checkpoint.json: {len(master_norm)} total entries.")
        except Exception as e:
            print(f"Warning merging normalized: {e}")

    print("Phase C Completed!")

# ==============================================================================
# PHASE D: BGE-LARGE DENSE EMBEDDING & FAISS UPDATE
# ==============================================================================
def run_phase_d():
    print("\n" + "=" * 80)
    print("PHASE D: Encoding Normalized Texts with BGE-Large & Updating FAISS")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, pid, norm_text FROM products ORDER BY id ASC")
    all_rows = cursor.fetchall()
    conn.close()

    faiss_index_path = FAISS_DIR / "bge_index.faiss"
    faiss_ids_path = FAISS_DIR / "bge_index_ids.npy"

    existing_index = faiss.read_index(str(faiss_index_path))
    existing_ids = np.load(str(faiss_ids_path)).tolist()
    print(f"Current FAISS index has {existing_index.ntotal} vectors, {len(existing_ids)} IDs.")

    existing_id_set = set(existing_ids)
    pending_rows = [r for r in all_rows if r[0] not in existing_id_set]

    if len(pending_rows) == 0:
        print("FAISS index is already up to date! Skipping Phase D.")
        return

    print(f"Found {len(pending_rows)} new items to encode and add to FAISS.")
    print(f"Loading BGE-Large-en-v1.5 on {DEVICE}...")

    model_name = "BAAI/bge-large-en-v1.5"
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    model = AutoModel.from_pretrained(model_name, local_files_only=True).to(DEVICE)
    model.eval()

    batch_size = 32
    new_embeddings = []
    new_ids = []

    for i in range(0, len(pending_rows), batch_size):
        batch = pending_rows[i:i + batch_size]
        texts = [str(r[2]) if r[2] else "" for r in batch]
        ids = [r[0] for r in batch]

        encoded = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            output = model(**encoded)
            embs = output[0][:, 0]  # CLS token
            embs = F.normalize(embs, p=2, dim=1)
            new_embeddings.append(embs.cpu().numpy().astype(np.float32))
            new_ids.extend(ids)

        time.sleep(0.5)
        print(f"  [BGE Embedding] {min(i + batch_size, len(pending_rows))}/{len(pending_rows)} encoded...")

    new_embs_array = np.vstack(new_embeddings)  # Shape: (N, 1024)
    existing_index.add(new_embs_array)
    all_ids_updated = np.array(existing_ids + new_ids)

    faiss.write_index(existing_index, str(faiss_index_path))
    np.save(str(faiss_ids_path), all_ids_updated)

    del model
    del tokenizer
    clean_gpu()

    print(f"FAISS index updated: {existing_index.ntotal} total vectors saved to {faiss_index_path}!")
    print(f"Updated IDs array ({len(all_ids_updated)} items) saved to {faiss_ids_path}!")
    print("Phase D Completed!")

# ==============================================================================
# PHASE E: CLIP IMAGE EMBEDDINGS & IN-MEMORY RAM MATRIX UPDATE
# ==============================================================================
def run_phase_e():
    print("\n" + "=" * 80)
    print("PHASE E: Computing CLIP Image Embeddings & Updating RAM Matrix")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, pid, image_path FROM products ORDER BY id ASC")
    all_rows = cursor.fetchall()
    conn.close()

    emb_path = FAISS_DIR / "clip_image_embeddings.npy"
    pids_path = FAISS_DIR / "clip_image_pids.npy"
    ids_path = FAISS_DIR / "clip_image_db_ids.npy"

    existing_embs = np.load(str(emb_path))
    existing_pids = np.load(str(pids_path)).tolist()
    existing_ids = np.load(str(ids_path)).tolist()
    print(f"Current CLIP matrix: {existing_embs.shape}, {len(existing_pids)} PIDs.")

    existing_pid_set = set(existing_pids)
    pending_rows = [r for r in all_rows if r[1] not in existing_pid_set]

    if len(pending_rows) == 0:
        print("CLIP matrix is already up to date! Skipping Phase E.")
        return

    print(f"Found {len(pending_rows)} new images to encode for CLIP.")
    print(f"Loading CLIP ViT-B/32 on {DEVICE}...")

    model_name = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_name, local_files_only=True)
    model = CLIPModel.from_pretrained(model_name, local_files_only=True).to(DEVICE)
    model.eval()

    batch_size = 32
    new_embs_list = []
    new_pids_list = []
    new_ids_list = []

    for i in range(0, len(pending_rows), batch_size):
        batch = pending_rows[i:i + batch_size]
        images = []
        valid_batch_pids = []
        valid_batch_ids = []

        for r in batch:
            img_p = ROOT / "data" / "images" / f"{r[1]}.jpg"
            try:
                img = Image.open(img_p).convert("RGB")
                images.append(img)
                valid_batch_pids.append(r[1])
                valid_batch_ids.append(r[0])
            except Exception as e:
                print(f"Warning opening {img_p}: {e}")

        if images:
            inp = processor(images=images, return_tensors="pt")
            pv = inp["pixel_values"].to(DEVICE)
            with torch.no_grad():
                vis = model.vision_model(pixel_values=pv)
                embs = model.visual_projection(vis.pooler_output)
                norm = torch.norm(embs, p=2, dim=-1, keepdim=True)
                embs = embs / norm.clamp(min=1e-10)
                new_embs_list.append(embs.cpu().numpy().astype(np.float32))
                new_pids_list.extend(valid_batch_pids)
                new_ids_list.extend(valid_batch_ids)

        time.sleep(0.5)
        print(f"  [CLIP Encoding] {min(i + batch_size, len(pending_rows))}/{len(pending_rows)} images processed...")

    new_embs_array = np.vstack(new_embs_list)
    final_embs = np.vstack([existing_embs, new_embs_array])
    final_pids = np.array(existing_pids + new_pids_list)
    final_ids = np.array(existing_ids + new_ids_list)

    np.save(str(emb_path), final_embs)
    np.save(str(pids_path), final_pids)
    np.save(str(ids_path), final_ids)

    del model
    del processor
    clean_gpu()

    print(f"\nSUCCESS: Updated CLIP In-Memory Matrix!")
    print(f"New Matrix Shape: {final_embs.shape} (512-dim, L2-normalized)")
    print(f"Phase E Completed!")

# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def main():
    print("*" * 80)
    print("STARTING INCREMENTAL CATALOG EXPANSION: 200 LATEST SMARTPHONES")
    print("*" * 80)

    start_time = time.time()

    # Step 2: AI Captioning (Phase A)
    captions = run_phase_a()

    # Step 3: Keyword Normalization (Phase B)
    normalized = run_phase_b(captions)

    # Step 4a: SQLite Database Update (Phase C)
    run_phase_c(captions, normalized)

    # Step 4b: BGE-Large FAISS Dense Retrieval Update (Phase D)
    run_phase_d()

    # Step 4c: CLIP Image Reranking Embeddings Update (Phase E)
    run_phase_e()

    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"ALL PHASES COMPLETED SUCCESSFULLY IN {total_time / 60:.2f} MINUTES!")
    print("=" * 80)

if __name__ == "__main__":
    main()
