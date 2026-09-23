"""Fluxo 5 — comparação de desempenho: "qual arquitetura funciona melhor sob as mesmas condições?".

O quadro: mesmas tarefas (defeitos, funcionalidades, pesquisa, refatoração) → bancada de testes →
arquitetura A e arquitetura B + JEV → medir, não "achar": taxa de sucesso, custo, latência, novas
tentativas, intervenção humana; "arquitetura boa é uma hipótese testável". Aqui:

- **Mesmas condições**: cada execução começa numa pasta nova, copiada da mesma tarefa, com o mesmo
  orçamento. A ordem das arquiteturas alterna a cada repetição.
- **Sucesso é do verificador oculto**, não da arquitetura: os testes escondidos só são escritos na
  pasta depois que a arquitetura terminou, e rodados pelo harness. Uma arquitetura que "conclui"
  com o código errado conta como fracasso; uma que chama uma pessoa conta como intervenção humana.
- **As cinco medidas** por execução; a comparação usa `workflows.comparar_experimentos` (Wilson
  para proporções, IC95 aproximado para médias; vencedor só com intervalo separado de todas as
  alternativas). Com poucas repetições o resultado honesto é "inconclusivo".

Arquiteturas: `esteira` (A, `agentes` com `esteira=True`), `jev` (B, roteador por estado do
fluxo 2 com modelos do fluxo 3 e o judge do fluxo 1) e `avaliacao` (só o laço do fluxo 1).
Tarefas em `jev_hermes/tarefas_bancada/*.json`. Relatório em `estado/bancada/`.

CLI: `python3 -m jev_hermes.bancada --arquiteturas esteira jev --repeticoes 1 [--tarefas ID...]`.
Roda agentes de verdade (Claude Code na assinatura): use `systemd-run` para não morrer com o SSH.
"""
import json
import os
import shlex
import shutil
import sys
import tempfile
import time
from pathlib import Path

from . import agentes, avaliacao, nucleo, workflows

TAREFAS = Path(__file__).resolve().parent / 'tarefas_bancada'
SAIDA = nucleo.ESTADO / 'bancada'
# Interpretador com pytest para os testes das tarefas (`{python}` nos comandos). O Python do sistema
# da VPS não tem pytest; o ambiente do hermes-agent tem.
PYTHON = os.environ.get('JEV_BANCADA_PYTHON') or next(
    (p for p in ('/root/.hermes/hermes-agent/.venv/bin/python',) if Path(p).exists()), sys.executable)


def comando(texto):
    return texto.replace('{python}', shlex.quote(PYTHON)).replace('{vazio}', shlex.quote(os.devnull))


def carregar_tarefas(ids=None):
    tarefas = []
    for arquivo in sorted(TAREFAS.glob('*.json')):
        tarefa = json.loads(arquivo.read_text(encoding='utf-8'))
        if not ids or tarefa['id'] in ids:
            tarefas.append(tarefa)
    return tarefas


def preparar(tarefa, pasta):
    for nome, conteudo in tarefa['arquivos'].items():
        alvo = pasta / nome
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(conteudo, encoding='utf-8')


def verificar(tarefa, pasta):
    """Escreve o verificador oculto depois da arquitetura e roda pelo harness. True = sucesso.
    Roda sem `conftest.py` nem arquivo de configuração da pasta: o que o agente criou não o altera."""
    for nome, conteudo in tarefa['verificador']['arquivos'].items():
        (pasta / nome).write_text(conteudo, encoding='utf-8')
    obs = avaliacao.observar_testes(comando(tarefa['verificador']['comando']), pasta)
    r = obs.resultado
    return r['codigo_saida'] == 0 and not r.get('falharam') and r.get('executados') != 0, r


def _novas_tentativas(por_papel):
    return sum(max(0, n - 1) for n in (por_papel or {}).values())


# ---------------------------------------------------------------------------- arquiteturas

