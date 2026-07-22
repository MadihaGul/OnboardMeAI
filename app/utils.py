import os
import re
import json
from typing import List, Optional

def list_text_files(root: str, exts=None):
    if exts is None:
        exts = {'.py', '.md', '.txt', '.json', '.yaml', '.yml', '.rst'}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            _, e = os.path.splitext(fn)
            if e.lower() in exts:
                yield os.path.join(dirpath, fn)

def read_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def extract_imports(content: str) -> List[str]:
    imports = []
    patterns = [
        r"import\s+[^'\"]+[\"']([^\"']+)[\"']",
        r"import\([\"']([^\"']+)[\"']\)",
        r"require\([\"']([^\"']+)[\"']\)",
        r"export\s+[^'\"]+from\s+[\"']([^\"']+)[\"']",
    ]
    for pat in patterns:
        for match in re.findall(pat, content):
            imports.append(match)
    return imports


def resolve_js_import(base_path: str, import_path: str) -> Optional[str]:
    if import_path.startswith('.'):
        root = os.path.dirname(base_path)
        candidate = os.path.normpath(os.path.join(root, import_path))
        extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.json']
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
        for ext in extensions:
            if os.path.isfile(candidate + ext):
                return os.path.abspath(candidate + ext)
        if os.path.isdir(candidate):
            for ext in extensions:
                idx = os.path.join(candidate, 'index' + ext)
                if os.path.isfile(idx):
                    return os.path.abspath(idx)
    return None


def file_role_hint(path: str, content: str) -> str:
    path_lower = path.replace('\\', '/').lower()
    hints = []
    if 'auth' in path_lower or 'login' in path_lower or 'signup' in path_lower:
        hints.append('authentication')
    if 'store' in path_lower or 'zustand' in content.lower():
        hints.append('global state management')
    if 'supabase' in path_lower or 'supabase' in content.lower():
        hints.append('Supabase backend integration')
    if 'router' in path_lower or 'routes' in path_lower or 'navigate' in content.lower():
        hints.append('routing')
    if 'config' in path_lower or 'settings' in path_lower:
        hints.append('configuration')
    if 'component' in path_lower or 'components/' in path_lower:
        hints.append('UI component')
    if 'page' in path_lower or 'modules/' in path_lower:
        hints.append('page or module')
    if 'lib' in path_lower:
        hints.append('utility library')
    if 'api' in path_lower:
        hints.append('API wrapper')
    if not hints:
        return ''
    hints = list(dict.fromkeys(hints))
    return f"This file is likely responsible for {', '.join(hints)}."


def build_architecture_summary(files, import_edges, package_summary: str, readme_excerpt: str) -> str:
    lines = []
    if package_summary:
        lines.append('Package info: ' + package_summary.replace('\n', '; '))
    if readme_excerpt:
        lines.append('README overview: ' + ' '.join(readme_excerpt.split('\n')[:2]))
    if import_edges:
        if len(import_edges) > 0:
            lines.append('Key file relationships:')
            for src, dst in import_edges[:20]:
                lines.append(f'- {src} imports {dst}')
    if files:
        top = ', '.join(sorted([os.path.basename(f) for f in files if len(f) < 40])[:10])
        lines.append('Main files: ' + top)
    return '\n'.join(lines)

def summarize_package_json(content: str) -> str:
    try:
        j = json.loads(content)
    except Exception:
        return ''
    parts = []
    name = j.get('name')
    if name:
        parts.append(f"Project name: {name}")
    desc = j.get('description')
    if desc:
        parts.append(f"Description: {desc}")
    deps = j.get('dependencies', {})
    dev = j.get('devDependencies', {})
    scripts = j.get('scripts', {})
    if deps:
        top = ', '.join(list(deps.keys())[:10])
        parts.append(f"Top dependencies: {top}")
    if dev:
        topd = ', '.join(list(dev.keys())[:10])
        parts.append(f"Top devDependencies: {topd}")
    if scripts:
        parts.append("Scripts: " + ', '.join(scripts.keys()))
    # detect likely frameworks
    fw = []
    tags = ['react','vite','tailwind','typescript','next','express','supabase','zustand']
    for t in tags:
        if t in deps or t in dev or (desc and t in desc.lower()):
            fw.append(t)
    if fw:
        parts.append("Frameworks/tools detected: " + ', '.join(fw))
    return '\n'.join(parts)


def summarize_package_lock(content: str) -> str:
    try:
        j = json.loads(content)
    except Exception:
        return ''
    deps = j.get('dependencies', {})
    if not deps:
        return ''
    top = list(deps.keys())[:20]
    return "Locked dependencies (sample): " + ', '.join(top)


def code_preview(content: str, max_lines: int = 40) -> str:
    lines = content.splitlines()
    preview = '\n'.join(lines[:max_lines])
    return preview