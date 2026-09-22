"""Medição do Jev no Hermes, recalculada dos registros: `python3 medir.py [--gravar]`.

Fontes: `estado/decisoes.jsonl` (toda chamada), `estado/camadas.jsonl` (plugin),
`estado/portoes.jsonl` (cron) e o livro de gastos em `estado/jev.sqlite3`. Nada aqui é estimado
sem declarar: tokens evitados usam 4 caracteres por token; execuções evitadas do modelo caro
são contadas uma a uma, e o tamanho de cada uma é a média dos prompts reais daquele job em
`/root/.hermes/cron/output` — piso, porque um job com ferramentas reenvia o contexto a cada volta.

Os dois números não valem o mesmo, e o relatório não os soma. Medido em 22/09 no
`session_model_usage`, 89% da entrada do modelo principal vem do cache: token de entrada
poupado por um recorte alivia a janela e a latência, mas quase não mexe na cota. Turno evitado
por um porteiro não é entrada nenhuma — leva junto a saída e o raciocínio, que se pagam cheios.
"""
import json
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jev_hermes import nucleo  # noqa: E402

SAIDAS_DE_CRON = Path('/root/.hermes/cron/output')
ESTADO_DO_HERMES = Path('/root/.hermes/state.db')
CONFIG_DO_HERMES = Path('/root/.hermes/config.yaml')
DIAS_DO_CACHE = 14
JOBS = {'arcano-email-fabio': '6b539f9271ed', 'monitor-fabio-whatsapp': '19fa0f01b2c5',
        'email-revisao-diaria': 'a3288e4d3f60', 'radar-ia': '29f2c9f69bb3', 'sono-memoria': '99ce108c2539',
        'tese-diaria': '8f2260d9fe4a', 'boletim-taguatinga': '7e5e2b895040'}
# Camadas que tiram texto do contexto (as outras só anotam). Cada registro traz a estimativa.
CAMADAS_QUE_RECORTAM = ('leitura', 'recorte', 'skill', 'sessoes', 'resultado', 'transcricao')
CARACTERES_POR_TOKEN = 4
RELATORIO = nucleo.ESTADO / 'RELATORIO.md'
# Ferramentas que o Jev sustenta sozinho: origem no registro -> o que ela faz por Igor.
FERRAMENTAS = {
    'pendencias-whatsapp': 'pendências do WhatsApp (quem espera resposta e o que foi prometido)',
    'prazos': 'controle de prazos por e-mail, com evento na véspera',
    'camada-checklist': 'checklist de documento (contrato, triagem de acórdão)',
    'painel-encerrados': 'demandas de trabalho encerrado fora do painel da manhã',
    'rotina-painel-manha': 'painel da manhã (prioridade do dia e agenda)',
}


def linhas(arquivo):
    try:
        texto = arquivo.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return []
    saida = []
    for linha in texto.splitlines():
        try:
            saida.append(json.loads(linha))
        except ValueError:
            continue
    return saida


def tamanho_medio_do_prompt(job_id):
    """Média, em caracteres, da seção de prompt das execuções com agente daquele job."""
    tamanhos = []
    pasta = SAIDAS_DE_CRON / job_id
    for arquivo in sorted(pasta.glob('*.md'))[-60:] if pasta.exists() else []:
        texto = arquivo.read_text(encoding='utf-8', errors='replace')
        if 'wakeAgent=false' in texto or 'Mode:** no_agent' in texto:
            continue
        fim = texto.find('\n## Response')
        tamanhos.append(fim if fim > 0 else len(texto))
    return int(statistics.mean(tamanhos)) if tamanhos else None


def modelo_principal():
    """O modelo da conversa, lido do config do Hermes — não o que mais consumiu (esse é o do cron)."""
    try:
        texto = CONFIG_DO_HERMES.read_text(encoding='utf-8')
    except OSError:
        return None
    # `model:` abre um bloco (`default: gpt-6-astra`) ou traz o nome na própria linha.
    dentro = False
    for linha in texto.splitlines():
        if linha.startswith('model:'):
            nome = linha.split(':', 1)[1].strip().strip('"\'')
            if nome:
                return nome
            dentro = True
        elif dentro:
            if not linha.startswith((' ', '\t')):
                return None
            if linha.strip().startswith('default:'):
                return linha.split(':', 1)[1].strip().strip('"\'') or None
    return None


