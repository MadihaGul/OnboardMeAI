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
                    chunk_text_value = f"CONFIGURATION FILE: {rel}. Summary: {package_summary}"
                    texts.append(chunk_text_value)
                    metadatas.append({
                        'path': rel,
                        'chunk': 0,
                        'text': chunk_text_value,
                        'type': 'package_summary'
                    })
                else:
                    for i, c in enumerate(chunk_text(content)):
                        chunk_text_value = f"CONFIGURATION FILE: {rel}. {c}"
                        texts.append(chunk_text_value)
                        metadatas.append({'path': rel, 'chunk': i, 'text': chunk_text_value, 'type': 'doc_chunk'})
                continue

            if name == 'package-lock.json' or name == 'package-lock':
                summary = summarize_package_lock(content)
                if summary:
                    chunk_text_value = f"CONFIGURATION FILE: {rel}. Summary: {summary}"
                    texts.append(chunk_text_value)
                    metadatas.append({
                        'path': rel,
                        'chunk': 0,
                        'text': chunk_text_value,
                        'type': 'package_lock_summary'
                    })
                    continue

            ext = os.path.splitext(fp)[1].lower()
            code_extensions = {
                '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte',
                '.java', '.kt', '.kts', '.go', '.rs', '.rb', '.php', '.swift', '.scala',
                '.c', '.cpp', '.cc', '.h', '.hpp', '.m', '.mm', '.dart', '.sh', '.bash', '.ps1', '.sql'
            }
            if ext in code_extensions:
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

                code_header = f"CODE FILE: {rel}. {role if role else 'Implementation source code.'}"
                preview = code_preview(content, max_lines=80)
                preview_text = f"{code_header}\n{preview}"
                texts.append(preview_text)
                metadatas.append({
                    'path': rel,
                    'chunk': 0,
                    'text': preview_text,
                    'type': 'code_preview'
                })
                for i, c in enumerate(chunk_text(content, chunk_size=1200, overlap=200)):
                    chunk_text_value = f"{code_header}\n{c}"
                    texts.append(chunk_text_value)
                    metadatas.append({
                        'path': rel,
                        'chunk': i + 1,
                        'text': chunk_text_value,
                        'type': 'code_chunk'
                    })
                continue

            chunks = chunk_text(content)
            for i, c in enumerate(chunks):
                chunk_text_value = f"DOCUMENTATION FILE: {rel}.\n{c}"
                texts.append(chunk_text_value)
                metadatas.append({
                    'path': rel,
                    'chunk': i,
                    'text': chunk_text_value,
                    'type': 'doc_chunk'
                })

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
