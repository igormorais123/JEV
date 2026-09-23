"""Fluxo 2 — orquestração de agentes: "quem trabalha agora?".

O quadro: chamado → estado atual → JEV roteador → pesquisador, programador, testador ou revisor
→ cada agente devolve novo estado → JEV decide de novo; "não é esteira fixa: é decisão baseada no
estado". Aqui, sobre o motor `ciclo`:

- **Estado**: o chamado, o diagnóstico (se já há), a versão do código, o resultado do último teste
  e a revisão de cada versão. É o que o gabarito do guia pede: objetivo, o que foi feito, o
  resultado da última ação e o que falta.
- **Guardas em código**: testar só com código novo ou nunca testado; revisar só a versão que
  passou nos testes; concluir só com a versão atual testada, aprovada na revisão e aprovada pelo
  `judge` do fluxo 1 (evidência que o harness observou). Com mais de uma ação permitida, decide o
  Jev — por exemplo, pesquisar de novo ou reprogramar depois de um teste que falhou.
- **Testador é o harness**, não um modelo: roda o comando de teste e conta o resultado.
- **Modelo de cada agente pelo fluxo 3**: a mesma função que volta depois de falhar sobe um nível.
- `esteira=True` troca o roteador pela sequência fixa pesquisar → programar → testar → revisar,
  sem voltar: é a arquitetura A da bancada (fluxo 5).

CLI: `python3 -m jev_hermes.agentes --pasta DIR --chamado ARQ --teste "python3 -m pytest -q"
[--orcamento 8] [--esteira] [--avisar]`.
"""
import json
import re
from pathlib import Path

from . import avaliacao, ciclo, modelos, workflows

LEITURA = ['Read', 'Glob', 'Grep', 'Bash(git log:*)', 'Bash(git diff:*)', 'Bash(git status:*)', 'Bash(ls:*)']
VEREDITO = re.compile(r'VEREDITO:\s*(aprovado|mudancas|mudanças)', re.IGNORECASE)
ESTEIRA = ['PESQUISAR', 'PROGRAMAR', 'TESTAR', 'REVISAR', 'CONCLUIDO']
MAX_PESQUISAS = 2

PROMPTS = {
    'PESQUISAR': ('Você é o PESQUISADOR. Não altere arquivos. Leia o código e diga onde está o problema do '
                  'chamado, a causa provável e o que precisa mudar, em até 15 linhas.'),
    'PROGRAMAR': ('Você é o PROGRAMADOR. Faça a menor mudança que resolve o chamado. Rode os testes '
                  'exatamente com o COMANDO DE TESTE DO PROJETO (outro Python pode não ter pytest). '
                  + avaliacao.ENTREGA),
    'REVISAR': ('Você é o REVISOR. Não altere arquivos. Leia o `git diff` e diga se a mudança resolve o '
                'chamado sem quebrar outra coisa. Termine com uma linha exatamente "VEREDITO: aprovado" '
                'ou "VEREDITO: mudancas" seguida do que mudar.'),
}


def _contexto(estado):
    partes = [f"CHAMADO:\n{estado['objetivo']}", f"COMANDO DE TESTE DO PROJETO: {estado.get('comando_teste')}"]
    if estado.get('diagnostico'):
        partes.append(f"DIAGNÓSTICO DO PESQUISADOR:\n{estado['diagnostico']}")
    if estado.get('teste'):
        partes.append(f"ÚLTIMO TESTE (versão {estado['teste']['versao']}): {json.dumps(estado['teste']['resultado'])}\n"
                      f"{estado['teste']['saida'][-1500:]}")
    if estado.get('revisao') and estado['revisao'].get('texto'):
        partes.append(f"ÚLTIMA REVISÃO (versão {estado['revisao']['versao']}):\n{estado['revisao']['texto'][-1500:]}")
    if estado.get('retorno_do_judge'):
        partes.append('A AVALIAÇÃO FINAL APONTOU:\n' + '\n'.join(estado['retorno_do_judge']))
    return '\n\n'.join(partes)


