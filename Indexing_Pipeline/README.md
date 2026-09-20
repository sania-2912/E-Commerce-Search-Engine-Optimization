# 🔍 Offline Indexing Pipeline

Processes e-commerce catalog images and metadata through AI models to construct searchable vector indexes and metadata tables.

---

## 🏗️ Architecture

```text
Indexing_Pipeline/
├── config/
│   └── indexing.yaml             # Model, data, and database configuration
├── data/
│   ├── dataset_loader.py         # Batch image loader and validator
│   └── image_registry.py         # Image ID to path registry
├── logic/
│   ├── caption_generator.py      # Vision-language captioning
│   ├── text_normalizer.py        # Entity & keyword normalization
│   └── embedding_generator.py    # 1024-dim dense text embedding
├── models/
│   ├── caption_model.py          # Qwen2-VL-2B-Instruct wrapper
│   ├── normalization_model.py    # Qwen2.5-0.5B-Instruct wrapper
│   └── embedding_model.py        # BAAI/bge-large-en-v1.5 wrapper
├── storage/
│   ├── faiss_writer.py           # FAISS IndexFlatIP indexer
│   ├── sqlite_writer.py          # SQLite products.db writer
│   ├── postgres_writer.py        # Optional PostgreSQL writer
│   └── schema.sql                # SQL table schema
├── utils/
│   ├── batching.py               # Dynamic batching generator
│   ├── logger.py                 # Structured logging
│   └── validation.py             # Image validation
├── scripts/
│   ├── build_clean_smartphones_catalog.py
│   ├── expand_to_200.py
│   └── apply_unique_mobiles_pipeline.py
├── run_indexing.py               # Main pipeline runner
└── README.md
```

## 🚀 Execution

```bash
python Indexing_Pipeline/run_indexing.py
```
