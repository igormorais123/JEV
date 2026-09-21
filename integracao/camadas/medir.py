"""A medição das camadas: o que o Jev poupou, custou e errou, recalculado do registro.

    python integracao/camadas/medir.py            # imprime o resumo
    python integracao/camadas/medir.py --gravar   # gera docs/CAMADAS-CLAUDE-CODE.md e o JSON

Fontes: `estado/camadas.jsonl` (leitura, busca, sentinela, ler), `decisoes.jsonl` (roteador
de tema), `gastos.jsonl` (guarda e custo do roteador). Nada aqui chama o Jev.

O que a página afirma e o que ela não afirma:
- **Tokens evitados** são caracteres que deixaram de entrar no contexto divididos por 4. É
  estimativa declarada, não contagem do tokenizador do modelo caro.
- **Releitura** é um Read do mesmo arquivo, na mesma sessão, até dez leituras depois de um
  Read estreitado. É o sinal de arrependimento: o agente precisou do que ficou de fora.
- **Concordância da busca** é a fração dos arquivos que o Jev pôs em "leia primeiro" que o
  agente de fato leu nas oito leituras seguintes da mesma sessão. Mede se a sugestão foi
  seguida, não se estava certa.
- O valor em dólares do modelo caro usa um preço por milhão de tokens de entrada que é
  **parâmetro declarado** em `PRECO_CARO_USD_POR_MILHAO`; a página o exibe ao lado do número.
"""
import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PROJETO = RAIZ.parent
REGISTRO = RAIZ / 'estado' / 'camadas.jsonl'
DECISOES = RAIZ / 'decisoes.jsonl'
GASTOS = RAIZ / 'gastos.jsonl'
PAGINA = PROJETO / 'docs' / 'CAMADAS-CLAUDE-CODE.md'
AGREGADO = RAIZ / 'avaliacao' / 'camadas-medicao.json'

# Preço de entrada de um modelo da classe Opus, em USD por milhão de tokens. Parâmetro
# declarado para converter tokens evitados em dinheiro; o preço real do Fable não foi lido de
# nenhuma tabela pública nesta máquina.
PRECO_CARO_USD_POR_MILHAO = 15.0
JANELA_DE_RELEITURA = 10
JANELA_DE_CONCORDANCIA = 8


def _jsonl(caminho):
    if not caminho.exists():
        return []
    linhas = []
    for linha in caminho.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            linhas.append(json.loads(linha))
        except ValueError:
            continue
    return linhas


def _mediana(valores):
    valores = [v for v in valores if isinstance(v, (int, float))]
    return round(statistics.median(valores)) if valores else None


def _p90(valores):
    valores = sorted(v for v in valores if isinstance(v, (int, float)))
    return valores[int(len(valores) * 0.9) - 1 if len(valores) >= 10 else -1] if valores else None


