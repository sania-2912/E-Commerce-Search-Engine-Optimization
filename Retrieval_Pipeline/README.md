# 🔍 Online Retrieval Pipeline

High-speed enterprise multimodal retrieval pipeline combining dense semantic recall with in-memory cross-modal visual reranking.

---

## 🏗️ Architecture

```text
Retrieval_Pipeline/
├── config/
│   └── retrieval.yaml            # Retrieval parameters and model paths
├── logic/
│   ├── query_normalization.py    # Query entity parsing (Qwen2.5-0.5B LoRA)
│   ├── query_embedding.py        # Dense text embedding (BGE-Large)
│   └── reranking.py              # In-memory visual reranking (CLIP ViT-B/32)
├── models/
│   ├── clip_reranking_model.py   # CLIP model wrapper
│   ├── model_loader.py           # Unified GPU model loader
│   └── schemas.py                # Request & response data schemas
├── storage/
│   ├── faiss_searcher.py         # FAISS vector similarity search
│   └── sqlite_reader.py          # SQLite product metadata reader
├── utils/
│   └── logger.py                 # Logging utility
├── retrieval_pipeline.py         # Main unified search service
├── run_test.py                   # Standalone CLI test script
└── README.md
```

## 🚀 Execution

```bash
python Retrieval_Pipeline/run_test.py
```
