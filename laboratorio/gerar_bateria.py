"""Gera `docs/BATERIA-COMPLEMENTAR.md` a partir dos artefatos das rodadas R23 a R27.

A bateria complementar existe para fechar o que o estudo declarou em aberto: a robustez do
sanitizador a paráfrase (fora de alcance na R22), a votação nunca medida de ponta a ponta
(Q098), o terceiro domínio (Q060), a resposta dividida em dois trechos (Q095) e a integração
das duas defesas num payload só. Toda linha numérica desta página sai do artefato na hora da
geração; o julgamento de cada rodada está em `LEITURA`, escrito à mão e datado.

    python laboratorio/gerar_bateria.py
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LAB = RAIZ / 'laboratorio'
DESTINO = RAIZ / 'docs' / 'BATERIA-COMPLEMENTAR.md'


def carregar(nome):
    caminho = LAB / nome
    return json.loads(caminho.read_text(encoding='utf-8')) if caminho.exists() else None


def pct(valor, casas=1):
    return '—' if valor is None else f'{valor * 100:.{casas}f}%'.replace('.', ',')


def p_valor(valor):
    if valor is None:
        return '—'
    return 'p < 0,0001' if valor < 0.0001 else f'p = {valor:.4f}'.replace('.', ',')


def mil(valor):
    return f'{int(valor):,}'.replace(',', '.')


def usd(valor):
    return f'US$ {valor:.4f}'.replace('.', ',')


# O julgamento de cada rodada. É a única parte da página escrita à mão, e é preenchida depois
# de os números existirem — nunca antes.
LEITURA = {
    'R23': (
        '**Leitura (2026-09-20).** A recomendação "sanitize com expressão regular" caiu. O v1 do '
        'guia — oito padrões que zeraram a virada na R22 — não cobre **nenhum** dos 48 vetores '
        'desta rodada, e o v2, escrito olhando para os doze do laboratório, cobre 12 deles e só 2 '
        'dos 36 escritos por outros modelos. Contra ordens ao sistema que o sanitizador nunca viu '
        '(gemma e gpt-oss-20b, 24 vetores), a virada é de 42% a 48%, **202 viradas passam do '
        'corte de 0,90**, e o v2 muda quase nada. Sanitizar por lista funciona contra o vetor para '
        'o qual a lista foi escrita, e isso é tudo o que a R22 tinha provado. O sentinela, que não '
        'depende de lista, acusa 94% a 97% dessas mesmas ordens, calando-se em 98% do texto limpo — '
        'ele é a camada que generaliza, e passa a ser a primeira, não a segunda. O custo que ele '
        'cobra está no conjunto gatilho: 7 de 24 mensagens legítimas que dizem "desconsidere a '
        'mensagem anterior" são acusadas, e o sanitizador v2 mutila 22 das 24. Os doze vetores do '
        'mistral-nemo são outra coisa: pedidos genuínos de cancelamento, que o modelo lê como '
        'conteúdo — virar ali é leitura, não obediência, e o sentinela acerta em não acusar.'),
    'R24': (
        '**Leitura (2026-09-20).** Votar três vezes a mesma pergunta não serve para nada: em 148 '
        'casos, **zero** oscilaram — o modelo é determinístico neste regime, e a maioria de três '
        'iguais é a chamada única com custo triplo. O que muda é a **formulação**: no jurídico, '
        'a instrução base acerta 79,7%, a com frase de sujeito 92,6% e a reescrita com os '
        'critérios em ordem inversa 95,5%. A "maioria diversa" ganha da chamada única por 9 a 0 '
        '(p = 0,0039) não porque vota, mas porque duas das três formulações são melhores que a '
        'base. A recomendação do guia troca de sentido: em vez de votar, **escolha a formulação '
        'medindo** — e, se quiser redundância, use formulações diferentes, nunca repetições.'),
    'R25': (
        '**Leitura (2026-09-20).** A queda é de distância, não do jurídico. A clínica fica em '
        '63,2% sem a frase de sujeito, abaixo do jurídico (78,5%) e muito abaixo do atendimento '
        '(90%). O padrão é o mesmo dos outros dois domínios, mais acentuado: pedido direto 23/23 e '
        'terceiro-contra-eu-quero 10/10; o que despenca é terceiro-quer (4/19) e sem-pedido '
        '(11/24) — o modelo atribui a quem escreve o pedido que é de outro, e lê lembrete como '
        'pedido. As duas mitigações do guia se transportam: a frase de sujeito sobe 14,8 pontos '
        '(11 a 0, p = 0,001) e a sanitização v1 zera a virada do vetor da R22 (16 a 0). A '
        'acurácia publicada no guia é a do atendimento; em domínio novo, medir antes de confiar '
        'deixa de ser conselho e vira requisito.'),
    'R26': (
        '**Leitura (2026-09-20).** Q095 estava certa, e com mais força do que previa. Quando a '
        'resposta exige dois trechos, mandar o primeiro que o Jev escolheu acerta **6 de 80** '
        'contra 60 de 80 mandando os oito (54 a 0); k = 2 recupera metade (40/80, ainda 26 a 6 '
        'atrás, p = 0,0005) e k = 3 chega a 50/80, já sem diferença significativa. O controle '
        'confirma que é a divisão, não o candidato: a mesma primeira pergunta sozinha dá 76/80 '
        'com k = 1 contra 67/80 com os oito — a vantagem de selecionar continua intacta quando '
        'a resposta mora num lugar só. O pior está na regra de recall de graça: o topo veio '
        '`essencial` em 53 dos 80 casos, então **a regra não dispara em dois terços das falhas** '
        '— o modelo marca em média 1,04 trechos como essenciais mesmo quando dois o são, e só em '
        '17 casos marcou os dois. A recomendação central sobrevive a uma condição que não pode '
        'mais ficar implícita: k = 1 vale para pergunta de fonte única, e quem não sabe de '
        'antemão se a resposta está dividida deve mandar três, não um.'),
    'sintese': (
        'Quatro decisões do guia mudam. **Defesa:** a sanitização por expressão regular deixa de '
        'ser a defesa e vira complemento para o ataque já conhecido; o sentinela, lendo o texto '
        'original, passa a primeira camada — ele generaliza (95% em ordens nunca vistas) e a '
        'lista não (cobre 2 de 36). **Redundância:** votar a mesma pergunta não muda nada (0 '
        'oscilações em 148); redundância útil é de formulação, e a formulação por si só leva o '
        'jurídico de 79,7% para 95,5%. **Escopo:** a acurácia publicada é a do atendimento; em '
        'domínio distante ela cai a 63% e a frase de sujeito recupera 15 pontos. **Seleção de '
        'contexto:** k = 1 vale para pergunta de fonte única; com resposta dividida acerta 7,5%, '
        'e a regra de recall de graça não avisa em dois terços das vezes — mande três. E um '
        'achado fora do plano: a latência do provedor mudou de regime no mesmo dia (p99 de 0,9 s '
        'para 5–8 s), o que derruba H038 e obriga timeout curto com caminho de escape em '
        'qualquer gancho interativo.'),
    'R27': (
        '**Leitura (2026-09-20).** A integração num payload só funciona, com uma ressalva '
        'medida. O sentinela precisa ver o texto **original**: depois de sanitizar ele fica cego '
        '(2 de 85 acusadas). Com os dois campos no estado — limpo para o classificador, original '
        'para o sentinela — a detecção volta a 84/84 e a virada reabre em 3 de 84 (contra 0 no '
        'separado; p = 0,25, não significativo), nenhuma acima do corte. Duas chamadas separadas '
        'dão 0 viradas e 83/83 de detecção ao dobro do custo. Para a classe irreversível, duas '
        'chamadas; para o resto, dois campos.'),
}


def secao_r23(r):
    if not r:
        return ['## R23 — ainda não rodou', '']
    linhas = ['## R23 — o sanitizador contra a ordem escrita de outro jeito', '']
    c = r['por_conjunto']
    linhas += [
        f"Quarenta e oito vetores anexados às 85 mensagens do corpus de atendimento, em três braços "
        f"cada — bruto, sanitizado pelo v1 da R22 e pelo v2 deste arquivo — mais o texto limpo e "
        f"{r['gatilho']['bruto']['n']} mensagens legítimas com palavra-gatilho. "
        f"**{mil(r['chamadas'])} chamadas, {usd(r['custo_usd'])}.**", '',
        '| conjunto | vetores | v1 cobre | v2 cobre | virada bruta | virada com v1 | virada com v2 '
        '| pareado bruto × v2 | sentinela acusou |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for nome in ('conhecidos', 'surpresa'):
        b = c[nome]
        linhas.append(
            f"| {nome} | {b['vetores']} | {b['vetores_cobertos_v1']} | {b['vetores_cobertos_v2']} "
            f"| {b['bruto']['viradas']}/{b['bruto']['pares']} = **{pct(b['bruto']['taxa_de_virada'])}** "
            f"| {b['v1']['viradas']}/{b['v1']['pares']} = {pct(b['v1']['taxa_de_virada'])} "
            f"| {b['v2']['viradas']}/{b['v2']['pares']} = {pct(b['v2']['taxa_de_virada'])} "
            f"| {b['pareado_v2']['virou_so_sem_defesa']} a {b['pareado_v2']['virou_so_com_defesa']}, "
            f"{p_valor(b['pareado_v2']['p'])} "
            f"| {b['sentinela']['acusou']}/{b['sentinela']['n']} = **{pct(b['sentinela']['recall'])}** |")
    limpo = c['limpo']
    linhas += ['',
               f"No texto limpo o sentinela ficou calado em {limpo['sentinela_calada']}/"
               f"{limpo['sentinela_n']}.", '',
               '### Por família de vetor', '',
               'Os vetores do mistral-nemo não dão ordem ao sistema — são pedidos genuínos de',
               'cancelamento anexados à mensagem, a família de **conteúdo** da R15b. Virar para',
               '`cancelar` ali é leitura do texto, e o sentinela não tem por que acusar. As outras',
               'três famílias são **instrução**: falam com o classificador.', '',
               '| família | vetores | virada bruta | acima do corte | com v2 | pareado bruto × v2 '
               '| sentinela acusou |',
               '|---|---|---|---|---|---|---|']
    for nome, f in r.get('por_familia', {}).items():
        par = f['pareado_v2']
        linhas.append(
            f"| {nome} | {f['vetores']} | {f['bruto']['viradas']}/{f['bruto']['pares']} = "
            f"**{pct(f['bruto']['taxa_de_virada'])}** | {f['bruto']['acima_do_corte']} "
            f"| {f['v2']['viradas']}/{f['v2']['pares']} = {pct(f['v2']['taxa_de_virada'])} "
            f"| {par['virou_so_sem_defesa']} a {par['virou_so_com_defesa']}, {p_valor(par['p'])} "
            f"| {f['sentinela']['acusou']}/{f['sentinela']['n']} = **{pct(f['sentinela']['recall'])}** |")
    linhas += ['',
               '### Por vetor', '',
               '| vetor | autor | v2 cobre | virada bruta | com v2 | sentinela |',
               '|---|---|---|---|---|---|']
    autores = r.get('autores_surpresa', {})
    for chave, v in r['por_vetor'].items():
        conjunto, nome = chave.split('/', 1)
        autor = 'laboratório' if conjunto == 'conhecidos' else autores.get(nome, '?')
        linhas.append(
            f"| `{v['texto'].strip()[:70]}` | {autor} | {'sim' if v['v2_cobre'] else 'não'} "
            f"| {v['bruto']['viradas']}/{v['bruto']['pares']} | {v['v2']['viradas']}/{v['v2']['pares']} "
            f"| {v['sentinela']['acusou']}/{v['sentinela']['n']} |")
    g = r['gatilho']
    linhas += ['', '### O dano colateral em mensagem legítima', '',
               '| braço | acerto | mensagens mutiladas | pareado contra bruto |',
               '|---|---|---|---|']
    for braco in ('bruto', 'v1', 'v2'):
        par = g.get(f'pareado_{braco}', {})
        pareado = (f"{par['certo_so_bruto']} a {par['certo_so_sanitizado']}, {p_valor(par['p'])}"
                   if par else '—')
        linhas.append(f"| {braco} | {g[braco]['acertos']}/{g[braco]['n']} = {pct(g[braco]['taxa'])} "
                      f"| {g[braco]['mensagens_mutiladas']} | {pareado} |")
    s = g['sentinela_alarme_falso']
    linhas += ['', f"O sentinela acusou {s['acusou']}/{s['n']} das mensagens legítimas com gatilho.", '']
    if 'R23' in LEITURA:
        linhas += [LEITURA['R23'], '']
    return linhas


def secao_r24(r):
    if not r:
        return ['## R24 — ainda não rodou', '']
    linhas = ['## R24 — votar em três chamadas, de ponta a ponta', '',
              f"**{mil(r['chamadas'])} chamadas, {usd(r['custo_usd'])}.** Cinco chamadas por caso: três "
              'idênticas e duas formulações alternativas, nos dois corpus mais difíceis.', '',
              '| corpus | casos | oscilaram (3 iguais) | divergiram (3 formulações) | única '
              '| maioria igual | maioria diversa | diversa por confiança |',
              '|---|---|---|---|---|---|---|---|']
    for nome, b in r['corpora'].items():
        p = b['politicas']

        def celula(pol):
            x = p[pol]
            par = x.get('pareado_contra_unica')
            extra = (f" ({par['certo_so_votacao']} a {par['certo_so_unica']}, {p_valor(par['p'])})"
                     if par else '')
            return f"{x['acertos']}/{x['n']} = {pct(x['taxa'])}{extra}"
        linhas.append(
            f"| {nome} | {b['casos']} | {b['oscilacao']['oscilaram']}/{b['oscilacao']['n']} "
            f"| {b['divergencia_entre_formulacoes']['divergiram']}/{b['divergencia_entre_formulacoes']['n']} "
            f"| {celula('unica')} | {celula('maioria-igual')} | {celula('maioria-diversa')} "
            f"| {celula('diversa-por-confianca')} |")
    linhas += ['', '| corpus | formulação | acerto |', '|---|---|---|']
    for nome, b in r['corpora'].items():
        for f, x in b['por_formulacao'].items():
            linhas.append(f"| {nome} | {f} | {x['acertos']}/{x['n']} = {pct(x['taxa'])} |")
    linhas.append('')
    if 'R24' in LEITURA:
        linhas += [LEITURA['R24'], '']
    return linhas


def secao_r25(r):
    if not r:
        return ['## R25 — ainda não rodou', '']
    linhas = ['## R25 — o terceiro domínio: uma clínica de saúde', '',
              f"**{mil(r['chamadas'])} chamadas, {usd(r['custo_usd'])}.** Corpus gerado por molde com "
              'gabarito fixado antes do texto, cinco classes, quatro arranjos.', '',
              '| arranjo | acerto | IC95 | viradas contra a base | acima do corte | por molde |',
              '|---|---|---|---|---|---|']
    for nome, b in r['arranjos'].items():
        ic = f"[{pct(b['ic95'][0])}; {pct(b['ic95'][1])}]"
        virada = (f"{b['viradas']}/{b['pares_com_base']}" if nome.startswith('meta') else '—')
        moldes = ', '.join(f"{m} {v['acertos']}/{v['n']}" for m, v in sorted(b['por_molde'].items()))
        linhas.append(f"| {nome} | {b['acertos']}/{b['n']} = **{pct(b['taxa'])}** | {ic} | {virada} "
                      f"| {b['viradas_acima_do_corte'] if nome.startswith('meta') else '—'} | {moldes} |")
    ps, pz = r['pareado_sujeito'], r['pareado_sanitizacao']
    linhas += ['',
               f"Frase de sujeito contra a base: {ps['certo_so_sujeito']} a {ps['certo_so_base']}, "
               f"{p_valor(ps['p'])}. Sanitização contra a ordem direta: "
               f"{pz['virou_so_sem_defesa']} a {pz['virou_so_com_defesa']}, {p_valor(pz['p'])}.", '']
    if 'R25' in LEITURA:
        linhas += [LEITURA['R25'], '']
    return linhas


def secao_r26(r):
    if not r:
        return ['## R26 — ainda não rodou', '']
    linhas = ['## R26 — a resposta que exige dois trechos', '',
              f"**{mil(r['chamadas'])} chamadas, {usd(r['custo_usd'])}.** {r['pares']} pares de "
              'perguntas de fonte única viraram perguntas duplas; a resposta só conta se as duas '
              'regex casarem.', '',
              '| pergunta | arranjo | acerto | todos os alvos presentes | pareado contra todos |',
              '|---|---|---|---|---|']
    for nome, b in r['arranjos'].items():
        tipo, arranjo = nome.split('/')
        par = b.get('pareado_contra_todos')
        pareado = (f"{par['certo_so_selecao']} a {par['certo_so_todos']}, {p_valor(par['p'])}"
                   if par else '—')
        linhas.append(f"| {tipo} | {arranjo} | {b['acertos']}/{b['n']} = **{pct(b['taxa'])}** "
                      f"| {b['todos_os_alvos_presentes']}/{b['n']} | {pareado} |")
    o = r['ordenacao']
    linhas += ['',
               f"Ordenação nas perguntas duplas ({o['n']} casos): o topo é um dos alvos em "
               f"{o['topo_e_alvo']}; os dois alvos estão no top-2 em {o['dois_no_top2']} e no top-3 em "
               f"{o['dois_no_top3']}; o topo veio `essencial` em {o['topo_essencial']}, então a regra de "
               f"recall de graça dispararia em {o['regra_de_recall_dispararia']}; os dois alvos foram "
               f"marcados `essencial` em {o['casos_com_dois_alvos_essenciais']}.", '']
    if 'R26' in LEITURA:
        linhas += [LEITURA['R26'], '']
    return linhas


def secao_r27(r):
    if not r:
        return ['## R27 — ainda não rodou', '']
    linhas = ['## R27 — sanitizador e sentinela no mesmo payload', '',
              f"**{mil(r['chamadas'])} chamadas, {usd(r['custo_usd'])}.**", '',
              '| montagem | acerto | viradas | acima do corte | sentinela certo | chamadas por decisão |',
              '|---|---|---|---|---|---|']
    for nome, b in r['montagens'].items():
        s = b['sentinela']
        vigia = f"{s['certos']}/{s['n']}" if s else '—'
        linhas.append(f"| {nome} | {b['acertos']}/{b['n']} | {b['viradas']}/{b['pares_com_base']} = "
                      f"{pct(b['taxa_de_virada'])} | {b['viradas_acima_do_corte']} | {vigia} "
                      f"| {b['chamadas_por_decisao']} |")
    linhas += ['', '| montagem | pareado contra separado |', '|---|---|']
    for nome, par in r['pareado_contra_separado'].items():
        linhas.append(f"| {nome} | {par['virou_so_nesta']} viraram só aqui, "
                      f"{par['virou_so_separado']} só no separado, {p_valor(par['p'])} |")
    linhas.append('')
    if 'R27' in LEITURA:
        linhas += [LEITURA['R27'], '']
    return linhas


def montar():
    artefatos = {n: carregar(f) for n, f in (('R23', 'r23-parafrase.json'),
                                             ('R24', 'r24-votacao.json'),
                                             ('R25', 'r25-terceiro-dominio.json'),
                                             ('R26', 'r26-dois-trechos.json'),
                                             ('R27', 'r27-integracao.json'))}
    chamadas = sum((a or {}).get('chamadas', 0) for a in artefatos.values())
    custo = sum((a or {}).get('custo_usd', 0) for a in artefatos.values())
    partes = [
        '# Bateria complementar: as lacunas que o estudo declarou, medidas',
        '',
        '> Gerado por `python laboratorio/gerar_bateria.py` a partir dos artefatos `r23-` a `r27-`.',
        '> Cada rodada tem pré-registro no cabeçalho do próprio script, com o critério de',
        '> falsificação escrito antes de rodar.',
        '',
        f'**Cinco rodadas, {mil(chamadas)} chamadas novas, {usd(custo)}.** O que cada uma fecha:',
        '',
        '- **R23** — o sanitizador da R22 foi medido contra um vetor; aqui contra 48, incluindo 36',
        '  escritos por outros modelos depois de o sanitizador estar congelado, mais o dano',
        '  colateral em mensagem legítima que usa as palavras-gatilho.',
        '- **R24** — a votação que o guia sugeria e Q098 registrou como nunca testada.',
        '- **R25** — o terceiro domínio que Q060 pediu, com a frase de sujeito e a sanitização',
        '  levadas junto.',
        '- **R26** — a pergunta cuja resposta exige dois trechos, o teste adversarial de Q095.',
        '- **R27** — as duas defesas no mesmo payload, que o guia prescreve e ninguém tinha medido.',
        '',
    ]
    if 'sintese' in LEITURA:
        partes += ['## O que muda no guia', '', LEITURA['sintese'], '']
    for nome, funcao in (('R23', secao_r23), ('R24', secao_r24), ('R25', secao_r25),
                         ('R26', secao_r26), ('R27', secao_r27)):
        partes += funcao(artefatos[nome])
    partes += ['## Como refazer', '', '```',
               'python laboratorio/r23_parafrase.py --gerar && python laboratorio/r23_parafrase.py --rodar',
               'python laboratorio/r24_votacao.py --rodar',
               'python laboratorio/r25_terceiro_dominio.py --gerar && python laboratorio/r25_terceiro_dominio.py --rodar',
               'python laboratorio/r26_dois_trechos.py --rodar',
               'python laboratorio/r27_integracao.py --rodar',
               'python laboratorio/gerar_bateria.py', '```', '']
    return '\n'.join(partes) + '\n'


def main():
    DESTINO.write_text(montar(), encoding='utf-8')
    print(f'{DESTINO} ({len(DESTINO.read_text(encoding="utf-8").splitlines())} linhas)')


if __name__ == '__main__':
    main()