def leitura(linhas):
    todas = [l for l in linhas if l['camada'] == 'leitura']
    com_chamada = [l for l in todas if l.get('chamadas')]
    estreitadas = [l for l in todas if l.get('acao') == 'estreitar']
    ativas = [l for l in estreitadas if l.get('modo') == 'ativo']
    # releitura: mesmo arquivo, mesma sessão, nas 10 leituras seguintes
    por_sessao = defaultdict(list)
    for l in todas:
        por_sessao[l.get('sessao')].append(l)
    releituras = 0
    linhas_relidas = 0
    sem_intervalo = 0
    for l in ativas:
        seq = por_sessao[l.get('sessao')]
        i = seq.index(l)
        voltas = [s for s in seq[i+1:i+1+JANELA_DE_RELEITURA] if s.get('arquivo') == l.get('arquivo')]
        if voltas:
            releituras += 1
            for v in voltas:
                if v.get('limit'):
                    linhas_relidas += v['limit']
                elif v.get('motivo') == 'read ja delimitado':
                    # Registro anterior ao campo de intervalo: tamanho desconhecido, não zero.
                    sem_intervalo += 1
                else:
                    # Voltou sem intervalo: o arquivo inteiro de novo, a economia daquela zera.
                    linhas_relidas += l.get('linhas') or 0
    tokens = sum(l.get('tokens_evitados_estimados') or 0 for l in ativas)
    return {
        'reads': len(todas),
        'com_pedido': sum(1 for l in todas if l.get('com_pedido')),
        'classificados': len(com_chamada),
        'estreitados': len(estreitadas),
        'estreitados_ativos': len(ativas),
        'motivos': dict(Counter(l.get('motivo') for l in todas if l.get('acao') != 'estreitar')),
        'linhas_evitadas': sum(l.get('linhas_evitadas') or 0 for l in ativas),
        'tokens_evitados': tokens,
        'releituras': releituras,
        'linhas_relidas': linhas_relidas,
        'releituras_sem_intervalo_registrado': sem_intervalo,
        'custo_usd': round(sum(l.get('custo_usd') or 0 for l in todas), 6),
        'chamadas': sum(l.get('chamadas') or 0 for l in todas),
        'latencia_mediana_ms': _mediana([l.get('latencia_ms') for l in com_chamada]),
        'latencia_p90_ms': _p90([l.get('latencia_ms') for l in com_chamada]),
        'blocos_por_classe': dict(Counter(
            c[0] for l in com_chamada for c in (l.get('blocos_classes') or []))),
        'descartaveis_a_099': sum(l.get('descartaveis_a_099') or 0 for l in com_chamada),
    }


def busca(linhas):
    todas = [l for l in linhas if l['camada'] == 'busca']
    sugeridas = [l for l in todas if l.get('acao') == 'sugerir']
    leituras = defaultdict(list)
    for l in linhas:
        if l['camada'] == 'leitura':
            leituras[l.get('sessao')].append(l)
    seguidas = total_primeiro = 0
    for l in sugeridas:
        depois = [r for r in leituras[l.get('sessao')] if r['em'] > l['em']][:JANELA_DE_CONCORDANCIA]
        lidos = {Path(r.get('arquivo') or '').name for r in depois}
        for a in l.get('primeiro') or []:
            total_primeiro += 1
            seguidas += Path(a).name in lidos
    return {
        'greps': len(todas),
        'por_ferramenta': dict(Counter(l.get('ferramenta') or 'Grep' for l in todas)),
        'classificados': sum(1 for l in todas if l.get('chamadas')),
        'sugeridos': len(sugeridas),
        'sugeridos_ativos': sum(1 for l in sugeridas if l.get('modo') == 'ativo'),
        'arquivos_no_topo': total_primeiro,
        'arquivos_no_topo_lidos_depois': seguidas,
        'arquivos_fora': sum(len(l.get('fora') or []) for l in sugeridas),
        'motivos': dict(Counter(l.get('motivo') for l in todas if l.get('acao') != 'sugerir')),
        'custo_usd': round(sum(l.get('custo_usd') or 0 for l in todas), 6),
        'chamadas': sum(l.get('chamadas') or 0 for l in todas),
        'latencia_mediana_ms': _mediana([l.get('latencia_ms') for l in todas if l.get('chamadas')]),
    }


def sentinela(linhas):
    todas = [l for l in linhas if l['camada'] == 'sentinela']
    inspecionadas = [l for l in todas if l.get('chamadas')]
    acusadas = [l for l in todas if l.get('acao') == 'avisar']
    return {
        'conteudos': len(todas),
        'inspecionados': len(inspecionadas),
        'partes': sum(l.get('partes') or 0 for l in inspecionadas),
        'acusados': len(acusadas),
        'por_ferramenta': dict(Counter(l.get('ferramenta') for l in inspecionadas)),
        'acusados_por_ferramenta': dict(Counter(l.get('ferramenta') for l in acusadas)),
        'custo_usd': round(sum(l.get('custo_usd') or 0 for l in todas), 6),
        'chamadas': sum(l.get('chamadas') or 0 for l in todas),
        'latencia_mediana_ms': _mediana([l.get('latencia_ms') for l in inspecionadas]),
    }


