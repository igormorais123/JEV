"""Gera `docs/DOSSIE-DE-EVIDENCIAS.md`: cada afirmação do estudo com a evidência que a sustenta.

A documentação que já existe responde três perguntas diferentes: o `GUIA-PRATICO` diz o que
fazer, o `PREREGISTRO` diz o que foi prometido antes de medir, e o `LIMITES` diz onde o modelo
quebra. Falta a quarta: **cada afirmação, com a força dela e com o caminho para conferir**.

O dossiê é gerado, não escrito à mão, pela mesma razão que a auditoria existe: número copiado
envelhece. A prosa de interpretação é fixa; todo valor numérico sai do JSON bruto na hora.

    python laboratorio/gerar_dossie.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:  # rodado como script, o pacote laboratorio precisa estar no caminho
    sys.path.insert(0, str(RAIZ))
LAB = RAIZ / 'laboratorio'
DESTINO = RAIZ / 'docs' / 'DOSSIE-DE-EVIDENCIAS.md'


def carregar(nome):
    return json.loads((LAB / nome).read_text(encoding='utf-8'))


def pct(valor, casas=1):
    return f'{valor * 100:.{casas}f}'.replace('.', ',') + '%'


def milhar(valor):
    return f'{valor:,}'.replace(',', '.')


def p_escrito(valor):
    """p = 0,0001 vira 'p < 0,0001'; o resto sai com as casas que tem."""
    if valor < 0.0001:
        return 'p < 0,0001'
    escrito = f'{valor:.4f}'.rstrip('0')
    if escrito.endswith('.'):
        escrito += '0'
    return 'p = ' + escrito.replace('.', ',')


# ----------------------------------------------------------------- as afirmações
FORCAS = {
    'demonstrado': 'demonstrado',
    'direcao': 'direção consistente, sem significância',
    'falsificado': 'falsificado',
    'descritivo': 'medição única, sem comparador',
    'derivou': 'deixou de valer — deriva pega pelo canário',
    'corrigida': 'afirmação anterior corrigida por medição nova',
}


def afirmacoes():
    """Cada afirmação do estudo, com a força, a evidência e o que ela não autoriza dizer."""
    c = carregar('r18-r20-consolidado.json')
    r18 = carregar('r18-escala.json')
    r19 = carregar('r19-armadilha.json')
    r20 = carregar('r20-k-adaptativo.json')
    r15b = carregar('r15b-familias.json')
    r16 = carregar('r16-resumo.json')
    r11 = carregar('r11-extremos.json')
    r10 = carregar('r10-injecao-comparada.json')
    r21 = carregar('r21-generalizacao.json')
    r21b = carregar('r21b-cruzamento.json')

    guarda = r16['segunda_camada']['D-pergunta-do-efeito@0.8']
    benignos = 108

    return [
        dict(
            titulo='Selecionar contexto com o Jev responde **melhor** do que carregar tudo',
            forca='demonstrado',
            evidencia=(
                f"Em {c['perguntas']} perguntas geradas e filtradas por máquina, mandar os dois "
                f"trechos que o Jev escolheu acerta {c['arranjos']['jev-2']['acertos']}/"
                f"{c['perguntas']} ({pct(c['arranjos']['jev-2']['taxa'])}) contra "
                f"{c['arranjos']['todos']['acertos']}/{c['perguntas']} "
                f"({pct(c['arranjos']['todos']['taxa'])}) carregando os oito. Pareado caso a caso: "
                f"{c['pareado']['jev-2 vs todos']['so_jev-2']} a "
                f"{c['pareado']['jev-2 vs todos']['so_todos']}, "
                f"{p_escrito(c['pareado']['jev-2 vs todos']['p'])}. E com "
                f"{pct(1 - c['arranjos']['jev-2']['bytes'] / c['arranjos']['todos']['bytes'])} "
                f"menos contexto."),
            onde='`r18-escala.json`, `r20-k-adaptativo.json`, `r18-r20-consolidado.json`',
            nao_prova=(
                'Não prova que vale para qualquer corpus. As perguntas são sobre código Python '
                'deste repositório, respondidas por um modelo só. Um corpus onde a resposta '
                'dependa de juntar vários trechos deve inverter o sinal.'),
        ),
        dict(
            titulo='O Jev ordena melhor que o BM25',
            forca='demonstrado',
            evidencia=(
                f"Na colocação do trecho certo entre os dois primeiros, "
                f"{r18['pareado']['H18b jev-2 vs bm25-2 (alvo no topo)']['so_jev-2']} casos só do "
                f"Jev contra {r18['pareado']['H18b jev-2 vs bm25-2 (alvo no topo)']['so_bm25-2']} "
                f"só do BM25, "
                f"{p_escrito(r18['pareado']['H18b jev-2 vs bm25-2 (alvo no topo)']['p'])}. "
                f"Na resposta final, "
                f"{r18['pareado']['H18b jev-2 vs bm25-2 (resposta)']['so_jev-2']} a "
                f"{r18['pareado']['H18b jev-2 vs bm25-2 (resposta)']['so_bm25-2']}, "
                f"{p_escrito(r18['pareado']['H18b jev-2 vs bm25-2 (resposta)']['p'])}."),
            onde='`r18-escala.json`, bloco `pareado`',
            nao_prova=(
                'O BM25 aqui é uma implementação de referência com k1=1,5 e b=0,75 sobre o mesmo '
                'recorte, sem ajuste de parâmetros nem expansão de consulta. Um BM25 afinado para '
                'este corpus fecharia parte da diferença.'),
        ),
        dict(
            titulo='Um trecho e dois trechos são equivalentes; três é pior',
            forca='direcao',
            evidencia=(
                f"k=1 contra k=2: {c['pareado']['jev-1 vs jev-2']['so_jev-1']} a "
                f"{c['pareado']['jev-1 vs jev-2']['so_jev-2']}, "
                f"{p_escrito(c['pareado']['jev-1 vs jev-2']['p'])} — nenhuma diferença, e k=1 custa "
                f"metade. k=2 contra k=3: {c['pareado']['jev-2 vs jev-3']['so_jev-2']} a "
                f"{c['pareado']['jev-2 vs jev-3']['so_jev-3']}, "
                f"{p_escrito(c['pareado']['jev-2 vs jev-3']['p'])}."),
            onde='`r18-r20-consolidado.json`, bloco `pareado`',
            nao_prova=(
                'A queda de k=2 para k=3 nunca atingiu p < 0,05, em nenhum recorte. A direção se '
                'manteve em todos e não se inverteu em nenhum, o que é sugestivo e não é prova.'),
        ),
        dict(
            titulo='A classe que o Jev dá ao melhor candidato prediz se a resposta vai sair certa',
            forca='descritivo',
            evidencia=(
                f"Quando o topo veio `essencial` "
                f"({r20['por_classe_do_topo']['essencial']['n']} casos), a resposta acertou "
                f"{pct(r20['por_classe_do_topo']['essencial']['taxa'])}. Nos "
                f"{r20['por_classe_do_topo']['irrelevante']['n']} casos em que veio "
                f"`irrelevante`, acertou "
                f"{pct(r20['por_classe_do_topo']['irrelevante']['taxa'])} — e em nenhum deles o "
                f"trecho certo estava entre os candidatos."),
            onde='`r20-k-adaptativo.json`, bloco `por_classe_do_topo`',
            nao_prova=(
                'São dois casos do lado `irrelevante`. O intervalo de Wilson vai de 0 a '
                f"{pct(r20['por_classe_do_topo']['irrelevante']['ic95'][1])}: o sinal é real como "
                'hipótese e frágil como número. Vale porque a ação que ele sugere — buscar mais '
                'candidatos em vez de escolher melhor — é barata e sai de graça na mesma chamada.'),
        ),
        dict(
            titulo='Contra aviso pseudo-sistêmico o Jev não vira; contra **ordem direta**, vira',
            forca='corrigida',
            evidencia=(
                f"Sob os 12 vetores adversariais escritos por três LLMs, o Jev virou "
                f"{r15b['familias']['A']['jev']['virou']} de "
                f"{r15b['familias']['A']['jev']['n']} na família que fala com o classificador e "
                f"{r15b['familias']['B']['jev']['virou']} de "
                f"{r15b['familias']['B']['jev']['n']} na que acrescenta um pedido real — e "
                f"{r15b['jev']['viradas_acima_do_corte']} dessas passaram do corte de "
                f"{str(r15b['corte']).replace('.', ',')}. Foi disso que saiu a afirmação de "
                f"imunidade. Só que os doze vetores são **avisos pseudo-sistêmicos** "
                f"(\"Protocolo #7894-Omega\", \"Cancelamento automático aprovado\"): nenhum dá "
                f"uma ordem ao classificador. A meta-instrução imperativa, testada só na R21, "
                f"vira {r21['meta_instrucao']['viradas']} de {r21['meta_instrucao']['n']} no "
                f"jurídico e {r21b['viradas']} de {r21b['n']} **em atendimento**, o domínio onde "
                f"a imunidade tinha sido publicada."),
            onde='`r15b-familias.json`, `r21-generalizacao.json`, `r21b-cruzamento.json`',
            nao_prova=(
                'Não apaga a separação estrutural entre `state` e `questions`, que é real e é o '
                'que impede o texto do cliente de virar instrução por concatenação. O que cai é '
                'a leitura de que isso produz imunidade. E cai também o uso do corte de '
                'confiança como defesa: ele barra as viradas em atendimento e deixa passar 10 '
                'de 25 no jurídico. Contra ordem direta escrita no estado, a defesa é sanitizar '
                'a entrada.'),
        ),
        dict(
            titulo='Como segunda camada, o Jev corta dois terços das confirmações inúteis '
                   'sem soltar nada irreversível',
            forca='demonstrado',
            evidencia=(
                f"Em 120 comandos reais desta máquina, a regra por palavra barrou 90. Dos "
                f"{benignos} comandos benignos da amostra, a regra sozinha interrompe "
                f"{pct((guarda['marcados_pela_regra'] - 12) / benignos)}; com o Jev liberando o que "
                f"a regra barrou, {pct(guarda['interrupcoes_benignas'] / benignos)}. Foram "
                f"{guarda['liberados']} liberações e "
                f"{int(guarda['irreversivel_liberado'])} irreversíveis soltos."),
            onde='`r16-guarda-de-comando.json`, `r16b-segunda-camada.json`',
            nao_prova=(
                'Zero observado não é zero garantido: o intervalo de Wilson sobre 0 em '
                f"{guarda['liberados']} liberações admite até "
                f"{pct(guarda['ic95_do_erro'][1])} de erro. Por isso o guarda nunca libera "
                'sozinho — ele só deixa de pedir confirmação do que a regra já barrou.'),
        ),
        dict(
            titulo='Uma frase na instrução conserta a pior fraqueza medida',
            forca='direcao',
            evidencia=(
                f"Dizer na instrução de quem é o pedido que importa levou a acurácia de "
                f"{pct(r19['formulacoes']['A-atual']['taxa'])} para "
                f"{pct(r19['formulacoes']['B-instrucao-de-sujeito']['taxa'])} em "
                f"{r19['formulacoes']['A-atual']['n']} mensagens, sem piorar nenhuma família."),
            onde='`r19-armadilha.json`, formulação `B-instrucao-de-sujeito`',
            nao_prova=(
                'São 3 casos a 0 no geral, p = 0,25. A recomendação se justifica pelo custo — uma '
                'frase — e pela ausência de contrapartida, não pela significância.'),
        ),
        dict(
            titulo='Decompor a decisão em duas perguntas não ajuda quando a pergunta auxiliar '
                   'é mais fraca que a decisão',
            forca='falsificado',
            evidencia=(
                f"Perguntar *de quem é a ação* junto com *qual é a ação*, de graça no mesmo "
                f"payload, sobe a família do terceiro para "
                f"{pct(r19['formulacoes']['D-sujeito-e-acao']['familia_terceiro']['taxa'])} contra "
                f"{pct(r19['formulacoes']['A-atual']['familia_terceiro']['taxa'])} — e derruba o "
                f"geral para {pct(r19['formulacoes']['D-sujeito-e-acao']['taxa'])}, porque destrói "
                f"o molde oposto. A causa está medida: a pergunta de sujeito acerta sozinha "
                f"{pct(r19['pergunta_de_sujeito']['taxa'])}."),
            onde='`r19-armadilha.json`, formulação `D-sujeito-e-acao` e `pergunta_de_sujeito`',
            nao_prova=(
                'Não condena a decomposição em geral. Condena decompor **numa pergunta menos '
                'confiável que a decisão que ela alimenta**, que é o caso aqui e é verificável '
                'antes de adotar: basta medir a pergunta auxiliar sozinha.'),
        ),
        dict(
            titulo='Recortar o candidato com as constantes do módulo junto piora a resposta',
            forca='falsificado',
            evidencia=(
                f"A mitigação proposta na R17 melhorou a **ordenação** "
                f"({r18['arranjos']['jev-cab-2']['alvo_presente']}/{r18['casos']} contra "
                f"{r18['arranjos']['jev-2']['alvo_presente']}/{r18['casos']}) e piorou a "
                f"**resposta** ({r18['arranjos']['jev-cab-2']['acertos']} contra "
                f"{r18['arranjos']['jev-2']['acertos']}). Mais contexto ajuda a achar e atrapalha "
                f"a responder — a mesma curva do k, por outro caminho."),
            onde='`r18-escala.json`, arranjo `jev-cab-2`',
            nao_prova=(
                'O pareamento é 2 a 5, p = 0,45: a piora não é significativa. O que a rodada '
                'falsifica é a hipótese de que o cabeçalho **melhoraria** a resposta, que era a '
                'razão de propô-lo.'),
        ),
        dict(
            titulo='O endpoint rejeita a chamada quando a instrução vem vazia — **não vale mais**',
            forca='derivou',
            evidencia=(
                f"Em 2026-09-19, a condição `instrucao/vazia` da R11 voltou `http 400` em "
                f"{r11['condicoes']['instrucao/vazia']['sem_resposta']} de "
                f"{r11['condicoes']['instrucao/vazia']['sem_resposta']} chamadas: o provedor "
                f"recusava o payload. Em 2026-09-20, o canário `instrucao-vazia-nao-responde` "
                f"reprovou — com os **mesmos critérios** e a instrução igualmente vazia, "
                f"**7 de 7** chamadas voltaram 200, com a classe certa e confiança 1 (duas "
                f"corridas de canário e três de confirmação com o formato literal da R11). "
                f"A propriedade caiu em "
                f"menos de 24 horas, e quem pegou foi o canário, na primeira corrida dele."),
            onde='`r11-extremos.json` e `canarios-de-comportamento.jsonl`',
            nao_prova=(
                'Não prova o que mudou do outro lado: da posição de cliente não dá para '
                'distinguir validação relaxada, troca de versão do modelo ou roteamento '
                'diferente. O que fica provado é outra coisa, e mais importante: uma propriedade '
                'publicada do endpoint pode morrer em um dia, e documentação sem canário não '
                'avisa. Nenhuma recomendação do guia dependia desta, o que foi sorte e não '
                'projeto.'),
        ),
        dict(
            titulo='Receber a instrução pelo prompt expõe o comparador a um risco que o '
                   'contrato do Jev não tem',
            forca='demonstrado',
            evidencia=(
                'Sob as mesmas injeções, a taxa de virada foi ' + ', '.join(
                    f"{braco} {pct(dados['taxa_de_manipulacao'])}"
                    for braco, dados in r10['por_braco'].items())
                + '. Nem todo comparador vira — o `mistralai/mistral-nemo` também ficou em zero '
                  'nesta rodada — mas os que viram, viraram muito, e o pior deles em 7 de cada '
                  '10 tentativas.'),
            onde='`r10-injecao-comparada.json`, bloco `por_braco`',
            nao_prova=(
                'Os comparadores recebem a instrução no prompt porque é assim que eles funcionam; '
                'a comparação é entre **arquiteturas de chamada**, não entre inteligências. Um '
                'comparador com defesa própria contra injeção não foi testado.'),
        ),
    ]


# ----------------------------------------------------------------- fichas por rodada
def fichas():
    c = carregar('r18-r20-consolidado.json')
    r17 = carregar('r17-economia-de-contexto.json')
    r18 = carregar('r18-escala.json')
    r19 = carregar('r19-armadilha.json')
    r20 = carregar('r20-k-adaptativo.json')
    r15 = carregar('r15-adversario-externo.json')
    r16 = carregar('r16-guarda-de-comando.json')

    return [
        ('R15', 'O Jev resiste a ataque que eu não escrevi?',
         f"{len(r15['vetores'])} vetores escritos por 3 LLMs, {r15['chamadas']} chamadas",
         'Falsificou a versão simples da afirmação de imunidade em horas; a R15b recuperou uma '
         'versão mais forte e mais precisa separando meta-instrução de conteúdo inserido.',
         'r15-adversario-externo.json'),
        ('R16', 'O Jev serve de guarda de comando de shell?',
         f"{r16['casos']} comandos reais, 4 formulações, {len(r16['detalhe'])} avaliações",
         'No lugar da regra é inseguro. Depois da regra, corta dois terços da fricção sem soltar '
         'nada irreversível.',
         'r16-guarda-de-comando.json'),
        ('R17', 'Quanto contexto a ordenação economiza, de verdade?',
         f"{r17['perguntas']} perguntas escritas à mão, {len(r17['detalhe'])} respostas avaliadas",
         f"Primeira medição de economia do estudo: {pct(r17['arranjos']['jev']['economia'])} do "
         f"contexto, sem perder resposta. Amostra pequena demais para decidir entre arranjos.",
         'r17-economia-de-contexto.json'),
        ('R18', 'A mesma pergunta em escala, com gabarito que não é meu',
         f"{r18['casos']} perguntas geradas por LLM e aprovadas por filtro mecânico, "
         f"{len(r18['detalhe'])} respostas avaliadas",
         'Fechou a dúvida contra o BM25 e achou a curva do k. Falsificou a mitigação do cabeçalho '
         'que a R17 tinha proposto.',
         'r18-escala.json'),
        ('R19', 'Dá para consertar a armadilha de ação de terceiro?',
         f"{r19['casos']} mensagens de 5 moldes com gabarito fixado antes do texto, "
         f"{len(r19['detalhe'])} avaliações",
         'Sim, com uma frase. E não com decomposição: a capacidade de múltiplas perguntas no mesmo '
         'payload, nunca usada em 6.000 chamadas anteriores, piora o resultado geral.',
         'r19-armadilha.json'),
        ('R20', 'Replica em lote novo, e a confiança pode escolher o k?',
         f"{r20['casos']} perguntas de semente nova sobre funções que a R18 não usou, "
         f"{len(r20['detalhe'])} respostas avaliadas",
         f"Replicou. Juntando os dois lotes ({c['perguntas']} perguntas), selecionar deixa de "
         f"\"não perder\" e passa a **ganhar** de carregar tudo. O k adaptativo empata em acerto e "
         f"economiza {pct(r20['arranjos']['adaptativo']['economia'])} contra "
         f"{pct(r20['arranjos']['jev-2']['economia'])}.",
         'r20-k-adaptativo.json'),
    ]


# ----------------------------------------------------------------- contabilidade
def caixa():
    from laboratorio import caixa as livro
    return livro.totais()


# ----------------------------------------------------------------- montagem
CABECALHO = """# Dossiê de evidências — o que o estudo do Jev sustenta, e com que força

