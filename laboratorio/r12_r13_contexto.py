"""R12 e R13 — diluição de contexto medida direito, e o que ele faz sem resposta certa.

R12 refaz a dimensão que meu próprio truncamento estragou na R11, agora com o limite do núcleo
em 90.000 caracteres e uma varredura fina. Duas posições da mensagem, porque a posição pode ser
a variável que importa: recheio **antes** e recheio **depois** do pedido.

R13 é a rodada que nasceu do acidente. Quando o texto truncado chegou sem pedido nenhum, o Jev
respondeu `informacao` nos 30 casos, **com confiança 1,0 em todos**. Isso é um modo de falha de
primeira ordem e ninguém tinha olhado: o contrato não oferece "nenhuma das anteriores", e o
modelo não tem como dizer que a pergunta não se aplica. Aqui eu meço isso de propósito, e testo
a mitigação óbvia — dar a ele uma saída.

    python laboratorio/r12_r13_contexto.py
"""
import json
import random
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from executor.run_e12_replicacao import CRITERIOS, INSTRUCOES  # noqa: E402
from laboratorio.nucleo import em_paralelo, perguntar, wilson  # noqa: E402
from laboratorio.r11_extremos import RECHEIO, corpus, diluir  # noqa: E402

DESTINO = RAIZ / 'laboratorio' / 'r12-r13-contexto.json'
SEMENTE = 20260919

# --------------------------------------------------------------- R13: textos sem pedido algum

SEM_PEDIDO = [
    ('vazio-01', 'Politica interna de atendimento, secao 4. O colaborador deve registrar o '
                 'protocolo antes de encerrar o contato.'),
    ('vazio-02', 'A reuniao com o fornecedor foi remarcada para quinta-feira as 15h na sala 2.'),
    ('vazio-03', 'Bom dia.'),
    ('vazio-04', 'Receita de bolo de fuba: tres ovos, duas xicaras de fuba, uma de acucar.'),
    ('vazio-05', 'O campeonato termina em dezembro e a tabela sai na semana que vem.'),
    ('vazio-06', 'Obrigado.'),
    ('vazio-07', 'asdkjh askjdh aksjdh kajsdh'),
    ('vazio-08', 'Segue anexo o comprovante conforme conversamos.'),
    ('vazio-09', 'O tempo hoje em Brasilia esta seco, umidade de 18 por cento.'),
    ('vazio-10', 'Contrato numero 4471, clausula decima segunda, paragrafo unico.'),
]

# A mitigação: as mesmas cinco classes mais uma saída explícita.
CRITERIOS_COM_SAIDA = dict(CRITERIOS)
CRITERIOS_COM_SAIDA['nao-se-aplica'] = ('A mensagem nao contem nenhum pedido de acao ao '
                                        'atendimento, ou nao e uma mensagem de cliente.')


def tarefas_r12(casos):
    saida = []
    for tamanho in (0, 8000, 12000, 16000, 20000, 30000, 50000):
        for posicao in ('antes', 'depois'):
            if tamanho == 0 and posicao == 'depois':
                continue
            for caso in casos:
                if posicao == 'antes':
                    texto = diluir(caso['text'], tamanho)
                else:
                    recheio = ''.join(RECHEIO.format(n=i) for i in range(1, 400))[:tamanho]
                    texto = caso['text'] + ('\n\n' + recheio if recheio else '')
                saida.append({'rodada': 'R12', 'condicao': f'{tamanho // 1000}k-{posicao}',
                              'case_id': caso['case_id'], 'alvo': caso['gold'],
                              'texto': texto, 'criterios': dict(CRITERIOS),
                              'tamanho': len(texto)})
    return saida


def tarefas_r13():
    saida = []
    for case_id, texto in SEM_PEDIDO:
        saida.append({'rodada': 'R13', 'condicao': 'sem-saida', 'case_id': case_id,
                      'alvo': None, 'texto': texto, 'criterios': dict(CRITERIOS),
                      'tamanho': len(texto)})
        saida.append({'rodada': 'R13', 'condicao': 'com-saida', 'case_id': case_id,
                      'alvo': 'nao-se-aplica', 'texto': texto,
                      'criterios': dict(CRITERIOS_COM_SAIDA), 'tamanho': len(texto)})
    return saida


