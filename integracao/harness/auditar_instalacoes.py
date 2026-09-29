"""Install isolated upstream environments and persist bounded, credential-free checks."""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / 'research/sources'
OUT = ROOT / 'runs/harness-20260921'

def run(name, stage, args, timeout=300):
    env = {k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('API_KEY','TOKEN','SECRET','OPENAI','ANTHROPIC','TYPESAFE','OPENROUTER'))}
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', CI='1')
    start = time.time()
    try:
        p = subprocess.run(args, cwd=SOURCES/name, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
        code, output = p.returncode, p.stdout+p.stderr
    except subprocess.TimeoutExpired as e:
        code, output = 124, str(e.stdout or b'')+'\nTIMEOUT'
    except Exception as e:
        code, output = 125, type(e).__name__+': '+str(e)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/f'{name}-{stage}.log').write_text(output, encoding='utf-8')
    result = {'system':name,'stage':stage,'command':args,'exit':code,'seconds':round(time.time()-start,2),'log':f'{name}-{stage}.log'}
    (OUT/f'{name}-{stage}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result), flush=True)
    return code

def project(name):
    d = SOURCES/name
    run(name,'revision',['git','rev-parse','HEAD'])
    package=d/'package.json'
    if package.exists():
        scripts=json.loads(package.read_text(encoding='utf-8')).get('scripts',{})
        if (d/'pnpm-lock.yaml').exists() and not (d/'package-lock.json').exists():
            cmd=[shutil.which('npx.cmd'),'--yes','pnpm@10']
            install=cmd+['install','--frozen-lockfile','--ignore-scripts']
        else:
            cmd=[shutil.which('npm.cmd')]
            install=cmd+(['ci'] if (d/'package-lock.json').exists() else ['install'])+['--ignore-scripts','--no-audit','--no-fund']
        if run(name,'install',install,600): return
        for stage in ('test','typecheck','build'):
            if stage in scripts:
                run(name,stage,cmd+['run',stage],300)
    elif (d/'pyproject.toml').exists():
        uv=shutil.which('uv')
        if run(name,'venv',[uv,'venv','--python','3.13','.venv'],180): return
        py=str(d/'.venv/Scripts/python.exe')
        extra={'every':'.[dev]','Janus':'.[dev]','jevcal':'.[dev]', 'openjev':'.[test]', 'system-one-adapter-python':'.[openai,anthropic]'}.get(name,'.')
        if name=='jev-rerank-bench':
            install=[uv,'pip','install','--python',py,'requests','python-dotenv','numpy','pytest','bm25s','PyStemmer']
        else:
            install=[uv,'pip','install','--python',py,'-e',extra,'pytest']
            if name=='system-one-adapter-python': install+=['pytest-recording','httpx']
        if run(name,'install',install,600): return
        run(name,'test',[py,'-m','pytest','-q','--tb=short'],300)

if __name__=='__main__':
    names=['jev-cli','jev-search','Janus','pi-warden','jev-ultrafast','jevcal','jev-rerank-bench','system-one-adapter-python','jev-review','every','heist-one','openjev','pi-model-router','should-ai-kill-us-all']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(project,names))