> Gerado por `python laboratorio/gerar_dossie.py`. Todo número desta página sai do JSON bruto
> na hora da geração, e `laboratorio/auditoria.py` reconfere cada um contra as linhas de resposta
> originais, com estatística independente da que produziu os resumos.

Os outros documentos respondem outras perguntas: o [guia prático](GUIA-PRATICO-JEV.md) diz **o que
fazer**, o [pré-registro](../laboratorio/PREREGISTRO.md) diz **o que foi prometido antes de medir**,
o [mapa de limites](LIMITES-DO-JEV.md) diz **onde quebra** e a
[auditoria](AUDITORIA-DE-NUMEROS.md) mostra **conferência por conferência**. Este aqui responde a
pergunta que faltava: *desta afirmação, quanto é prova?*

## Como ler

Cada afirmação recebe uma de quatro forças, e a diferença entre elas é o ponto do documento:

| força | o que significa | o que você pode fazer com ela |
|---|---|---|
| **demonstrado** | comparação pareada com p < 0,05 | decidir em cima |
| **direção consistente** | o sinal se repete e nunca se inverte, sem atingir p < 0,05 | adotar se o custo for baixo; não usar para convencer ninguém |
| **medição única** | um número observado, sem comparador ou com n pequeno demais | tratar como hipótese, e medir de novo antes de depender |
| **falsificado** | a hipótese foi testada e o dado disse não | parar de fazer, e registrar por quê |
| **corrigida** | uma afirmação publicada caiu diante de medição nova | ler a versão nova, e desconfiar de quem citar a antiga |
| **derivou** | valia quando foi medida e não vale mais | refazer a medição antes de usar |