def montar(pasta, comando_teste, orcamento, *, esteira=False, transporte=None):
    pasta = Path(pasta).resolve()

    def agente(papel, ferramentas):
        def executar(estado):
            tentativas = estado.setdefault('tentativas_por_papel', {})
            tentativas[papel] = tentativas.get(papel, 0) + 1
            decisao = modelos.escolher(f'{PROMPTS[papel]}\n\n{_contexto(estado)[:3000]}', orcamento,
                                       tentativa=tentativas[papel],
                                       nivel_anterior=estado.get('nivel_por_papel', {}).get(papel),
                                       transporte=transporte, origem='fluxo-agentes-modelo')
            if not decisao.get('nivel'):
                modelos.registrar(decisao)
                estado['sem_orcamento'] = True
                return {'erro': decisao['motivo']}
            estado.setdefault('nivel_por_papel', {})[papel] = decisao['nivel']
            feito = modelos.executar_claude(f"{PROMPTS[papel]}\n\n{_contexto(estado)}", pasta, decisao,
                                            ferramentas=ferramentas, orcamento=orcamento)
            modelos.registrar(decisao, feito['custo_usd'])
            estado['custo_agentes_usd'] = round(estado.get('custo_agentes_usd', 0) + (feito['custo_usd'] or 0), 4)
            if papel == 'REVISAR':   # o veredito é a última linha: lido do texto inteiro, antes do corte
                achado = VEREDITO.findall(feito['texto'])
                estado['_aprovado'] = bool(achado) and achado[-1].lower() == 'aprovado'
            if papel == 'PROGRAMAR':
                estado['relato'] = feito['texto'][:workflows.MAX_TEXTO]
            return {'papel': papel.lower(), 'modelo': feito['modelo'], 'custo_usd': feito['custo_usd'],
                    'texto': feito['texto'][:1500], **({'erro': 'agente falhou'} if feito['erro'] else {})}
        return executar

    pesquisar_agente = agente('PESQUISAR', LEITURA)
    programar_agente = agente('PROGRAMAR', avaliacao.FERRAMENTAS_DE_EDICAO + [f'Bash({comando_teste}:*)'])
    revisar_agente = agente('REVISAR', LEITURA)

    def pesquisar(estado):
        observacao = pesquisar_agente(estado)
        if not observacao.get('erro'):
            estado['diagnostico'] = observacao['texto']
        return observacao

    def programar(estado):
        observacao = programar_agente(estado)
        if not observacao.get('erro'):
            estado['versao'] = estado.get('versao', 0) + 1
            estado.pop('retorno_do_judge', None)
        return observacao

    def testar(estado):
        obs = avaliacao.observar_testes(comando_teste, pasta)
        r = obs.resultado
        passou = r['codigo_saida'] == 0 and not r.get('falharam') and r.get('executados') != 0
        estado['teste'] = {'versao': estado.get('versao', 0), 'passou': passou, 'resultado': r, 'saida': obs.conteudo}
        return {'papel': 'testador', 'passou': passou, **{k: v for k, v in r.items() if v is not None}}

    def revisar(estado):
        observacao = revisar_agente(estado)
        if observacao.get('erro'):
            return observacao
        aprovado = estado.pop('_aprovado', False)
        estado['revisao'] = {'versao': estado.get('versao', 0), 'aprovada': aprovado, 'texto': observacao['texto']}
        return {**observacao, 'aprovada': aprovado}

    def concluir(estado):
        veredito = workflows.judge(
            {'pedido_original': estado['objetivo'][:workflows.MAX_TEXTO],
             'criterios': estado.get('criterios') or [avaliacao.CRITERIO_PADRAO],
             'resultado': (estado.get('relato') or 'sem relato')[:workflows.MAX_TEXTO],
             'tentativa': 1, 'max_tentativas': 0, 'sensivel': bool(estado.get('sensivel'))},
            observacoes=[o for o in (avaliacao.observar_testes(comando_teste, pasta),
                                     avaliacao.observar_diff(pasta, estado.get('base')),
                                     avaliacao.observar_integridade(pasta, estado.get('base'))) if o is not None],
            transporte=transporte, sensivel_por_regra=False)
        estado['judge'] = veredito['veredito']
        if veredito['veredito'] == 'passou':
            return {'fim': True, 'resposta': f"Chamado resolvido na versão {estado.get('versao', 0)}: testes "
                                             'passando, revisão aprovada e avaliação final aprovada.'}
        faltas = avaliacao._faltas_do_jev(veredito)
        if faltas and estado.get('rejeicoes_do_judge', 0) < 1:
            estado['rejeicoes_do_judge'] = estado.get('rejeicoes_do_judge', 0) + 1
            estado['retorno_do_judge'] = faltas
            estado['revisao'] = {'versao': -1, 'aprovada': False}   # a versão atual precisa mudar
            return {'judge': 'refazer', 'faltas': faltas}
        estado['precisa_humano'] = True
        return {'judge': veredito['veredito'], 'motivos': veredito.get('motivos', [])[:4], 'humano': True,
                'motivo': 'avaliação final pede uma pessoa: ' + '; '.join(veredito.get('motivos', [])[:2])}

    def atual(estado, chave):
        registro = estado.get(chave) or {}
        return registro.get('versao') == estado.get('versao', 0)

    def pode_concluir(estado):
        return (estado.get('versao', 0) > 0 and atual(estado, 'teste') and estado['teste']['passou']
                and atual(estado, 'revisao') and estado['revisao']['aprovada'] and not estado.get('precisa_humano'))

    def precisa_mudar(estado):
        """Nada feito ainda, teste da versão atual falhou, revisão dela pediu mudança, ou o judge apontou falta."""
        return (estado.get('versao', 0) == 0 or bool(estado.get('retorno_do_judge'))
                or (atual(estado, 'teste') and not estado['teste']['passou'])
                or (atual(estado, 'revisao') and not estado['revisao']['aprovada']))

    livre = lambda e: not e.get('precisa_humano') and not e.get('sem_orcamento')   # noqa: E731
    acoes = [
        ciclo.Acao('PESQUISAR', 'Pesquisador: localizar o problema e a causa, sem mudar codigo.', pesquisar,
                   lambda e: livre(e) and e.get('tentativas_por_papel', {}).get('PESQUISAR', 0) < MAX_PESQUISAS),
        ciclo.Acao('PROGRAMAR', 'Programador: mudar o codigo para resolver o chamado ou o que falhou.', programar,
                   # programar só com motivo: medido na bancada de 23/09, o Jev lia o tema do chamado
                   # ("implemente") e pedia PROGRAMAR oito vezes seguidas, sem testar nem revisar
                   lambda e: livre(e) and precisa_mudar(e)),
        ciclo.Acao('TESTAR', 'Testador: rodar os testes na versao atual do codigo.', testar,
                   lambda e: livre(e) and not atual(e, 'teste')),
        ciclo.Acao('REVISAR', 'Revisor: ler a mudanca que passou nos testes e aprovar ou pedir mudancas.', revisar,
                   lambda e: livre(e) and atual(e, 'teste') and e['teste']['passou'] and not atual(e, 'revisao')
                   and not e.get('retorno_do_judge')),
        ciclo.Acao('CONCLUIDO', 'Testes passam e a revisao aprovou a versao atual: fechar o chamado.', concluir,
                   pode_concluir),
    ]
    if esteira:   # arquitetura A: a ordem manda, não o estado
        def posicao(nome):
            return lambda e: len(e['historico']) == ESTEIRA.index(nome)
        acoes = [ciclo.Acao(a.nome, a.descricao, a.executar,
                            (lambda p, a=a: lambda e: p(e) and (a.nome != 'CONCLUIDO' or pode_concluir(e)))(posicao(a.nome)))
                 for a in acoes]

    def regra(estado):
        if pode_concluir(estado):
            return 'CONCLUIDO'
        if not estado.get('diagnostico') and not estado.get('versao'):
            return 'PESQUISAR'
        if estado.get('versao', 0) == 0:
            return 'PROGRAMAR'
        if not atual(estado, 'teste'):
            return 'TESTAR'
        if not estado['teste']['passou'] or estado.get('retorno_do_judge'):
            return 'PROGRAMAR'
        if not atual(estado, 'revisao'):
            return 'REVISAR'
        return 'PROGRAMAR'

    def descrever(estado):
        teste = estado.get('teste') or {}
        revisao = estado.get('revisao') or {}
        return '\n'.join([   # progresso primeiro: o Jev lê tema, e o tema do chamado é sempre "programar"
            'FEITO ATE AGORA: ' + (' -> '.join(f"{h['acao']}" for h in estado['historico']) or 'nada'),
            f"DIAGNOSTICO: {'pronto: ' + estado['diagnostico'][:600] if estado.get('diagnostico') else 'nenhum ainda'}",
            f"VERSAO DO CODIGO: {estado.get('versao', 0)} (0 = nada mudou ainda)",
            f"ULTIMO TESTE: versao {teste.get('versao', '-')}, "
            f"{'passou' if teste.get('passou') else 'falhou' if teste else 'nunca rodou'} "
            f"{json.dumps(teste.get('resultado') or {})}",
            f"ULTIMA REVISAO: versao {revisao.get('versao', '-')}, "
            f"{'aprovada' if revisao.get('aprovada') else 'pediu mudancas' if revisao else 'nenhuma'}",
            f"AVALIACAO FINAL APONTOU: {estado.get('retorno_do_judge') or 'nada'}",
            f"CHAMADO (resumo, so contexto): {estado['objetivo'][:300]}",
        ])

    return ciclo.Fluxo('agentes-esteira' if esteira else 'agentes', acoes, descrever, None if esteira else regra,
                       instrucao=('Pelo PROGRESSO descrito (o que ja foi feito, versao, ultimo teste, ultima revisao), '
                                  'e nao pelo tema do chamado: quem deve trabalhar agora?'),
                       max_passos=len(ESTEIRA) if esteira else 14)


