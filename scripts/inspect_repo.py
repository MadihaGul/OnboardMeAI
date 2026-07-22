import tempfile, subprocess, os, shutil, json
import sys

def inspect(url):
    try:
        tmp = tempfile.mkdtemp(prefix='repo_')
        subprocess.run(['git','clone','--depth','1',url,tmp], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        readme = None
        for name in ('README.md','README.rst','README.txt','README'):
            p = os.path.join(tmp, name)
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    readme = f.read()
                break
        ext_counts = {}
        top_files = []
        for root, dirs, files in os.walk(tmp):
            for fn in files:
                top_files.append(os.path.relpath(os.path.join(root,fn), tmp))
                _, e = os.path.splitext(fn)
                if e:
                    ext_counts[e.lower()] = ext_counts.get(e.lower(),0)+1
        primary_lang = 'unknown'
        if ext_counts.get('.py',0) > max(ext_counts.get('.js',0), ext_counts.get('.java',0)):
            primary_lang = 'python'
        elif ext_counts.get('.js',0) or ext_counts.get('.ts',0):
            primary_lang = 'javascript/typescript'
        elif ext_counts.get('.java',0):
            primary_lang = 'java'
        summary = ''
        if readme:
            paragraphs = [p.strip() for p in readme.split('\n\n') if p.strip()]
            if paragraphs:
                summary = paragraphs[0][:2000]
        result = {
            'repo': url,
            'primary_language': primary_lang,
            'readme_excerpt': summary,
            'top_files_sample': top_files[:40]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except subprocess.CalledProcessError as e:
        print(json.dumps({'error':'git clone failed','stderr': e.stderr.decode('utf-8','ignore')}))
    finally:
        try:
            if 'tmp' in locals() and os.path.exists(tmp):
                shutil.rmtree(tmp)
        except Exception:
            pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: inspect_repo.py <repo_url>')
        sys.exit(1)
    inspect(sys.argv[1])