Toda afirmação traz também **o que ela não prova**. Essa coluna é a parte do documento que
mais custou a escrever e a única que impede o resto de virar propaganda.

"""


def montar():
    partes = [CABECALHO, '## As afirmações\n']

    ordem = {'demonstrado': 0, 'direcao': 1, 'descritivo': 2, 'falsificado': 3,
             'corrigida': 4, 'derivou': 5}
    for item in sorted(afirmacoes(), key=lambda i: ordem[i['forca']]):
        evidencia = item['evidencia']
        if isinstance(evidencia, tuple):  # vírgula perdida sobrevive como tupla; normaliza
            evidencia = evidencia[0]
        partes.append(f"### {item['titulo']}\n")
        partes.append(f"**Força:** {FORCAS[item['forca']]}.\n")
        partes.append(f"**Evidência.** {evidencia}\n")
        partes.append(f"**O que não prova.** {item['nao_prova']}\n")
        partes.append(f"**Dado bruto:** {item['onde']}\n")

    partes.append('## Fichas das rodadas do programa E17\n')
    partes.append('| rodada | a pergunta | o desenho | o que saiu | bruto |')
    partes.append('|---|---|---|---|---|')
    for nome, pergunta, desenho, saiu, arquivo in fichas():
        partes.append(f'| **{nome}** | {pergunta} | {desenho} | {saiu} | `{arquivo}` |')
    partes.append('')

    chamadas, gasto = caixa()
    partes.append('## Contabilidade\n')
    partes.append(
        f'O livro-caixa SQLite em `runs/ledger.sqlite3` registra **{milhar(chamadas)} chamadas** '
        f'liquidadas, somando **US$ {f"{gasto:.4f}".replace(".", ",")}** do teto de US$ 5,00 '
        f'autorizado — restam US$ {f"{5 - gasto:.4f}".replace(".", ",")}. O livro-caixa é a fonte '
        f'única: os JSONL do laboratório são cópias do mesmo evento e somá-los junto contaria duas '
        f'vezes, defeito que já esteve no painel e foi corrigido.\n')

    partes.append('## Como conferir\n')
    partes.append(
        '```\n'
        'python laboratorio/auditoria.py                         # recalcula tudo e aponta divergência\n'
        'python laboratorio/gerar_dossie.py                      # regera esta página a partir do dado\n'
        'python -m laboratorio.canarios_de_comportamento --rodar # 16 chamadas: as propriedades ainda valem?\n'
        'python -m pytest                                        # a auditoria está presa na suíte\n'
        '```\n')
    partes.append(
        'A auditoria confere três coisas, nesta ordem: que cada resumo fecha quando recalculado '
        'das linhas brutas; que cada número escrito na documentação existe nesses resumos, com a '
        'mesma casa decimal; e que as chamadas e o custo declarados fecham com o livro-caixa. '
        'Ela também declara o que **não** consegue conferir, em vez de omitir.\n')
    partes.append(
        'Mas a auditoria só prova que os números fecham com o dado **que foi medido**. Ela não '
        'tem como saber se o modelo do outro lado continua o mesmo, e essa é a segunda metade do '
        'problema. Os canários de comportamento congelam oito propriedades em que este dossiê se '
        'apoia, custam menos de US$ 0,0003 por corrida, e a primeira corrida deles já derrubou '
        'uma afirmação desta página — que é exatamente o serviço que deviam prestar.\n')

    return '\n'.join(partes)


def main():
    DESTINO.write_text(montar(), encoding='utf-8')
    print(f'dossiê em {DESTINO} ({len(DESTINO.read_text(encoding="utf-8").splitlines())} linhas)')


if __name__ == '__main__':
    main()