def saida(linhas):
    todas = [l for l in linhas if l['camada'] == 'saida']
    classificadas = [l for l in todas if l.get('chamadas')]
    apontadas = [l for l in todas if l.get('acao') == 'apontar']
    return {
        'saidas_com_erro': len(todas),
        'classificadas': len(classificadas),
        'apontadas': len(apontadas),
        'partes_por_classe': dict(Counter(
            c['classe'] for l in classificadas for c in (l.get('classes') or []))),
        'motivos': dict(Counter(l.get('motivo') for l in todas if l.get('acao') != 'apontar')),
        'custo_usd': round(sum(l.get('custo_usd') or 0 for l in todas), 6),
        'chamadas': sum(l.get('chamadas') or 0 for l in todas),
        'latencia_mediana_ms': _mediana([l.get('latencia_ms') for l in classificadas]),
    }


def verificar(linhas):
    todas = [l for l in linhas if l['camada'] == 'verificar']
    return {
        'usos': len(todas),
        'afirmacoes': sum(l.get('afirmacoes') or 0 for l in todas),
        'suportadas': sum(l.get('suportadas') or 0 for l in todas),
        'contraditas': sum(l.get('contraditas') or 0 for l in todas),
        'nao_informadas': sum(l.get('nao_informadas') or 0 for l in todas),
        'nao_verificadas': sum(l.get('nao_verificadas') or 0 for l in todas),
        'custo_usd': round(sum(l.get('custo_usd') or 0 for l in todas), 6),
        'chamadas': sum(l.get('chamadas') or 0 for l in todas),
    }


def ler(linhas):
    todas = [l for l in linhas if l['camada'] == 'ler']
    ok = [l for l in todas if l.get('acao') == 'selecionar']
    return {
        'usos': len(todas),
        'selecionaram': len(ok),
        'blocos': sum(l.get('blocos') or 0 for l in ok),
        'blocos_devolvidos': sum(len(l.get('selecionados') or []) for l in ok),
        'caracteres_total': sum(l.get('caracteres_total') or 0 for l in ok),
        'caracteres_devolvidos': sum(l.get('caracteres_devolvidos') or 0 for l in ok),
        'tokens_evitados': sum(l.get('tokens_evitados_estimados') or 0 for l in ok),
        'custo_usd': round(sum(l.get('custo_usd') or 0 for l in todas), 6),
        'chamadas': sum(l.get('chamadas') or 0 for l in todas),
    }


def roteador_e_guarda():
    decisoes = _jsonl(DECISOES)
    gastos = _jsonl(GASTOS)
    producao = [d for d in decisoes if d.get('origem') == 'claude-code/UserPromptSubmit']
    guarda = [g for g in gastos if g.get('origem') == 'guarda-de-comando']
    return {
        'roteador': {
            'decisoes': len(producao),
            'sugeriu': sum(1 for d in producao if d.get('sugere')),
            'cache': sum(1 for d in producao if d.get('cache')),
            'custo_usd': round(sum(d.get('custo_usd') or 0 for d in producao), 6),
            'latencia_mediana_ms': _mediana([d.get('latencia_ms') for d in producao if not d.get('cache')]),
        },
        'guarda': {'chamadas': len(guarda),
                   'custo_usd': round(sum(g.get('custo_usd') or 0 for g in guarda), 6)},
    }


# Sessões de teste de ponta a ponta (os hooks rodados à mão com `session_id` "smoke-...")
# ficam fora da medida: são chamadas reais, mas não são uso real.
PREFIXO_DE_FUMACA = 'smoke-'


