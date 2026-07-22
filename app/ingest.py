import os
import shutil
import tempfile
from git import Repo
from typing import List

from app.utils import list_text_files, read_file, chunk_text
from app.vectorstore import VectorStore

def clone_repo(url: str, branch: str = None) -> str:
    tmp = tempfile.mkdtemp(prefix='repo_')
    Repo.clone_from(url, tmp, branch=branch) if branch else Repo.clone_from(url, tmp)
    return tmp

def ingest_repo(repo_url: str, repo_name: str, data_dir: str = './data') -> str:
    repo_path = clone_repo(repo_url)
    try:
        vs_path = os.path.join(data_dir, repo_name)
        vs = VectorStore(vs_path)

        texts = []
        metadatas = []
        for fp in list_text_files(repo_path):
            rel = os.path.relpath(fp, repo_path)
            content = read_file(fp)
            if not content:
                continue
            chunks = chunk_text(content)
            for i, c in enumerate(chunks):
                texts.append(c)
                metadatas.append({'path': rel, 'chunk': i, 'text': c})

        if texts:
            vs.add(texts, metadatas)
            vs.save()

        return vs_path
    finally:
        try:
            shutil.rmtree(repo_path)
        except Exception:
            pass
