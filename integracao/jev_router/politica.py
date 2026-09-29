"""O que o Jev decide nos fluxos do Claude Code e do Codex, e o que ele não decide.

Este arquivo foi reescrito depois da medição, e o que saiu dele importa tanto quanto o que
ficou. O plano original era rotear esforço — classificar o pedido como simples ou difícil e
poupar modelo caro nos simples. Medido em 60 pedidos reais do histórico e em 40 com o contexto
da conversa, isso não funciona: o Jev quase nunca diz "simples", e quando diz é com confiança
de no máximo 0,73. Não existe corte que economize sem estragar trabalho. A evidência está em
`avaliacao/relatorio.json` e `avaliacao/com-contexto.json`.

O que ficou é o que o estudo já dizia que o Jev faz bem, e que a medição confirmou no material
real: **dizer sobre o que é a mensagem**. Nos mesmos 60 pedidos, contra os oito `regex_match`
que hoje sugerem skills nesta máquina:

    Jev, corte 0,90:  9 de 23 temas reais, 0 sugestões à toa em 37 mensagens sem tema
    regex de hoje:    5 de 23 temas reais, 1 sugestão à toa

Quase o dobro da cobertura, sem nenhum disparo falso. E o erro do Jev é por omissão — 10 dos 13
erros foram deixar de sugerir, não sugerir errado —, que é o lado seguro para quem injeta
contexto num modelo caro.

O corte é 0,90 e não 0,99 porque esta aplicação tem outra assimetria: uma sugestão perdida
custa uma skill não carregada, e uma sugestão errada custa três linhas de contexto. O corte foi
calibrado neste dado, que é a regra número 2 do guia prático.
"""

from pathlib import Path

# Calibrado em `avaliacao/skills-resultado.json`: em 0,90 são 9 acertos e 0 falsos; em 0,95 a
# cobertura cai para 5 sem nenhum ganho de precisão.
CORTE_DO_TEMA = 0.90

TEMAS = {
    'juridico': 'Peticao, recurso, processo, jurisprudencia, audiencia, prazo judicial, cliente do escritorio.',
    'comunicacao': 'Texto para publicar: post, materia, roteiro, card, apresentacao, site institucional, aula.',
    'estrategia': 'Decisao de negocio, plano, prioridade, posicionamento.',
    'google': 'Gmail, Drive, Agenda, Planilhas, Apps Script, Docs do Google.',
    'infra': 'Servidor, VPS, deploy, Docker, rede, backup, maquina, sistema operacional, ambiente.',
    'pesquisa': 'Levantar informacao, buscar fonte, revisar literatura, investigar dados, comparar opcoes.',
    'relatorio': 'Produzir relatorio, dossie, documento formal de resultado, PDF de entrega.',
    'receita': 'Dinheiro entrando: proposta comercial, cliente novo, preco, contrato, faturamento.',
    'nenhum': 'Nenhum dos temas acima: e programacao comum, conversa, ajuste de codigo ou operacao do projeto.',
}

# As skills que cada tema oferece. Revisto em 23/09/2026: a lista antiga, copiada dos hookify,
# apontava para skills que não existem (`/ash`, `/themis`, `/google`, `/infra`, `/midas`) ou
# estão desligadas (`oracle`, `mel`, `apify-operacional`, `investigador-provas`), e a nota
# injetada mandava o agente atrás de nada. Agora cada nome é conferido na pasta de skills do
# agente que está rodando (Claude Code ou Codex têm pastas diferentes) antes de ser sugerido.
SKILLS = {
    'juridico': [('cicero', 'engenharia jurídica'), ('arcano', 'esteira do escritório')],
    'comunicacao': [('diana-comunicacao', 'comunicação'), ('relatorio-inteia', 'relatório')],
    'estrategia': [('helena', 'estratégia e decisão')],
    'infra': [('vps-server-management', 'VPS'), ('hermes', 'Hermes')],
    'pesquisa': [('deep-research', 'pesquisa com fontes'), ('helena', 'dados e cenários')],
    'relatorio': [('relatorio-inteia', 'relatório INTEIA')],
    'receita': [('iris', 'concierge')],
}