def medir():
    linhas = [l for l in _jsonl(REGISTRO)
              if not str(l.get('sessao') or '').startswith(PREFIXO_DE_FUMACA)]
    dado = {'leitura': leitura(linhas), 'busca': busca(linhas), 'sentinela': sentinela(linhas),
            'ler': ler(linhas), 'saida': saida(linhas), 'verificar': verificar(linhas),
            **roteador_e_guarda(),
            'parametros': {'caracteres_por_token': 4, 'preco_caro_usd_por_milhao': PRECO_CARO_USD_POR_MILHAO,
                           'janela_de_releitura': JANELA_DE_RELEITURA,
                           'janela_de_concordancia': JANELA_DE_CONCORDANCIA}}
    tokens = dado['leitura']['tokens_evitados'] + dado['ler']['tokens_evitados']
    custo_jev = sum(dado[c]['custo_usd'] for c in ('leitura', 'busca', 'sentinela', 'ler', 'saida',
                                                    'verificar', 'roteador', 'guarda'))
    dado['total'] = {
        'tokens_evitados': tokens,
        'valor_evitado_usd_ao_preco_declarado': round(tokens / 1e6 * PRECO_CARO_USD_POR_MILHAO, 4),
        'custo_jev_usd': round(custo_jev, 6),
        'chamadas_jev': sum(dado[c].get('chamadas') or 0
                            for c in ('leitura', 'busca', 'sentinela', 'ler', 'saida', 'verificar')),
        'registros': len(linhas),
        'primeiro_registro': linhas[0]['em'] if linhas else None,
        'ultimo_registro': linhas[-1]['em'] if linhas else None,
    }
    return dado


def n(v):
    if v is None:
        return '—'
    if isinstance(v, float):
        return f'{v:,.6f}'.replace(',', 'X').replace('.', ',').replace('X', '.').rstrip('0').rstrip(',')
    return f'{v:,}'.replace(',', '.')


