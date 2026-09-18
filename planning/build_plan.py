"""Gera matriz, manifesto e fichas de planejamento; nenhuma chamada de inferencia."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'planning'
SOURCES = {s['repo']: s for s in json.loads((ROOT/'research/sources-manifest.json').read_text(encoding='utf-8'))}


def system(id, name, repo, family, unit, n, calls, llm, question, smoke, deep, baseline, gate, dependencies):
    source = SOURCES[repo]
    return dict(id=id,name=name,repo=repo,url=source['url'],sha=source['sha'],family=family,
                smoke_unit=unit,smoke_units=n,smoke_jev_call_cap=calls,smoke_llm_call_cap=llm,
                question=question,smoke=smoke,deep=deep,baseline=baseline,gate=gate,
                dependencies=dependencies,status='Planejado — não executado',
                evidence_level='Inspeção de código; ensaio do sistema pendente')


systems = [
 system('S01','Jev CLI','Nasrallah-AL/jev-cli','Decisões','cenários',12,12,0,
 'O CLI preserva a decisão, os erros e a cobrança da API sem criar retrabalho?',
 '12 cenários: classificação, rota, verificação, lote, JSON inválido, opções ambíguas, entrada vazia, Unicode, limite de tamanho, timeout, 429 e cache. Contratos/erros primeiro com transporte simulado; até 12 chamadas reais separadas.',
 '840 casos do corpus central, em três tarefas; comparar saída normalizada com resposta original. Conferir todos os erros de transporte e integridade do registro. Reusar respostas para outras ferramentas apenas quando o payload for idêntico.',
 'HTTP mínimo com o mesmo payload; regras locais para a qualidade semântica.',
 'Nenhuma decisão silenciosamente perdida; custo ausente fica desconhecido. Acurácia deve coincidir com a resposta original; diferença é falha do cliente.',
 'Node >=20.12; OPENROUTER_API_KEY; rota Decisions. Inspecionar configuração e usar provedor explícito.'),
 system('S02','Jev Search','superagents-lab/jev-search','Busca','consultas',8,16,0,
 'Reordenar resultados melhora a recuperação de evidência útil por consulta?',
 '8 consultas com 10 resultados congelados cada: resposta, ressalva, sem resposta, duplicatas, data antiga, fonte oficial, homônimo e instrução maliciosa. Testar ranking e deduplicação com busca simulada; até dois formatos por consulta.',
 '60 consultas x 10 candidatos, 20 dev e 40 teste; até dois formatos de ranking. Reaproveitar o banco do Rerank Bench. Depois 12 consultas com busca real, se Search1API estiver disponível e couber na verba.',
 'Ordem original, BM25 e deduplicação determinística com os mesmos candidatos.',
 'Candidato a adoção se nDCG@5 melhora pelo menos 0,05, intervalo pareado favorece ganho e recall de ressalvas não cai mais de 2 pp. Sem evidência suficiente: continuar consultivo.',
 'Node >=22.12, pnpm; TypeSafe direto e Search1API no aplicativo original. Teste com fontes congeladas não comprova a busca externa.'),
 system('S03','Janus','FirasSX914/Janus','Calibração','registros pareados',12,0,0,
 'Uma cascata reduz custo mantendo a qualidade medida em gabarito externo?',
 '12 registros conhecidos de primário e fallback, incluindo erro com confiança alta, discordância, ausência de custo e grupo raro; executar escolha de limiar e conferir à mão. Sem novas inferências.',
 '240 pares Jev/LLM do corpus central, 80 por tarefa: 20 dev, 20 calibração e 40 teste. Limiar escolhido antes do teste. Reusar exatamente os mesmos pares no jevcal.',
 'Sempre Jev, sempre LLM econômico, regra fixa e encaminhar tudo à revisão humana como limite de cobertura.',
 'Economia líquida >=25% e limite inferior da diferença de acurácia acima de -5 pp no teste; amostra insuficiente produz conclusão inconclusiva. Medir erros graves separadamente.',
 'Python/NumPy; obter previsões do fallback, sem tratá-lo como gabarito. A função de medição original precisa de avaliação externa independente.'),
 system('S04','pi-warden','DevMortimer/pi-warden','Agentes','eventos',12,12,0,
 'O alerta semântico detecta erros úteis além das regras e sem alarmes excessivos?',
 '12 eventos: seis problemas e seis ações legítimas, com tarefas concluídas/incompletas e loops. Executar extensão em contexto Pi simulado e verificar aviso, bloqueio e continuação como resultados distintos.',
 '120 eventos de 40 episódios, estratificados por conclusão falsa, repetição e comportamento normal; 40 dev e 80 teste agrupados por episódio. A/B adicional em 24 tarefas com estado reiniciado.',
 'Regras/padrões do próprio projeto, sem Jev; agente sem extensão.',
 'Precisão de alertas >=90%, ganho de recall >=10 pp sobre regras e aumento de interrupções indevidas <=5 pp, todos exploratórios até intervalos aceitáveis. Tempo por tarefa também precisa melhorar.',
 'Pi e Node; TypeSafe direto no código. Aviso emitido não conta como dano evitado.'),
 system('S05','Jev Ultrafast','browser-use/jev-ultrafast','Agentes','tarefas web',6,48,6,
 'As decisões rápidas levam à conclusão correta da tarefa no navegador?',
 '6 tarefas em site local controlado, no máximo 8 decisões por tarefa e um auxílio de texto: selecionar, navegar, formulário, paginação, alvo ambíguo e caminho sem solução. Verificador de estado independente do modelo.',
 '24 tarefas novas (8 dev e 16 teste), reiniciadas em cada braço. Limite 8 passos, uma chamada auxiliar por tarefa; medir conclusão, ações indevidas e tempo total. Falha por limite continua no denominador.',
 'Playwright determinístico nas tarefas roteirizáveis; agente sem Jev se disponível dentro da cota de comparadores.',
 'Candidato se >=90% de sucesso no conjunto, sem ação indevida grave e tempo mediano pelo menos 20% menor que o braço comparável. Com 16 tarefas finais não declarar confiabilidade geral.',
 'Python/uv, Chrome; TypeSafe nas ações; OpenRouter no auxílio textual. Fluxos com iframe, canvas e uploads são estratos de limitações explícitas.'),
 system('S06','jevcal','abhixhek/jevcal','Calibração','registros pareados',24,0,0,
 'O compilador escolhe uma política que generaliza, ou apenas ajusta o conjunto observado?',
 '24 registros sintéticos para custo, cobertura, erro e suporte; incluir grupo sem holdout e desempenho abaixo da meta. Conferir a saída e identificar aprovação por folga do algoritmo.',
 'Mesmos 240 pares do Janus. Ajuste em dev/calibração, avaliação única em teste externo. Política por tarefa só quando suporte permite; comparar corte global.',
 'Limiar global fixado na calibração; curvas risco-cobertura do Janus.',
 'Nenhuma aprovação com suporte ausente. Usar nossa regra de intervalo, não apenas status ok ou folga de 2 pp. Preferir ferramenta mais simples quando decisões forem equivalentes.',
 'Python >=3.10, PyYAML; demo offline. Provedor OpenRouter de LLM não é o transporte Jev Decisions.'),
 system('S07','Jev Rerank Bench','anessbelbati/jev-rerank-bench','Busca','consultas',8,16,0,
 'Qual formato de decisão melhora ranking em português com custo menor?',
 '8 consultas x 10 candidatos compartilhadas com Search; conferir métrica com ranking conhecido e reproduzir um resultado existente sem rede. Até dois formatos Jev por consulta.',
 '60 consultas compartilhadas, 600 rótulos de relevância e utilidade. Fixar 10 candidatos, comprimento e ordem. Comparar dois formatos selecionados no dev, reportando recall, nDCG@5 e estabilidade.',
 'BM25, ranking original e uma ordenação aleatória como controle de implementação.',
 'Escolha por qualidade/custo por consulta, não por resultado médio de tarefas incompatíveis; ganho >=0,05 em nDCG@5 e intervalo pareado de consultas favorável.',
 'Python e dados/cache publicados. Reproduzir saída armazenada não é repetir inferência; texto truncado deve ser registrado.'),
 system('S08','System One Adapter','typesafe-ai/system-one-adapter-python','Decisões','casos',12,0,12,
 'Quanto custa obter decisões estruturadas de um modelo generalista comparável?',
 '12 casos cobrindo Choice, Noul e Score com esquema conhecido; validar JSON, número de tentativas e custo bruto de cada tentativa. Proibir correção silenciosa por novo modelo.',
 '240 pares do corpus central, 80 por tarefa, usando Gemini 2.5 Flash-Lite como comparador econômico se continuar disponível ao preço fixado. Prompts próprios adequados ao modelo, congelados com o mesmo esforço de ajuste.',
 'Jev nativo e regras locais. O comparador econômico não representa o melhor modelo generalista possível.',
 '100% de respostas conformes após política declarada; incluir respostas inválidas como falhas. Ganho de acurácia, latência e custo avaliados em conjunto.',
 'Python; OpenAI-compatible provider/base_url e OpenRouter chat. Verificar suporte do adaptador ao modelo e registrar retries.'),
 system('S09','Jev Review','devagrawal09/jev-review','Código','diffs',8,8,0,
 'A revisão identifica defeitos verificáveis sem acusar mudanças corretas?',
 '8 diffs pequenos: quatro com defeitos que um teste independente demonstra e quatro corretos; verificar associação entre alerta e trecho.',
 '80 diffs (20 dev, 20 calibração, 40 teste), metade com defeitos, diversidade de linguagem e tipo de bug. Medir precisão/recall por defeito e minutos de triagem.',
 'Testes e analisadores estáticos pertinentes; revisão sem Jev. Não presumir substituição de análise estática.',
 'Precisão >=80% e contribuição adicional comprovada em defeitos que a baseline não pega; alarme genérico sem localização e explicação verificável não conta como acerto.',
 'Node24, TypeSafe SDK; repositório descartável sem conteúdo privado; testes do defeito separados do modelo.'),
 system('S10','Every','sufianetaouil/every','Código','funções',12,2,0,
 'Busca semântica por função encontra padrões que texto/AST deixam passar?',
 '12 funções rotuladas, com sinônimos, wrappers, comentários enganosos e negativas; duas chamadas de seis decisões. Testar cache com alteração de código, rubrica e versão.',
 '80 funções (20 dev, 20 calibração, 40 teste), quatro perguntas semanticamente distintas. Até uma chamada por função com quatro questões. Separar resultados por pergunta.',
 'rg, busca textual e regra AST definida antes de olhar as respostas.',
 'Precisão >=90% e recall >=10 pp acima da melhor baseline simples em ao menos uma tarefa útil; cache deve invalidar em toda mudança semântica.',
 'Python/tree-sitter, TypeSafe direto. Corrigir ou isolar chave de cache sem versão de modelo antes de medir.'),
 system('S11','HEIST//ONE','AbdelStark/heist-one','Simulação','sementes de jogo',4,24,0,
 'Decisões locais tornam os guardas coerentes e úteis além de uma política roteirizada?',
 '4 sementes x 6 instantes de decisão; estado determinístico e validador de propostas. Repetir primeiro em modo scripted; até 24 chamadas Jev com múltiplos guardas por chamada.',
 '12 novas sementes x 6 instantes, estados idênticos entre braços. Medir ações inválidas, consistência com percepção local, diversidade útil e objetivo do jogo definido previamente.',
 'Política scripted do projeto nos mesmos estados e sementes.',
 'Zero propostas inválidas executadas; redução de incoerências sem ganho decorrente de informação privilegiada. Não usar entretenimento como evidência sobre triagem documental.',
 'Node >=22.13, pnpm; modo offline existe. Limitar observação ao que cada guarda de fato recebe.'),
 system('S12','SemIf / OpenJev','TheoLeeCJ/openjev','Modelo local','casos',8,0,0,
 'Um modelo local atende tarefas estreitas com custo operacional aceitável?',
 '8 casos com decisão e saída verificáveis em CPU/GPU suportada ou WebGPU. Primeiro verificar hardware e licença. Teste real exige carregar pesos e inferir; replay só testa integração.',
 '120 casos do corpus central, 40 por tarefa; medir acurácia, aquecimento, tokens/s, RAM/VRAM, tempo e energia estimada. Instalação e download registrados separadamente.',
 'Jev nos mesmos casos e regra local; comparar precisão/peso quando quantização mudar.',
 'Qualidade a até 5 pp de Jev no conjunto e benefício local real. Sem hardware adequado: registrar bloqueio de inferência e manter ensaio offline, sem alegar conclusão.',
 'CUDA ou WebGPU conforme implementação; verificar licença de código e pesos. Sem aluguel de GPU nem download grande automático; não é implementação dos pesos Jev.'),
 system('S13','pi-model-router','redrossa/pi-model-router','Agentes','pedidos',12,12,0,
 'A rota escolhida melhora resultado e custo da tarefa final?',
 '12 pedidos de ação clara/ambígua, pedidos mistos, negação, assunto enganoso e histórico longo. Testar seleção, fallback e restauração da configuração em Pi simulado; não chamar modelo roteado nesta etapa.',
 'Reusar triagem central; executar 24 tarefas finais pareadas, 8 dev e 16 teste, dentro da cota de agentes/comparadores. Medir qualidade final e custo total do especialista acionado.',
 'Modelo fixo e roteador determinístico por tipo de tarefa, com o mesmo orçamento final.',
 'Economia >=25%, sem queda maior que 5 pp em sucesso; intervalo ainda amplo mantém recomendação experimental. Classificação certa isoladamente não aprova roteamento.',
 'Pi/Node e TypeSafe direto; histórico limitado/truncado. Fixar lista de modelos disponíveis e prioridade.'),
 system('S14','should-ai-kill-us-all','hellogumbo/should-ai-kill-us-all','Demonstração','feeds sintéticos',6,6,0,
 'O painel reage de forma rastreável às fontes e seu cache funciona?',
 '6 feeds controlados: neutro, positivo, negativo, misto, duplicado e indisponível. Testar quatro perguntas, procedência, tempo e cache sem publicar.',
 '12 conjuntos de manchetes x duas ordens usando reaproveitamento quando idênticos; contraste de seleção/editorial e ausência de fonte. Limite financeiro comporta até 24 chamadas.',
 'Saída fixa, regras de disponibilidade e permutação de manchetes.',
 'Teste de software, sensibilidade e proveniência. Não existe gabarito observável para validar previsão de extermínio; aprovar componente técnico não aprova essa inferência.',
 'Cloudflare Pages/KV no produto, transporte TypeSafe; emulador/fixtures locais na avaliação.'),
 system('S15','Jeeves','Infrawrench/Jeeves','Agentes','mensagens',12,12,0,
 'A classificação reduz trabalho de moderação mantendo contexto e poucos falsos alarmes?',
 '12 mensagens sintéticas contextualizadas com piada, citação, ambiguidade, menção, spam e casos legítimos. Núcleo Jev e dispatcher com ações simuladas; nenhum envio a Discord/Twitch.',
 '120 eventos compartilháveis com a base de agentes, mas com rubrica própria; 40 dev e 80 teste agrupados por conversa. Medir precisão/recall, abstenção e resultado do dispatcher.',
 'Regras determinísticas e fila de revisão humana; interpretação Gemini é braço separado se for testada.',
 'Precisão de alertas >=95%, ganho de recall >=10 pp sobre regras e zero execução de ação incorreta no simulador. Tamanho inicial não prova segurança para moderação automática.',
 'Rust, PostgreSQL, QuickJS e tokens Discord/Twitch/Gemini para produto integral. Sem essas contas: núcleo executado e integração simulada ficam claramente identificados.')
]


def main():
    audit = json.loads((ROOT/'research/hermes/auditoria-local.json').read_text(encoding='utf-8'))
    plan = dict(version='1.0',date='2026-09-18',status='Planejamento completo; execução dos sistemas pendente',
                seed=20260918,paid_calls_this_stage=0,new_spend_usd=0,
                total_cap_usd=5,historical_conservative_usd=3.002937546,
                conservative_available_usd=1.997062454,planned_active_ceiling_usd=1.70,
                unresolved_budget_scope=True,
                budget=[dict(stage=n,cap_usd=v) for n,v in [
                    ('Rodada simples dos 15 sistemas',.25),('Corpus central e desenho fatorial',.40),
                    ('Busca e código em profundidade',.25),('Agentes e simulações',.25),
                    ('Comparadores e confronto de provedores',.25),('Confirmação focalizada',.30)]],
                systems=systems,
                corpus=[dict(name=n,units=u,unit=t,split=s) for n,u,t,s in [
                    ('Piloto de desenho',120,'casos novos','40 por tarefa; desenvolvimento, sem alegação confirmatória'),
                    ('Decisões centrais',840,'casos novos','280 por tarefa: 60 dev / 60 calibração / 160 teste'),
                    ('Comparação com LLM',240,'pares, subconjunto dos 840','80 por tarefa: 20 dev / 20 calibração / 40 teste'),
                    ('Busca',60,'consultas, cada uma com 10 candidatos','20 dev / 40 teste'),
                    ('Código',160,'unidades: 80 funções + 80 diffs','por tipo: 20 dev / 20 calibração / 40 teste'),
                    ('Eventos de agentes',120,'eventos agrupados em episódios','40 dev / 80 teste; grupo inteiro em um split'),
                    ('Navegação',24,'tarefas web','8 dev / 16 teste'),
                    ('Roteamento de tarefas finais',24,'tarefas finais','8 dev / 16 teste'),
                    ('HEIST',12,'sementes novas','4 dev / 8 teste'),
                    ('Painel de manchetes',12,'feeds novos','4 dev / 8 teste')]],
                audit=audit,
                references=[dict(repo=r,url=SOURCES[r]['url'],sha=SOURCES[r]['sha'],status='Referência; validar um exemplo/documentação, não ranquear como produto') for r in ['AbdelStark/awesome-typesafe','typesafe-ai/skills','Anil-matcha/awesome-jev-by-typesafe']])
    plan['smoke_totals'] = dict(systems=len(systems), heterogeneous_units=sum(s['smoke_units'] for s in systems),
        jev_call_cap=sum(s['smoke_jev_call_cap'] for s in systems),llm_call_cap=sum(s['smoke_llm_call_cap'] for s in systems))
    (OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (OUT/'matriz-testes.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(systems[0]))
        writer.writeheader(); writer.writerows(systems)
    appendix = ['\n## 13. Fichas executáveis dos 15 sistemas\n',
                'Todas as fichas abaixo são planejamento. Nenhum desses ensaios foi executado nesta entrega. Os commits completos estão no manifesto e na matriz.\n']
    for s in systems:
        appendix += [f"### {s['id']} · {s['name']}\n",f"Fonte: [{s['repo']}](https://github.com/{s['repo']}/tree/{s['sha']}). Revisão `{s['sha'][:12]}`.\n",
          f"**Pergunta:** {s['question']}\n",f"**Rodada simples — {s['smoke_units']} {s['smoke_unit']}:** {s['smoke']}\n",
          f"**Teto de chamadas simples:** {s['smoke_jev_call_cap']} Jev remoto + {s['smoke_llm_call_cap']} LLM auxiliar; zero quando só offline/local. Tentativas e retries entram no teto.\n",
          f"**Rodada aprofundada:** {s['deep']}\n",f"**Comparador:** {s['baseline']}\n",
          f"**Regra de decisão proposta:** {s['gate']}\n",f"**Preparação e limite de interpretação:** {s['dependencies']}\n"]
    protocol=(OUT/'protocolo.md').read_text(encoding='utf-8')
    (ROOT/'docs/PLANO-CIENTIFICO-JEV-HELENA.md').write_text(protocol+'\n'+'\n'.join(appendix),encoding='utf-8')
    print(json.dumps(plan['smoke_totals'],ensure_ascii=False))


if __name__=='__main__':
    main()
