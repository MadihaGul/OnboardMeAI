import os
import shutil
import tempfile
from git import Repo
from typing import List

from app.utils import (
    list_text_files,
    read_file,
    chunk_text,
    summarize_package_json,
    summarize_package_lock,
    code_preview,
    extract_imports,
    resolve_js_import,
    file_role_hint,
    build_architecture_summary,
)
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
        files = []
        import_edges = []
        package_summary = ''
        readme_excerpt = ''

        for fp in list_text_files(repo_path):
            rel = os.path.relpath(fp, repo_path)
            content = read_file(fp)
            if not content:
                continue
            files.append(rel)

            name = os.path.basename(fp).lower()
            if name in {'readme.md', 'readme.txt', 'readme', 'readme.rst'}:
                if not readme_excerpt:
                    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                    if paragraphs:
                        readme_excerpt = paragraphs[0][:1000]

            # Special handling for package.json and package-lock.json to capture intent
            if name == 'package.json':
                package_summary = summarize_package_json(content)
                if package_summary:
                    texts.append(package_summary)
                    metadatas.append({
                        'path': rel,
                        'chunk': 0,
                        'text': package_summary,
                        'type': 'package_summary'
                    })
                else:
                    for i, c in enumerate(chunk_text(content)):
                        texts.append(c)
                        metadatas.append({'path': rel, 'chunk': i, 'text': c})
                continue

            if name == 'package-lock.json' or name == 'package-lock':
                summary = summarize_package_lock(content)
                if summary:
                    texts.append(summary)
                    metadatas.append({
                        'path': rel,
                        'chunk': 0,
                        'text': summary,
                        'type': 'package_lock_summary'
                    })
                    continue

            ext = os.path.splitext(fp)[1].lower()
            if ext in {'.js', '.jsx', '.ts', '.tsx', '.py'}:
                role = file_role_hint(rel, content)
                if role:
                    texts.append(f"{rel}: {role}")
                    metadatas.append({
                        'path': rel,
                        'chunk': 0,
                        'text': role,
                        'type': 'file_role_hint'
                    })

                imports = extract_imports(content)
                for imp in imports:
                    resolved = resolve_js_import(fp, imp)
                    target = os.path.relpath(resolved, repo_path) if resolved else imp
                    import_edges.append((rel, target))

                preview = code_preview(content, max_lines=60)
                texts.append(preview)
                metadatas.append({
                    'path': rel,
                    'chunk': 0,
                    'text': preview,
                    'type': 'code_preview'
                })
                for i, c in enumerate(chunk_text(content, chunk_size=1200, overlap=200)):
                    texts.append(c)
                    metadatas.append({'path': rel, 'chunk': i + 1, 'text': c})
                continue

            chunks = chunk_text(content)
            for i, c in enumerate(chunks):
                texts.append(c)
                metadatas.append({'path': rel, 'chunk': i, 'text': c})

        arch_summary = build_architecture_summary(files, import_edges, package_summary, readme_excerpt)
        if arch_summary:
            texts.append(arch_summary)
            metadatas.append({
                'path': 'ARCH_SUMMARY',
                'chunk': 0,
                'text': arch_summary,
                'type': 'architecture_summary'
            })

        if texts:
            vs.add(texts, metadatas)
            vs.save()

        return vs_path
    finally:
        try:
            shutil.rmtree(repo_path)
        except Exception:
            pass
