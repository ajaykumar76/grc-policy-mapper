"""
Embed every NIST 800-53 control and every policy statement with
all-MiniLM-L6-v2, and save the vectors. No LLM needed here.

Usage:  python src\\02_build_index.py
"""
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

controls = json.load(open("data/processed/controls.json", encoding="utf-8"))
policy = json.load(open("data/sample_policy.json", encoding="utf-8"))["statements"]

model = SentenceTransformer("all-MiniLM-L6-v2")

# Title + statement text. Guidance is left out on purpose (it is long and wordy).
control_texts = [f"{c['title']}. {c['statement']}" for c in controls]
policy_texts = [p["text"] for p in policy]

C = model.encode(control_texts, normalize_embeddings=True, show_progress_bar=True)
P = model.encode(policy_texts, normalize_embeddings=True, show_progress_bar=False)

Path("data/processed").mkdir(parents=True, exist_ok=True)
np.save("data/processed/control_vecs.npy", C)
np.save("data/processed/policy_vecs.npy", P)
print(f"Embedded {len(controls)} controls and {len(policy)} policy statements")