def arq_agentes(esteira):
    def rodar(tarefa, pasta, orcamento_usd, transporte=None):
        fim = agentes.resolver(pasta, tarefa['pedido'], comando(tarefa['teste_visivel']),
                               orcamento_usd=orcamento_usd, esteira=esteira, transporte=transporte)
        estado = json.loads((nucleo.ESTADO / 'ciclos' / f"{fim['id']}.json").read_text(encoding='utf-8'))
        return {'humano': fim['situacao'] != 'concluido', 'custo_usd': (fim['custo_agentes_usd'] or 0)
                + (fim['custo_jev_usd'] or 0), 'novas_tentativas': _novas_tentativas(estado.get('tentativas_por_papel')),
                'passos': fim['passos'], 'motivo': fim.get('motivo')}
    return rodar


def arq_avaliacao(tarefa, pasta, orcamento_usd, transporte=None):
    fim = avaliacao.tarefa_de_codigo(pasta, tarefa['pedido'], comando(tarefa['teste_visivel']),
                                     orcamento_usd=orcamento_usd, transporte=transporte)
    return {'humano': fim['resultado'] != 'aprovado', 'custo_usd': fim['custo_agente_usd'],
            'novas_tentativas': fim['tentativas'] - 1, 'passos': [h['veredito'] for h in fim['historico']],
            'motivo': fim['motivo']}


ARQUITETURAS = {'esteira': arq_agentes(True), 'jev': arq_agentes(False), 'avaliacao': arq_avaliacao}


# ------------------------------------------------------------------------------ bancada

def rodar(tarefas, nomes, *, repeticoes=1, orcamento_usd=6.0, arquiteturas=None, transporte=None):
    arquiteturas = arquiteturas or ARQUITETURAS
    execucoes = []
    for repeticao in range(repeticoes):
        ordem = nomes if repeticao % 2 == 0 else list(reversed(nomes))
        for tarefa in tarefas:
            for nome in ordem:
                pasta = Path(tempfile.mkdtemp(prefix=f"bancada-{tarefa['id']}-{nome}-"))
                preparar(tarefa, pasta)
                inicio = time.time()
                try:
                    medida = arquiteturas[nome](tarefa, pasta, orcamento_usd, transporte=transporte)
                except Exception as erro:
                    medida = {'humano': True, 'custo_usd': 0.0, 'novas_tentativas': 0,
                              'motivo': f'arquitetura falhou: {type(erro).__name__}: {str(erro)[:160]}'}
                latencia = round(time.time() - inicio, 1)
                sucesso, verificacao = verificar(tarefa, pasta)
                execucoes.append({'tarefa': tarefa['id'], 'tipo': tarefa['tipo'], 'arquitetura': nome,
                                  'repeticao': repeticao + 1, 'sucesso': sucesso, 'latencia_s': latencia,
                                  'custo_usd': round(medida.get('custo_usd') or 0.0, 4),
                                  'novas_tentativas': medida.get('novas_tentativas', 0),
                                  'intervencao_humana': bool(medida.get('humano')),
                                  'passos': medida.get('passos'), 'motivo': medida.get('motivo'),
                                  'verificador': verificacao})
                nucleo.registrar({'em': nucleo._agora().isoformat(timespec='seconds'),
                                  **{k: v for k, v in execucoes[-1].items() if k not in ('passos', 'verificador')}},
                                 nucleo.ESTADO / 'bancada.jsonl')
                shutil.rmtree(pasta, ignore_errors=True)
    return execucoes


def _media(valores):
    n = len(valores)
    media = sum(valores) / n
    desvio = (sum((v - media) ** 2 for v in valores) / (n - 1)) ** 0.5 if n > 1 else None
    return {'media': round(media, 4), 'desvio': round(desvio, 4) if desvio is not None else None, 'n': n}


