"""Gera `docs/CEM-PERGUNTAS-ESTRATEGICAS.md` a partir do registro e das respostas.

Página gerada, nunca escrita à mão, pela razão de sempre: número copiado envelhece. A prosa de
leitura é fixa; pergunta, decisão informada, gatilho de virada, resposta e parâmetros declarados
saem do registro e do módulo de respostas na hora da geração.

    python -m laboratorio.q100.relatorio
"""

from __future__ import annotations

import collections
from pathlib import Path

from laboratorio.q100 import registro, respostas

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / 'docs' / 'CEM-PERGUNTAS-ESTRATEGICAS.md'

MARCA_CONFIANCA = {'alta': 'alta', 'media': 'média', 'baixa': 'baixa'}

NOME_DA_FONTE = {'dado': 'dado medido', 'conta': 'conta declarada', 'medicao': 'coleta nova'}

# As respostas que mudam uma decisão já tomada no guia, e o que elas mudam. Esta é a única parte
# da página escrita à mão: exige julgamento, e julgamento não se gera a partir de tabela.
LEITURA = {
    'Q042': ('A mitigação que o guia recomendava sem prova agora tem prova, e ela é forte. Uma '
             'expressão regular de oito padrões, aplicada ao texto antes de ele virar `state`, '
             'derruba a virada por ordem direta de 35,9% para 1,2% — pareado, 27 a 0, '
             'p < 0,0001. Custa zero chamada e não machuca texto limpo. **Passa de sugestão a '
             'requisito de integração.**'),
    'Q044': ('O sentinela é a descoberta operacional mais barata do estudo: uma segunda pergunta '
             'no mesmo payload custa **nada** — o preço é por token de entrada, e o estado já '
             'foi enviado — e detecta 100% das tentativas de ordem direta, calando-se em 97,6% '
             'do texto limpo. Quem precisa de trilha de auditoria de ataque tem como tê-la de '
             'graça. O que o sentinela não faz é impedir a virada, então ele acompanha a '
             'sanitização em vez de substituí-la.'),
    'Q023': ('Esta resposta foi corrigida, e a correção é mais útil que a versão original. A '
             'primeira dizia que o corte de confiança degradava 13,5% nas condições extremas; '
             'o número somava a diluição **retratada** da R11, e 46 dos 52 erros acima de 0,99 '
             'eram o truncamento do laboratório, não o modelo. Sem a condição retratada, os '
             'extremos ficam em 1,29% e a rodada que mais escapa ao corte é a armadilha de '
             'sujeito (3,43%). A ressalva que sobrevive muda de endereço: não é a taxonomia '
             'grande nem o texto degradado que enganam o corte — é o pedido atribuído à pessoa '
             'errada. A frase de sujeito do guia é a mitigação, e ela custa uma linha.'),
    'Q036': ('Dois modos de falha sistemáticos, e os dois são de desenho, não do modelo. Texto '
             'sem pedido nenhum, num contrato sem classe de escape, erra 10 de 10 com confiança '
             'média de 0,987 — o modelo não tem como dizer "nada disso", então ele escolhe. E '
             'ordem direta ao classificador vira o resultado. **Classe de escape obrigatória e '
             'sanitização obrigatória** resolvem os dois, e nenhum dos dois custa chamada.'),
    'Q073': ('A operação precisa de repescagem, não de tolerância a erro. 2,7% das tentativas '
             'falharam, e a maioria é erro do provedor ou estouro do timeout de 45 s — coisas '
             'que uma segunda tentativa resolve. O que não pode acontecer é falha virar classe '
             'padrão: uma chamada que não voltou não é "informação", é ausência de decisão.'),
    'Q096': ('O limite deste trabalho não é orçamento. Gastou-se 10,6% do teto autorizado, e o '
             'que resta compra mais de nove vezes tudo que já foi feito. O que falta é **dado '
             'real com gabarito humano** — duzentas mensagens anotadas por duas pessoas fecham '
             'de uma vez a maior ressalva do estudo, e custam tempo de gente, não dinheiro.'),
}


