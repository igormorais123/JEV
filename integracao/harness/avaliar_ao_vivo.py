"""Native CLI smoke test; won't initialize a wallet or pay without existing accounting."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from integracao.apoio import status

def main():
    readiness = status()
    if not readiness.get('paid_ready'):
        print(json.dumps({'status':'blocked','reason':readiness.get('reason'),'sent':False}))
        return 3
    corpus=json.loads((ROOT/'integracao/harness/corpus.json').read_text(encoding='utf-8'))
    results=[]
    for kind in ('classification','evidence'):
        for case in corpus[kind]:
            args=(['classify',case['text'],'--labels','bug:Falha de software,melhoria:Pedido de nova funcionalidade,outro:Outro assunto'] if kind=='classification' else ['verify',case['claim'],'--evidence',case['source'],'--fail-on','none'])
            cmd=[sys.executable,str(ROOT/'integracao/harness/usar_ferramenta.py'),'jev-cli','--',*args,'--json']
            p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=45)
            row={'id':case['id'],'expected':case['expected'],'exit':p.returncode,'evidence':'live_component','origin':corpus['origin']}
            if p.returncode:
                row['status']='transport_or_configuration_error'
                results.append(row)
                break  # Do not retry an uncertain paid attempt.
            parsed=json.loads(p.stdout)
            row['actual']=parsed['label'] if kind=='classification' else parsed['results'][0]['verdict']
            row['correct']=row['actual']==case['expected']
            results.append(row)
        if results and results[-1].get('status'): break
    target=ROOT/'runs/harness-20260921/live.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'results':results,'file':str(target)},ensure_ascii=False))
    return int(any(not r.get('correct') for r in results))

if __name__=='__main__':raise SystemExit(main())