def cache_do_modelo_principal(dias=DIAS_DO_CACHE):
    """Quanto da entrada do modelo principal veio do cache — o desconto a aplicar na leitura.

    Sem isso o relatório se engana sozinho: um recorte de 20 mil tokens de entrada parece valer o
    mesmo que um turno inteiro evitado, e não vale.
    """
    consulta = ('select model, sum(input_tokens), sum(cache_read_tokens), sum(output_tokens), '
                "sum(reasoning_tokens), sum(api_call_count) from session_model_usage "
                "where last_seen > strftime('%s','now') - ? {} group by model order by 2 desc limit 1")
    modelo = modelo_principal()
    try:
        with sqlite3.connect(f'file:{ESTADO_DO_HERMES}?mode=ro', uri=True) as con:
            linha = None
            if modelo:
                linha = con.execute(consulta.format('and model = ?'), (dias * 86400, modelo)).fetchone()
            if not linha or not linha[0]:   # modelo recém-trocado ainda não aparece no uso
                linha = con.execute(consulta.format(''), (dias * 86400,)).fetchone()
    except sqlite3.Error:
        return None
    if not linha or not linha[0]:
        return None
    modelo, entrada, cache, saida, raciocinio, chamadas = (linha[0], *(v or 0 for v in linha[1:]))
    return {'modelo': modelo, 'dias': dias, 'entrada': entrada, 'cache': cache, 'saida': saida,
            'raciocinio': raciocinio, 'chamadas': chamadas,
            'parte_em_cache': round(cache / (entrada + cache), 4) if entrada + cache else None}