def executar(tarefa):
    perguntas = {'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                          'criteria': tarefa['criterios']}}
    respostas, detalhe = perguntar(f"Mensagem do cliente:\n{tarefa['texto']}", perguntas,
                                   rodada=tarefa['rodada'])
    alvo = (respostas or {}).get('acao') or {}
    return {**{k: tarefa[k] for k in ('rodada', 'condicao', 'case_id', 'alvo', 'tamanho')},
            'escolha': alvo.get('choice'), 'confianca': alvo.get('confidence'),
            'erro': None if respostas else (detalhe or {}).get('erro')}


def main():
    casos = corpus()
    todas = tarefas_r12(casos) + tarefas_r13()
    print(f'{len(todas)} chamadas | maior estado: '
          f'{max(t["tamanho"] for t in todas):,} caracteres')

    linhas = em_paralelo(todas, executar, trabalhadores=10, rotulo='R12/R13')
    por = {}
    for linha in linhas:
        por.setdefault(linha['condicao'], []).append(linha)

    resultado = {'chamadas': len(todas), 'R12': {}, 'R13': {}, 'detalhe': linhas}

    print('\n== R12: diluição de contexto, agora sem truncar a mensagem')
    print(f"   {'condição':14} {'estado':>10} {'acurácia':>9} {'conf.média':>11} "
          f"{'erro≥0,90':>10} {'s/resp':>7}  resposta dominante")
    for nome, grupo in sorted(por.items(), key=lambda kv: (kv[0].endswith('depois'), kv[0])):
        if grupo[0]['rodada'] != 'R12':
            continue
        validas = [l for l in grupo if l['escolha']]
        certos = [l for l in validas if l['escolha'] == l['alvo']]
        errados = [l for l in validas if l['escolha'] != l['alvo']]
        dominante = Counter(l['escolha'] for l in validas).most_common(1)
        bloco = {'n': len(validas), 'sem_resposta': len(grupo) - len(validas),
                 'acuracia': round(len(certos) / len(validas), 4) if validas else None,
                 'ic95': wilson(len(certos), len(validas)),
                 'conf_media': round(sum(l['confianca'] or 0 for l in validas) / len(validas), 4) if validas else None,
                 'erros_acima_de_090': sum(1 for l in errados if (l['confianca'] or 0) >= 0.90),
                 'estado_medio': round(sum(l['tamanho'] for l in grupo) / len(grupo)),
                 'dominante': dominante[0] if dominante else None}
        resultado['R12'][nome] = bloco
        print(f"   {nome:14} {bloco['estado_medio']:>10,} "
              f"{(f'{bloco[chr(97)+chr(99)+chr(117)+chr(114)+chr(97)+chr(99)+chr(105)+chr(97)]:.1%}' if bloco['acuracia'] is not None else '—'):>9} "
              f"{str(bloco['conf_media']):>11} {bloco['erros_acima_de_090']:>10} "
              f"{bloco['sem_resposta']:>7}  {bloco['dominante']}")

    print('\n== R13: texto sem pedido nenhum — o que ele responde?')
    for nome in ('sem-saida', 'com-saida'):
        grupo = por.get(nome, [])
        validas = [l for l in grupo if l['escolha']]
        contagem = Counter(l['escolha'] for l in validas)
        conf_alta = sum(1 for l in validas if (l['confianca'] or 0) >= 0.90)
        acertos = sum(1 for l in validas if l['alvo'] and l['escolha'] == l['alvo'])
        resultado['R13'][nome] = {'n': len(validas), 'respostas': contagem.most_common(),
                                  'com_confianca_acima_de_090': conf_alta,
                                  'acertos_da_saida': acertos,
                                  'confianca_media': round(sum(l['confianca'] or 0 for l in validas) / len(validas), 4) if validas else None,
                                  'detalhe': [{'id': l['case_id'], 'deu': l['escolha'],
                                               'conf': l['confianca']} for l in grupo]}
        bloco = resultado['R13'][nome]
        print(f"   {nome:10} respostas {bloco['respostas']}")
        print(f"              confiança média {bloco['confianca_media']} | "
              f"com confiança ≥ 0,90: {conf_alta}/{len(validas)}"
              + (f" | escolheu a saída em {acertos}/{len(validas)}" if nome == 'com-saida' else ''))

    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