def _desligadas(configuracao):
    try:
        import json
        dado = json.loads(Path(configuracao).read_text(encoding='utf-8'))
        return {k for k, v in (dado.get('skillOverrides') or {}).items() if v in ('off', False)}
    except (OSError, ValueError):
        return set()


def disponiveis(tema, pasta=None, configuracao=None):
    """As skills do tema que existem na pasta do agente e não estão desligadas, como texto."""
    pasta = Path(pasta) if pasta else Path.home() / '.claude' / 'skills'
    desligadas = _desligadas(configuracao or Path.home() / '.claude' / 'settings.json')
    achadas = [f'`/{nome}` ({rotulo})' for nome, rotulo in SKILLS.get(tema, [])
               if nome not in desligadas and ((pasta / nome / 'SKILL.md').exists()
                                              or any(pasta.glob(f'synced/*/{nome}/SKILL.md')))]
    return ', '.join(achadas)


PERGUNTAS = {
    'tema': {
        'type': 'choice',
        'instructions': ('Qual e o assunto do pedido abaixo, feito por um advogado que tambem '
                         'programa? Escolha o tema principal; se nenhum se aplicar, escolha '
                         '"nenhum".'),
        'criteria': TEMAS,
    },
    'risco': {
        'type': 'choice',
        'instructions': ('O pedido abaixo, se atendido literalmente, produz algum efeito que '
                         'nao se desfaz ou que sai desta maquina?'),
        'criteria': {
            'seguro': ('So leitura, analise, explicacao ou alteracao de arquivo local, que o '
                       'controle de versao desfaz.'),
            'atencao': ('Altera muitos arquivos, instala ou remove dependencia, mexe em '
                        'configuracao do ambiente ou apaga arquivo nao versionado.'),
            'irreversivel': ('Publica, envia, implanta, apaga em definitivo, mexe em producao, '
                             'em banco de dados remoto ou em servico externo.'),
        },
    },
}

AVISO_DE_RISCO = {
    'irreversivel': ('Este pedido tem efeito que não se desfaz ou que sai desta máquina. '
                     'Confirme o alvo antes de executar.'),
}


def decidir(respostas, pasta_de_skills=None, configuracao=None):
    """Traduz as respostas do Jev numa sugestão, ou em silêncio.

    Silêncio é o resultado mais comum e é o certo: em 37 dos 60 pedidos reais não havia tema
    nenhum a sugerir.
    """
    tema = (respostas.get('tema') or {}).get('choice')
    confianca = (respostas.get('tema') or {}).get('confidence')
    risco = (respostas.get('risco') or {}).get('choice')

    decisao = {'tema': tema, 'confianca': confianca, 'risco': risco, 'sugere': False}
    if tema in SKILLS and (confianca or 0) >= CORTE_DO_TEMA:
        decisao.update({'sugere': True, 'skills': disponiveis(tema, pasta_de_skills, configuracao)})
        if not decisao['skills']:
            decisao.update({'sugere': False, 'motivo': 'nenhuma skill do tema disponível neste agente'})
    elif tema in SKILLS:
        decisao['motivo'] = f'confiança {confianca} abaixo do corte {CORTE_DO_TEMA}'
    else:
        decisao['motivo'] = 'sem tema'

    # O risco nunca é automatizado: ele só acrescenta um aviso, nunca libera nada. É o passo 2
    # do guia prático, e a razão é que o Jev perdeu 1 de 4 comandos irreversíveis na medição.
    if risco in AVISO_DE_RISCO:
        decisao['aviso'] = AVISO_DE_RISCO[risco]
    return decisao


def texto_para_o_agente(decisao, modo):
    """A nota injetada no contexto. Curta: cada token dela é pago pelo modelo caro."""
    partes = []
    if decisao.get('sugere'):
        partes.append(f"[jev/{modo}] tema **{decisao['tema']}** "
                      f"(confiança {decisao['confianca']:.2f}".replace('.', ',') + "). Skills para isto: "
                      f"{decisao['skills']}.")
    if decisao.get('aviso'):
        partes.append(decisao['aviso'])
    return ' '.join(partes)