def montar():
    itens = []
    for pergunta in registro.PERGUNTAS:
        funcao = respostas.RESPOSTAS.get(pergunta['id'])
        if funcao is None:
            raise SystemExit(f'{pergunta["id"]} não tem resposta registrada')
        itens.append({**pergunta, **funcao()})

    por_fonte = collections.Counter(i['fonte'] for i in itens)
    por_confianca = collections.Counter(i['confianca'] for i in itens)
    com_parametro = [i for i in itens if i['parametros']]
    por_familia = collections.defaultdict(list)
    for item in itens:
        por_familia[item['familia']].append(item)

    partes = [
        '# Cem perguntas estratégicas sobre o Jev, e o que o dado responde',
        '',
        '> Gerado por `python -m laboratorio.q100.relatorio`. O registro das perguntas está em',
        '> `laboratorio/q100/registro.py` e foi commitado **antes** de qualquer resposta ser',
        '> escrita; as respostas estão em `laboratorio/q100/respostas.py` e calculam cada número',
        '> na hora, a partir dos artefatos e do livro-caixa. Nenhum número desta página foi',
        '> digitado à mão.',
        '',
        f'**{por_fonte["dado"]} respondidas por dado medido, {por_fonte["conta"]} por conta '
        f'sobre o medido, {por_fonte["medicao"]} por coleta nova.** '
        f'Confiança: {por_confianca["alta"]} alta, {por_confianca["media"]} média, '
        f'{por_confianca["baixa"]} baixa.',
        '',
        '## O que separa esta página das cem hipóteses',
        '',
        'As cem hipóteses perguntavam **o que o modelo faz**, e a resposta era sustentada ou',
        'falsificada. Estas cem perguntam **o que fazer com ele**, e a resposta termina numa',
        'decisão. É por isso que cada pergunta carrega, além do enunciado, a decisão concreta',
        'que ela informa e o que teria de ser verdade para essa decisão virar. Pergunta',
        'estratégica que não muda decisão nenhuma não é estratégia: é curiosidade cara, e as',
        'que não passaram nesse teste ficaram de fora do registro.',
        '',
        'A honestidade desta página depende de uma distinção que ela carrega em toda entrada.',
        '`dado medido` é contagem sobre o que foi observado. `conta declarada` é aritmética',
        'sobre o medido, usando parâmetros que **não** foram medidos — preço de mercado de um',
        'modelo caro, custo-hora de revisão, volume mensal. Esses parâmetros estão listados um',
        'a um na seção seguinte, com valor e origem, e as respostas que dependem deles vêm',
        'marcadas com confiança `baixa` de propósito. Conta com parâmetro escondido é opinião',
        'com aparência de número.',
        '',
        '## Os parâmetros que não foram medidos',
        '',
        f'{len(com_parametro)} das cem respostas dependem de pelo menos um destes. Trocar',
        'qualquer um deles muda o número da resposta, e as respostas dizem em que direção.',
        '',
        '| parâmetro | valor | o que é | usado em |',
        '|---|---|---|---|',
    ]
    for nome, (valor, o_que_e) in respostas.PARAMETROS.items():
        usos = sum(1 for i in itens if nome in i['parametros'])
        if not usos:
            # O preço do próprio Jev mora na mesma tabela por conveniência do código, mas ele é
            # verificado no provedor e entra nas contas pelo livro-caixa, não como suposição.
            continue
        casas = 3 if 0 < valor % 1 < 0.1 else (2 if valor % 1 else 0)
        valor_escrito = respostas.mil(valor, casas).replace(respostas.MILHAR, '.')
        partes.append(f'| `{nome}` | {valor_escrito} | {o_que_e} '
                      f'| {usos} {"resposta" if usos == 1 else "respostas"} |')
    partes.append('')

    partes.append('## As respostas que mudam uma decisão já tomada')
    partes.append('')
    for identificador, texto in LEITURA.items():
        item = next(i for i in itens if i['id'] == identificador)
        partes.append(f'### {identificador} — {item["pergunta"]}')
        partes.append('')
        partes.append(f'**Decide:** {item["decisao"]}  ')
        partes.append(f'**Responde:** {item["resposta"]}')
        partes.append('')
        partes.append(texto)
        partes.append('')

    partes.append('## As cem, por família')
    partes.append('')
    for familia, nome in registro.FAMILIAS.items():
        do_grupo = por_familia[familia]
        conta = collections.Counter(i['fonte'] for i in do_grupo)
        resumo = ', '.join(f'{v} por {NOME_DA_FONTE[k]}' for k, v in sorted(conta.items()))
        partes.append(f'### {familia} · {nome}')
        partes.append('')
        partes.append(f'*{len(do_grupo)} perguntas: {resumo}.*')
        partes.append('')
        for item in do_grupo:
            partes.append(f'**{item["id"]} — {item["pergunta"]}**')
            partes.append('')
            partes.append(item['resposta'])
            partes.append('')
            rodape = (f'Decide {item["decisao"]}. Fonte: {NOME_DA_FONTE[item["fonte"]]}; '
                      f'confiança {MARCA_CONFIANCA[item["confianca"]]}. '
                      f'Vira se {item["vira_se"]}.')
            if item['parametros']:
                rodape += (' Depende de: '
                           + ', '.join(f'`{n}`' for n in item['parametros']) + '.')
            partes.append(f'*{rodape}*')
            partes.append('')

    partes.append('## Como refazer')
    partes.append('')
    partes.append('```')
    partes.append('python -m laboratorio.q100.relatorio    # regera esta página')
    partes.append('python laboratorio/auditoria.py         # confere cada número publicado')
    partes.append('```')
    partes.append('')
    return '\n'.join(partes) + '\n'


def main():
    DESTINO.write_text(montar(), encoding='utf-8')
    linhas = len(DESTINO.read_text(encoding='utf-8').splitlines())
    print(f'{DESTINO} ({linhas} linhas)')


if __name__ == '__main__':
    main()
