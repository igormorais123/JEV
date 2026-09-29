"""Run installed upstream tools with shared Jev transport and no upstream API secrets."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from integracao.harness.ponte import Bridge
SOURCES=ROOT/'research/sources'


def command(tool, args):
    d=SOURCES/tool
    py=str(d/'.venv/Scripts/python.exe')
    if tool=='jev-cli': return ['node',str(d/'dist/cli.js'),*args,'--provider','typesafe']
    if tool=='jev-review': return ['node',str(d/'src/cli/review-changes.ts'),*args]
    if tool=='Janus':
        if args[:1]!=['measure'] or not any(x in args for x in ('--task','--replay','--help')):
            raise ValueError('Janus: usar measure --task banking77|wos ou --replay; backend pago direto desativado')
        return [str(d/'.venv/Scripts/janus.exe'),*args]
    if tool=='jevcal':
        if not args or args[0] not in ('demo','lint','--help'):
            raise ValueError('jevcal: demo, lint ou --help; backends pagos diretos desativados')
        return [str(d/'.venv/Scripts/jevcal.exe'),*args]
    if tool=='every':
        code='''import os
import every.judge as j
j.MAX_ATTEMPTS = 1
class SharedJudge(j.Judge):
    def __init__(self, api_key, **kwargs):
        kwargs["api_url"] = os.environ["TYPESAFE_BASE_URL"] + "/v1/systemone"
        super().__init__(api_key, **kwargs)
j.Judge = SharedJudge
from every.cli import main
raise SystemExit(main())
'''
        return [py,'-c',code,*args]
    if tool=='jevstudio':
        return [sys.executable,str(ROOT/'integracao/harness/studio.py'),*args]
    raise ValueError('Ferramenta nao tem lancador seguro: '+tool)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('tool',choices=['jev-cli','Janus','jevcal','every','jevstudio','jev-review'])
    p.add_argument('args',nargs=argparse.REMAINDER)
    opts=p.parse_args()
    args=opts.args[1:] if opts.args[:1]==['--'] else opts.args
    env={k:v for k,v in os.environ.items() if not any(t in k.upper() for t in ('API_KEY','TOKEN','SECRET','OPENAI','ANTHROPIC','TYPESAFE','OPENROUTER'))}
    env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    with Bridge() as bridge:
        env.update(TYPESAFE_API_KEY=bridge.token,TYPESAFE_BASE_URL=bridge.url.removesuffix('/v1'),JEV_ENDPOINT=bridge.url+'/systemone',JEV_RETRIES='1')
        return subprocess.call(command(opts.tool,args),cwd=SOURCES/opts.tool,env=env)

if __name__=='__main__':
    raise SystemExit(main())
