import os
import json
import pickle
from typing import List, Tuple
import numpy as np

from sentence_transformers import SentenceTransformer
import faiss

MODEL_NAME = "all-MiniLM-L6-v2"

class VectorStore:
    def __init__(self, path: str, model_name: str = MODEL_NAME):
        self.path = path
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.metadatas = []

    def _create_index(self, dim: int):
        self.index = faiss.IndexFlatL2(dim)

    def add(self, texts: List[str], metadatas: List[dict]):
        embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        if self.index is None:
            self._create_index(embs.shape[1])
        self.index.add(embs.astype('float32'))
        self.metadatas.extend(metadatas)

    def search(self, query: str, k: int = 4) -> List[Tuple[dict, float]]:
        qv = self.model.encode([query], convert_to_numpy=True)
        D, I = self.index.search(qv.astype('float32'), k)
        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx < len(self.metadatas):
                results.append((self.metadatas[idx], float(dist)))
        return results

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        faiss.write_index(self.index, self.path + '.index')
        with open(self.path + '.meta', 'wb') as f:
            pickle.dump(self.metadatas, f)

    def load(self):
        if os.path.exists(self.path + '.index') and os.path.exists(self.path + '.meta'):
            self.index = faiss.read_index(self.path + '.index')
            with open(self.path + '.meta', 'rb') as f:
                self.metadatas = pickle.load(f)
            return True
        return False