def resolver(pasta, chamado, comando_teste, *, criterios=None, orcamento_usd=8.0, esteira=False, sensivel=False,
             transporte=None):
    """Roda o fluxo inteiro sobre a pasta. Devolve o resumo do ciclo com custo e orçamento."""
    avaliacao.preparar_git(pasta)
    orcamento = modelos.Orcamento(orcamento_usd)
    fluxo = montar(pasta, comando_teste, orcamento, esteira=esteira, transporte=transporte)
    estado = ciclo.novo(fluxo, chamado, criterios=criterios, pasta=str(Path(pasta).resolve()),
                        comando_teste=comando_teste, sensivel=sensivel, base=avaliacao.linha_de_base(pasta))
    estado = ciclo.rodar(fluxo, estado, transporte=transporte)
    saida = ciclo.resumo(estado)
    saida.update(orcamento=orcamento.como_dict(), versao=estado.get('versao', 0),
                 judge=estado.get('judge'), custo_agentes_usd=estado.get('custo_agentes_usd', 0.0))
    return saida


if __name__ == '__main__':
    import argparse
    analisador = argparse.ArgumentParser(description='Fluxo 2: roteador de agentes por estado.')
    analisador.add_argument('--pasta', required=True)
    analisador.add_argument('--chamado', required=True, help='texto ou caminho de arquivo')
    analisador.add_argument('--teste', required=True)
    analisador.add_argument('--criterio', action='append')
    analisador.add_argument('--orcamento', type=float, default=8.0)
    analisador.add_argument('--esteira', action='store_true', help='sequência fixa (arquitetura A)')
    analisador.add_argument('--sensivel', action='store_true', help='nunca conclui sem uma pessoa')
    analisador.add_argument('--avisar', action='store_true')
    a = analisador.parse_args()
    caminho_chamado = Path(a.chamado)
    texto = caminho_chamado.read_text(encoding='utf-8') if caminho_chamado.is_file() else a.chamado
    fim = resolver(a.pasta, texto, a.teste, criterios=avaliacao._criterios(a.criterio) or None,
                   orcamento_usd=a.orcamento, esteira=a.esteira, sensivel=a.sensivel)
    if a.avisar and fim['situacao'] != 'concluido':
        avaliacao.avisar(f"🔧 Chamado precisa de você ({Path(a.pasta).name}): {fim['motivo']}. "
                         f"Passos: {', '.join(fim['passos'])}.")
    print(json.dumps(fim, ensure_ascii=False, indent=1))