def comparar(execucoes, *, amostra_minima=10, transporte=None):
    """As cinco medidas por arquitetura e a comparação calculada (taxa de sucesso é o critério principal)."""
    por_arq = {}
    for e in execucoes:
        por_arq.setdefault(e['arquitetura'], []).append(e)
    configuracoes = []
    for nome, lista in por_arq.items():
        configuracoes.append({'id': nome, 'descricao': f'arquitetura {nome}', 'resultados': {
            'taxa_sucesso': {'sucessos': sum(e['sucesso'] for e in lista), 'total': len(lista)},
            'custo_usd': _media([e['custo_usd'] for e in lista]),
            'latencia_s': _media([e['latencia_s'] for e in lista]),
            'novas_tentativas': _media([e['novas_tentativas'] for e in lista]),
            'intervencao_humana': {'sucessos': sum(e['intervencao_humana'] for e in lista), 'total': len(lista)}}})
    for c in configuracoes:   # média sem desvio (n = 1) não tem intervalo: o comparador exige os dois
        for medida in c['resultados'].values():
            if medida.get('desvio', 0) is None:
                medida.pop('desvio')
    if len(configuracoes) < 2:
        return {'configuracoes': configuracoes, 'comparacao': None}
    criterios = [{'metrica': 'taxa_sucesso', 'direcao': 'maior', 'amostra_minima': amostra_minima}] + [
        {'metrica': m, 'direcao': 'menor', 'amostra_minima': 1}
        for m in ('custo_usd', 'latencia_s', 'novas_tentativas', 'intervencao_humana')]
    comparacao = workflows.comparar_experimentos(
        {'objetivo': 'Resolver tarefas de código com a maior taxa de sucesso, depois menor custo, latência, '
                     'novas tentativas e intervenção humana.', 'criterios': criterios,
         'configuracoes': configuracoes, 'consultar_jev': False}, transporte=transporte)
    return {'configuracoes': configuracoes, 'comparacao': comparacao}


def relatorio(execucoes, analise):
    linhas = ['# Bancada dos fluxos JEV', '', f'{nucleo._agora():%d/%m/%Y %H:%M} · {len(execucoes)} execuções', '',
              '| arquitetura | sucesso | custo médio (US$ nominais) | latência média (s) | novas tentativas | '
              'intervenção humana |', '|---|---|---|---|---|---|']
    for c in analise['configuracoes']:
        r = c['resultados']
        linhas.append(f"| {c['id']} | {r['taxa_sucesso']['sucessos']}/{r['taxa_sucesso']['total']} | "
                      f"{nucleo.dec(r['custo_usd']['media'], 2)} | {nucleo.dec(r['latencia_s']['media'], 0)} | "
                      f"{nucleo.dec(r['novas_tentativas']['media'], 1)} | "
                      f"{r['intervencao_humana']['sucessos']}/{r['intervencao_humana']['total']} |")
    comp = (analise.get('comparacao') or {}).get('comparacao') or {}
    if comp:
        linhas += ['', f"Comparação (taxa de sucesso, IC95): **{comp['resultado']}** — {comp.get('motivo', '')}"]
        avisos = analise['comparacao'].get('avisos') or []
        if avisos:
            linhas += ['', 'Avisos: ' + '; '.join(avisos[:6])]
    linhas += ['', '| tarefa | tipo | arquitetura | sucesso | s | US$ | passos |', '|---|---|---|---|---|---|---|']
    for e in execucoes:
        linhas.append(f"| {e['tarefa']} | {e['tipo']} | {e['arquitetura']} | {'sim' if e['sucesso'] else 'não'} | "
                      f"{e['latencia_s']:.0f} | {e['custo_usd']:.2f} | {', '.join(e['passos'] or [])[:120]} |")
    return '\n'.join(linhas) + '\n'


if __name__ == '__main__':
    import argparse
    analisador = argparse.ArgumentParser(description='Fluxo 5: bancada de comparação de arquiteturas.')
    analisador.add_argument('--arquiteturas', nargs='+', default=['esteira', 'jev'], choices=sorted(ARQUITETURAS))
    analisador.add_argument('--tarefas', nargs='*')
    analisador.add_argument('--repeticoes', type=int, default=1)
    analisador.add_argument('--orcamento', type=float, default=6.0)
    analisador.add_argument('--amostra-minima', type=int, default=10)
    a = analisador.parse_args()
    execucoes = rodar(carregar_tarefas(a.tarefas), a.arquiteturas, repeticoes=a.repeticoes, orcamento_usd=a.orcamento)
    analise = comparar(execucoes, amostra_minima=a.amostra_minima)
    SAIDA.mkdir(parents=True, exist_ok=True)
    carimbo = nucleo._agora().strftime('%Y%m%d-%H%M')
    (SAIDA / f'{carimbo}.json').write_text(json.dumps({'execucoes': execucoes, 'analise': analise},
                                                      ensure_ascii=False, indent=1), encoding='utf-8')
    texto = relatorio(execucoes, analise)
    (SAIDA / f'{carimbo}.md').write_text(texto, encoding='utf-8')
    print(texto)