def pagina(d):
    L, B, S, R, T = d['leitura'], d['busca'], d['sentinela'], d['ler'], d['total']
    SA, V = d['saida'], d['verificar']
    rot, gua = d['roteador'], d['guarda']
    releitura = f"{L['releituras']} de {L['estreitados_ativos']}" if L['estreitados_ativos'] else '—'
    concord = (f"{B['arquivos_no_topo_lidos_depois']} de {B['arquivos_no_topo']}"
               if B['arquivos_no_topo'] else '—')
    return f"""# O Jev em camadas no Claude Code — medição

*Página gerada por `integracao/camadas/medir.py --gravar`; não edite à mão. Os números saem
de `integracao/estado/camadas.jsonl`, `decisoes.jsonl` e `gastos.jsonl`, e cada linha desses
arquivos é uma decisão de verdade tomada numa sessão desta máquina, nos dois modos. Sessões
de teste de ponta a ponta (`smoke-*`) ficam fora.*

Registros: **{n(T['registros'])}** ({T['primeiro_registro'] or '—'} a {T['ultimo_registro'] or '—'}).

## As camadas, e o que cada uma faz com o contexto do modelo caro

| camada | ponto do fluxo | o que decide | base no estudo |
|---|---|---|---|
| tema (roteador) | `UserPromptSubmit` | sobre o que é o pedido; sugere a skill | E1, E13: 9 de 23 temas, 0 falsos |
| leitura | `PreToolUse` em `Read` | que janela do arquivo entra | E16, R18, R20, R26: top-3 mantém a resposta, corta 74% |
| busca | `PostToolUse` em `Grep`, `Glob`, WebSearch, buscas do Gmail, Drive e Agenda | por qual item começar | E1, E16: triagem 92–99%, 8 de 8 essenciais no topo |
| sentinela | `PostToolUse` em conteúdo externo e no conteúdo colado no prompt | se o texto tenta dar ordens | R23, R27: 95% de detecção, 2,4% de alarme falso |
| saída | `PostToolUse` em `Bash` com erro e 3 mil caracteres ou mais | em que parte da saída está a causa | não medida no estudo; só aponta com confiança ≥ 0,90 |
| verificar (skill `/jev-verificar`) | quando o agente chama | se cada afirmação se sustenta na fonte | E3: 95,8% contra 62,5% |
| guarda (sombra) | `PreToolUse` em `Bash` | se o comando barrado pode passar | R16: 72% → 30% de interrupção, 0 de 12 liberados |
| ler (skill `/jev-ler`) | quando o agente chama | quais blocos de vários arquivos entram | R18, R20, R26: k = 3 |

## O total

| | valor |
|---|---|
| tokens que deixaram de entrar no contexto (estimados, 4 caracteres por token) | **{n(T['tokens_evitados'])}** |
| o que isso vale ao preço declarado de US$ {n(d['parametros']['preco_caro_usd_por_milhao'])}/M de entrada (parâmetro, não preço lido) | US$ {n(T['valor_evitado_usd_ao_preco_declarado'])} |
| chamadas ao Jev pelas camadas | {n(T['chamadas_jev'])} |
| custo do Jev, todas as camadas e o roteador | **US$ {n(T['custo_jev_usd'])}** |

## Leitura (`Read`)

| | valor |
|---|---|
| Reads vistos pelo hook | {n(L['reads'])} |
| com pedido vigente na sessão | {n(L['com_pedido'])} |
| classificados (arquivo grande, com pedido) | {n(L['classificados'])} |
| estreitados | {n(L['estreitados'])} (em modo ativo: {n(L['estreitados_ativos'])}) |
| linhas evitadas | {n(L['linhas_evitadas'])} |
| tokens evitados (estimados) | **{n(L['tokens_evitados'])}** |
| releitura do mesmo arquivo em até {JANELA_DE_RELEITURA} leituras (arrependimento) | **{releitura}** |
| linhas relidas nessas voltas (o que fez falta) | {n(L['linhas_relidas'])} de {n(L['linhas_evitadas'])} evitadas{(' (mais ' + n(L['releituras_sem_intervalo_registrado']) + ' volta(s) de tamanho não registrado)') if L['releituras_sem_intervalo_registrado'] else ''} |
| blocos por classe | {', '.join(f'{k}: {v}' for k, v in sorted(L['blocos_por_classe'].items())) or '—'} |
| blocos que uma regra "irrelevante ≥ 0,99" descartaria | {n(L['descartaveis_a_099'])} |
| latência mediana / p90 do hook | {n(L['latencia_mediana_ms'])} ms / {n(L['latencia_p90_ms'])} ms |
| custo | US$ {n(L['custo_usd'])} em {n(L['chamadas'])} chamadas |

Por que não estreitou: {', '.join(f'{k}: {v}' for k, v in sorted(L['motivos'].items(), key=lambda x: -x[1])) or '—'}.

## Busca (`Grep`, `Glob` e listagens externas)

| | valor |
|---|---|
| listagens vistas | {n(B['greps'])} ({', '.join(f'{k}: {v}' for k, v in sorted(B['por_ferramenta'].items())) or '—'}) |
| classificados (6 ou mais arquivos, com pedido) | {n(B['classificados'])} |
| com sugestão | {n(B['sugeridos'])} (em modo ativo: {n(B['sugeridos_ativos'])}) |
| arquivos postos em "leia primeiro" | {n(B['arquivos_no_topo'])} |
| desses, lidos pelo agente nas {JANELA_DE_CONCORDANCIA} leituras seguintes | **{concord}** |
| arquivos marcados irrelevantes com ≥ 0,99 | {n(B['arquivos_fora'])} |
| latência mediana | {n(B['latencia_mediana_ms'])} ms |
| custo | US$ {n(B['custo_usd'])} em {n(B['chamadas'])} chamadas |

Por que não sugeriu: {', '.join(f'{k}: {v}' for k, v in sorted(B['motivos'].items(), key=lambda x: -x[1])) or '—'}.

## Sentinela (conteúdo externo)

| | valor |
|---|---|
| conteúdos vistos | {n(S['conteudos'])} |
| inspecionados (partes de 3.500 caracteres) | {n(S['inspecionados'])} ({n(S['partes'])} partes) |
| acusados | **{n(S['acusados'])}** |
| por ferramenta | {', '.join(f'{k}: {v}' for k, v in sorted(S['por_ferramenta'].items())) or '—'} |
| acusados por ferramenta | {', '.join(f'{k}: {v}' for k, v in sorted(S['acusados_por_ferramenta'].items())) or '—'} |
| latência mediana | {n(S['latencia_mediana_ms'])} ms |
| custo | US$ {n(S['custo_usd'])} em {n(S['chamadas'])} chamadas |

Uma acusação não é bloqueio: o conteúdo continua no contexto com um aviso. A R23 mede 2,4% de
alarme falso em texto limpo e 7 de 24 em texto legítimo com palavra-gatilho; a taxa aqui só
vira medida de acerto quando alguém revisar as acusações.

## Saída de comando (`Bash`, `PowerShell`)

| | valor |
|---|---|
| saídas longas com marca de erro | {n(SA['saidas_com_erro'])} |
| classificadas | {n(SA['classificadas'])} |
| com causa apontada (confiança ≥ 0,90) | **{n(SA['apontadas'])}** |
| partes por classe | {', '.join(f'{k}: {v}' for k, v in sorted(SA['partes_por_classe'].items())) or '—'} |
| latência mediana | {n(SA['latencia_mediana_ms'])} ms |
| custo | US$ {n(SA['custo_usd'])} em {n(SA['chamadas'])} chamadas |

Aplicação não medida no estudo: a parte apontada só vira acerto quando alguém conferir contra
a causa real. Por que não apontou: {', '.join(f'{k}: {v}' for k, v in sorted(SA['motivos'].items(), key=lambda x: -x[1])) or '—'}.

## Verificação pela skill (`/jev-verificar`)

| | valor |
|---|---|
| usos / afirmações | {n(V['usos'])} / {n(V['afirmacoes'])} |
| suportadas (confiança ≥ 0,90) | {n(V['suportadas'])} |
| contraditas | **{n(V['contraditas'])}** |
| não informadas pela fonte | {n(V['nao_informadas'])} |
| não verificadas (falha) | {n(V['nao_verificadas'])} |
| custo | US$ {n(V['custo_usd'])} em {n(V['chamadas'])} chamadas |

## Leitura seletiva pela skill (`/jev-ler`)

| | valor |
|---|---|
| usos | {n(R['usos'])} (com seleção: {n(R['selecionaram'])}) |
| blocos classificados / devolvidos | {n(R['blocos'])} / {n(R['blocos_devolvidos'])} |
| caracteres nos candidatos / devolvidos | {n(R['caracteres_total'])} / {n(R['caracteres_devolvidos'])} |
| tokens evitados (estimados) | **{n(R['tokens_evitados'])}** |
| custo | US$ {n(R['custo_usd'])} em {n(R['chamadas'])} chamadas |

## Tema e guarda (as camadas anteriores)

| | valor |
|---|---|
| decisões do roteador de tema em produção | {n(rot['decisoes'])} (sugeriu skill em {n(rot['sugeriu'])}; {n(rot['cache'])} do cache) |
| latência mediana sem cache | {n(rot['latencia_mediana_ms'])} ms |
| custo do roteador | US$ {n(rot['custo_usd'])} |
| guarda de comando (sombra) | {n(gua['chamadas'])} chamadas, US$ {n(gua['custo_usd'])} |

## O que esta página não prova

- Tokens evitados são estimativa por caracteres; o tokenizador do modelo caro conta diferente.
- Uma leitura estreitada sem releitura não prova que a janela bastou: prova que o agente não
  voltou. A medida de acerto exige revisar as janelas contra o que o agente de fato usou.
- A concordância da busca mede se a sugestão foi seguida, e o agente que a segue pode estar
  seguindo o próprio Grep.
- O valor em dólares depende do preço declarado no parâmetro; troque-o e a linha muda.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gravar', action='store_true')
    args = parser.parse_args()
    dado = medir()
    if args.gravar:
        PAGINA.write_text(pagina(dado), encoding='utf-8')
        AGREGADO.parent.mkdir(parents=True, exist_ok=True)
        AGREGADO.write_text(json.dumps(dado, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'gravado: {PAGINA} e {AGREGADO}')
    print(json.dumps(dado['total'], ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