def medir():
    decisoes = linhas(nucleo.REGISTRO)
    camadas = linhas(nucleo.ESTADO / 'camadas.jsonl')
    portoes = linhas(nucleo.ESTADO / 'portoes.jsonl')
    situacao = nucleo.situacao()

    por_origem = defaultdict(lambda: {'chamadas': 0, 'do_cache': 0, 'falhas': 0, 'custo_usd': 0.0,
                                      'latencias': []})
    for d in decisoes:
        o = por_origem[d.get('origem', '?')]
        if d.get('cache'):
            o['do_cache'] += 1
        elif d.get('respostas') is not None:
            o['chamadas'] += 1
        else:
            o['falhas'] += 1
        o['custo_usd'] += d.get('custo_usd') or 0.0
        if d.get('latencia_ms') is not None and not d.get('cache'):
            o['latencias'].append(d['latencia_ms'])
    origens = {k: {'chamadas': v['chamadas'], 'do_cache': v['do_cache'], 'falhas': v['falhas'],
                   'custo_usd': round(v['custo_usd'], 6),
                   'latencia_mediana_ms': int(statistics.median(v['latencias'])) if v['latencias'] else None}
               for k, v in sorted(por_origem.items())}

    por_camada = defaultdict(Counter)
    tokens_evitados = 0
    for c in camadas:
        por_camada[c.get('camada')][c.get('acao', 'nada')] += 1
        if c.get('camada') in CAMADAS_QUE_RECORTAM and c.get('acao') == 'recortar':
            tokens_evitados += c.get('tokens_evitados_estimados') or 0

    execucoes = {}
    for nome, job_id in JOBS.items():
        do_job = [p for p in portoes if p.get('job') == nome]
        dormiu = sum(1 for p in do_job if not p.get('acordou'))
        media = tamanho_medio_do_prompt(job_id)
        execucoes[nome] = {'avaliacoes': len(do_job), 'agente_evitado': dormiu,
                           'agente_acordado': len(do_job) - dormiu,
                           'prompt_medio_caracteres': media,
                           'tokens_evitados_piso': (dormiu * media // CARACTERES_POR_TOKEN) if media else None,
                           'custo_jev_usd': round(sum(p.get('custo_jev_usd') or 0 for p in do_job), 6)}
    watchdog = [p for p in portoes if p.get('job') == 'watchdog-fabio']
    return {
        'situacao': situacao,
        'por_origem': origens,
        'camadas': {k: dict(v) for k, v in por_camada.items()},
        'cache_do_modelo_principal': cache_do_modelo_principal(),
        'entrada_evitada_pelos_recortes': tokens_evitados,
        'portoes': execucoes,
        'watchdog_fabio': {'avaliacoes': len(watchdog), 'alertou': sum(1 for p in watchdog if p.get('acordou'))},
        'turnos_evitados': sum(e['agente_evitado'] for e in execucoes.values()),
        'entrada_evitada_pelos_portoes_piso': sum(e['tokens_evitados_piso'] or 0 for e in execucoes.values()),
        'custo_total_jev_usd': round(sum(v['custo_usd'] for v in origens.values()), 6),
    }


def linhas_da_rota(dias=7):
    """A nota `[jev/ferramenta]` bateu com a ferramenta usada? Acumula no relatório, dia a dia."""
    try:
        from jev_hermes import aferir_rota
        m = aferir_rota.aferir(dias)
    except Exception:
        return []
    if not m.get('turnos'):
        return []
    placar = m.get('placar') or {}
    decididos = (placar.get('acertou') or 0) + (placar.get('errou') or 0)
    linhas_ = ['## Rota de ferramenta (últimos %d dias)' % dias, '']
    if decididos:
        linhas_.append(f"- {placar.get('acertou', 0)} de {decididos} turno(s) decididos usaram a ferramenta "
                       f"sugerida ({(m['acerto'] or 0) * 100:.0f}%).")
    else:
        linhas_.append('- nenhum turno decidido ainda: a nota só conta quando o modelo chega a chamar '
                       'alguma ferramenta.')
    if m.get('fora_da_conta'):
        linhas_.append(f"- {m['fora_da_conta']} fora da conta (sessão de prova, fora do agente).")
    if placar.get('abaixo do corte'):
        linhas_.append(f"- {placar['abaixo do corte']} abaixo do corte de "
                       f"{camadas_corte():.2f}: o Jev julgou e preferiu calar.")
    return linhas_ + ['']


def camadas_corte():
    from jev_hermes import camadas
    return getattr(camadas, 'CORTE_DA_FERRAMENTA', 0.9)


def mil(n):
    """Milhar com ponto, como se escreve em português."""
    return f'{n:,}'.replace(',', '.')


def nota_de_cache(c):
    if not c or c.get('parte_em_cache') is None:
        return ['> Sem leitura do `state.db`: não dá para dizer quanto da entrada vem do cache.', '']
    return [
        f"> **Como ler:** nos últimos {c['dias']} dias, {c['parte_em_cache'] * 100:.0f}% da entrada do "
        f"`{c['modelo']}` veio do cache ({mil(c['cache'])} contra {mil(c['entrada'])} novos), em "
        f"{mil(c['chamadas'])} chamadas que produziram {mil(c['saida'])} tokens de saída e "
        f"{mil(c['raciocinio'])} de raciocínio. Por isso os dois números acima não se somam: entrada "
        f"poupada é barata, turno evitado é caro.", '']


def pagina(m):
    s = m['situacao']
    partes = [
        '# Jev no Hermes — medição',
        '',
        f"Gerada de `estado/*.jsonl` e `estado/jev.sqlite3` em {nucleo._agora():%d/%m/%Y %H:%M}. "
        'Tokens evitados usam 4 caracteres por token e são piso.',
        '',
        f"- Gasto do Jev hoje: US$ {s['gasto_hoje_usd']:.6f} de US$ {s['teto_diario_usd']:.2f}; "
        f"no mês: US$ {s['gasto_mes_usd']:.6f} de US$ {s['teto_mensal_usd']:.2f}.",
        f"- **{m['turnos_evitados']} turno(s) do modelo principal evitados** pelos porteiros de cron — "
        f"cada um leva junto a saída e o raciocínio, e é a economia que se paga cheia "
        f"(piso de {mil(m['entrada_evitada_pelos_portoes_piso'])} tokens só de entrada).",
        f"- {mil(m['entrada_evitada_pelos_recortes'])} tokens de entrada poupados pelos recortes das "
        f"camadas — alívio de janela e de latência, não de cota (veja a nota de cache abaixo).",
        f"- Custo total do Jev registrado: US$ {m['custo_total_jev_usd']:.6f}.",
        '',
        *nota_de_cache(m.get('cache_do_modelo_principal')),
        '## Porteiros de cron',
        '',
        '| job | avaliações | agente evitado | agente acordado | prompt médio (caracteres) | tokens evitados (piso) |',
        '|---|---|---|---|---|---|',
    ]
    for nome, e in m['portoes'].items():
        partes.append(f"| {nome} | {e['avaliacoes']} | {e['agente_evitado']} | {e['agente_acordado']} | "
                      f"{e['prompt_medio_caracteres'] or '—'} | {e['tokens_evitados_piso'] or 0} |")
    w = m['watchdog_fabio']
    partes += ['', f"Watchdog do Fábio (sem agente): {w['avaliacoes']} avaliações com mensagem nova, "
               f"{w['alertou']} alertas.", '', '## Camadas do plugin', '']
    for nome, contagem in sorted(m['camadas'].items()):
        partes.append(f"- {nome}: " + ', '.join(f'{k} {v}' for k, v in sorted(contagem.items())))
    partes += ['', f"Entrada evitada pelos recortes (leitura, terminal, skill, sessões, resultado, transcrição): "
               f"{mil(m['entrada_evitada_pelos_recortes'])} tokens.", '',
               *linhas_da_rota(), '## Ferramentas sustentadas pelo Jev', '']
    usadas = [(n, m['por_origem'][n]) for n in FERRAMENTAS if n in m['por_origem']]
    if usadas:
        for nome, o in usadas:
            feitas = o['chamadas'] + o['do_cache']
            partes.append(f"- {FERRAMENTAS[nome]}: {feitas} julgamento(s), US$ {o['custo_usd']:.6f}"
                          + (f", {o['falhas']} falha(s)" if o['falhas'] else '') + '.')
    else:
        partes.append('- nenhuma rodou ainda.')
    partes += ['', '## Chamadas por origem', '',
               '| origem | pagas | cache | falhas | custo US$ | latência mediana |', '|---|---|---|---|---|---|']
    for nome, o in m['por_origem'].items():
        partes.append(f"| {nome} | {o['chamadas']} | {o['do_cache']} | {o['falhas']} | {o['custo_usd']:.6f} | "
                      f"{o['latencia_mediana_ms'] or '—'} ms |")
    return '\n'.join(partes) + '\n'


if __name__ == '__main__':
    medida = medir()
    if '--gravar' in sys.argv:
        RELATORIO.write_text(pagina(medida), encoding='utf-8')
        print(pagina(medida))
    else:
        print(json.dumps(medida, ensure_ascii=False, indent=1))
