"""Checklist: um documento, uma lista fixa de perguntas, um semáforo por item — numa chamada só.

    python integracao/camadas/checklist.py --documento contrato.txt --lista contrato-prestacao-de-servicos
    python integracao/camadas/checklist.py --documento - --lista caminho/da/minha-lista.json --json

Para que serve: triagem de documento contra pontos de atenção que se repetem (contrato, edital,
proposta, política). O Jev não escreve nem resume; ele responde cada pergunta da lista e diz o
quanto tem de certeza. O que ele deixa em amarelo é o que uma pessoa, ou o modelo caro, precisa
ler — é assim que poupa leitura.

Por que uma chamada só: todas as perguntas leem o mesmo documento, e o contrato aceita várias
perguntas no mesmo payload. Medido: com 4, 16 e 64 perguntas a latência é a mesma de uma (R33,
R49), e a resposta principal se mantém em 96–98%. Mandar item por item multiplica a espera pelo
número de itens e não melhora o acerto (R50).

A lista é um JSON em `integracao/camadas/listas/` (ou um caminho): `itens` com `id`, `tipo`
(`choice` ou `noul`), `pergunta`, `opcoes` (rótulo → descrição, só em `choice`) e `risco` (os
rótulos que acendem o vermelho; em `noul`, `["sim"]` ou `["nao"]`). Regras que o estudo mediu e
que esta camada aplica sozinha:

- Toda pergunta `choice` ganha a opção `nao-consta`. Sem classe de escape o Jev inventa uma
  resposta e vem confiante (R13).
- O corte é na **probabilidade** da resposta (0,90), não na confiança: a confiança depende do
  número de opções (R32) e itens da mesma lista têm números diferentes de opções.
- Pergunte o que o documento **estabelece**, não de que assunto ele fala: o Jev acha o tema
  quase sempre e erra quando o tema aparece sem a coisa (R28, R31).
- Um sentinela vai junto. Se o documento tenta dar ordem a quem o classifica, o resultado
  inteiro sai marcado e nada fica verde.
- Falha de rede, teto ou contrato devolve "não verificado"; nunca verde.
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from camadas import nucleo  # noqa: E402

LISTAS = Path(__file__).resolve().parent / 'listas'
CORTE = 0.90
LIMITE_DO_DOCUMENTO = 60000  # caracteres; cerca de 20 mil tokens, abaixo do contexto publicado de 32 mil
NAO_CONSTA = 'O documento nao trata deste ponto.'


def carregar_lista(nome):
    caminho = Path(nome)
    if not caminho.exists():
        caminho = LISTAS / (nome if nome.endswith('.json') else nome + '.json')
    lista = json.loads(caminho.read_text(encoding='utf-8'))
    for item in lista['itens']:
        if item['tipo'] not in ('choice', 'noul'):
            raise ValueError(f"item {item['id']}: tipo deve ser choice ou noul")
        if item['tipo'] == 'choice' and not set(item['risco']) <= set(item['opcoes']):
            raise ValueError(f"item {item['id']}: risco cita opção que não existe")
    return lista


def perguntas_da(lista):
    perguntas = {}
    for item in lista['itens']:
        if item['tipo'] == 'noul':
            perguntas[item['id']] = {'type': 'noul', 'instructions': item['pergunta']}
        else:
            perguntas[item['id']] = {'type': 'choice', 'instructions': item['pergunta'] + ' Use apenas o texto do documento.',
                                     'criteria': {**item['opcoes'], 'nao-consta': NAO_CONSTA}}
    perguntas['_sentinela'] = dict(nucleo.SENTINELA['sentinela'])
    return perguntas


def ler_item(item, bloco):
    """Devolve (resposta, probabilidade) de um item, qualquer que seja o tipo."""
    if not bloco:
        return None, None
    if item['tipo'] == 'noul':
        p = bloco.get('noul')
        return (None, None) if p is None else (('sim', p) if p >= 0.5 else ('nao', 1 - p))
    escolha = bloco.get('choice')
    p = (bloco.get('probabilities') or {}).get(escolha)
    if p is None and bloco.get('confidence') is not None:  # a confiança é (K·p − 1)/(K − 1)
        k = len(item['opcoes']) + 1
        p = bloco['confidence'] * (k - 1) / k + 1 / k
    return escolha, p


def semaforo(item, resposta, p, suspeito):
    if resposta is None:
        return 'não verificado'
    if suspeito or (p or 0) < CORTE:
        return 'amarelo'
    if resposta == 'nao-consta':
        return 'não consta'
    return 'vermelho' if resposta in item['risco'] else 'verde'


def auditar(documento, lista, *, transporte=None, tempo_total=30.0):
    resultados = nucleo.classificar_em_paralelo(
        [f'DOCUMENTO:\n{documento}'], perguntas_da(lista), origem='camada-checklist',
        tempo_total=tempo_total, transporte=transporte, limite=LIMITE_DO_DOCUMENTO)
    respostas, detalhe = resultados[0]
    vigia = ((respostas or {}).get('_sentinela') or {}).get('choice')
    suspeito = vigia is not None and vigia != 'nao-tenta'
    itens = []
    for item in lista['itens']:
        resposta, p = ler_item(item, (respostas or {}).get(item['id']))
        itens.append({'id': item['id'], 'pergunta': item['pergunta'], 'resposta': resposta,
                      'probabilidade': None if p is None else round(p, 3), 'cor': semaforo(item, resposta, p, suspeito)})
    cores = [i['cor'] for i in itens]
    return {'lista': lista['nome'], 'caracteres': len(documento), **nucleo.resumo_das_chamadas(resultados),
            'latencia_ms': (detalhe or {}).get('latency_ms'), 'tenta_instruir': suspeito, 'itens': itens,
            **{cor.replace(' ', '_').replace('ã', 'a'): cores.count(cor) for cor in ('vermelho', 'amarelo', 'verde', 'não consta', 'não verificado')}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--documento', required=True, help='arquivo de texto, ou - para a entrada padrão')
    parser.add_argument('--lista', required=True, help='nome de uma lista em camadas/listas/ ou caminho de um JSON')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
    documento = sys.stdin.read() if args.documento == '-' else Path(args.documento).read_text(encoding='utf-8', errors='replace')
    if len(documento) > LIMITE_DO_DOCUMENTO:
        parser.error(f'documento com {len(documento)} caracteres; o máximo é {LIMITE_DO_DOCUMENTO}. Divida por capítulo.')
    resultado = auditar(documento, carregar_lista(args.lista))
    nucleo.registrar('checklist', **{k: v for k, v in resultado.items() if k != 'itens'},
                     respostas=[(i['id'], i['resposta'], i['probabilidade'], i['cor']) for i in resultado['itens']])
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False))
        return 0
    print(f"[jev/checklist] {resultado['lista']} — {resultado['caracteres']} caracteres, {resultado['chamadas']} chamada(s), "
          f"US$ {nucleo.dec(resultado['custo_usd'], 6)}: {resultado['vermelho']} vermelho(s), {resultado['amarelo']} amarelo(s), "
          f"{resultado['verde']} verde(s), {resultado['nao_consta']} não consta.")
    if resultado['tenta_instruir']:
        print('ATENÇÃO: o documento contém texto que tenta dar ordens a quem o classifica. Nada foi marcado verde; leia você.')
    for i in resultado['itens']:
        p = nucleo.dec(i['probabilidade']) if i['probabilidade'] is not None else '—'
        print(f"- {i['cor'].upper()} ({p}) {i['id']}: {i['resposta']}")
    print('Amarelo quer dizer "leia você": a probabilidade ficou abaixo de 0,90. Verde não é parecer: é triagem.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
