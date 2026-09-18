import concurrent.futures, subprocess, pathlib, json
repos=['Nasrallah-AL/jev-cli','superagents-lab/jev-search','FirasSX914/Janus','DevMortimer/pi-warden','browser-use/jev-ultrafast','abhixhek/jevcal','anessbelbati/jev-rerank-bench','typesafe-ai/system-one-adapter-python','devagrawal09/jev-review','sufianetaouil/every','AbdelStark/heist-one','TheoLeeCJ/openjev','AbdelStark/awesome-typesafe','typesafe-ai/skills','Anil-matcha/awesome-jev-by-typesafe','redrossa/pi-model-router','hellogumbo/should-ai-kill-us-all','Infrawrench/Jeeves']
root=pathlib.Path('research/sources')
def fetch(repo):
 p=root/repo.split('/')[-1]
 r=subprocess.run(['git','clone','--depth','1','https://github.com/'+repo+'.git',str(p)],capture_output=True,text=True)
 if r.returncode: return {'repo':repo,'error':r.stderr}
 sha=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
 return {'repo':repo,'sha':sha,'url':'https://github.com/'+repo,'path':str(p)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: results=list(ex.map(fetch,repos))
pathlib.Path('research/sources-manifest.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
for r in results: print(r['repo'],r.get('sha',r.get('error')))
