"""Plugin jev-fluxos: a ferramenta `jev_fluxos`, com os fluxos do JEV que o modelo aciona na conversa.

- `agendar` / `responder` / `abertos`: fluxo 6, ciclo agêntico de agenda
  (`jev_hermes/agenda.py`). O ciclo busca horários livres no Google Agenda de Igor e para quando
  precisa dele: a ferramenta devolve `pergunta`, o modelo a repassa a Igor e, com a resposta dele,
  chama `responder`. A reserva só é feita depois da escolha de Igor e só é dada como feita depois
  de lida de volta como confirmada. O evento é criado sem convidados.
- `modelo`: fluxo 3, que nível de modelo uma subtarefa pede, dentro do orçamento (não executa).

Os fluxos 1, 2, 4 e 5 rodam por CLI e rotina (ver a skill `jev`), porque demoram minutos ou rodam
sem conversa. Nenhum gancho automático: nada roda sem o modelo chamar a ferramenta.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(os.environ.get('JEV_HERMES_RAIZ', '/root/.hermes/integrations/jev'))
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

OPERACOES = ['agendar', 'responder', 'abertos', 'modelo']

SCHEMA = {
    "name": "jev_fluxos",
    "description": (
        "Fluxos do JEV que agem. agendar: marca compromisso na agenda de Igor pelo ciclo "
        "buscar → perguntar → reservar → confirmar; devolve situacao. Se situacao for "
        "'aguardando_usuario', repasse a `pergunta` a Igor EXATAMENTE e, quando ele responder, chame "
        "responder com o `id` e a resposta dele, sem interpretar nem escolher por ele. 'concluido' traz "
        "a `resposta` final (o evento foi lido de volta como confirmado); 'humano' traz o `motivo`. "
        "abertos: ciclos de agenda esperando Igor. modelo: que nível de modelo (pequeno, especialista, "
        "fronteira) uma subtarefa pede dentro do orçamento, sem executar — para delegar com o modelo certo."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operacao": {"type": "string", "enum": OPERACOES},
            "pedido": {"type": "string", "description": "agendar: o pedido de Igor, como ele disse."},
            "titulo": {"type": "string", "description": "agendar: título do compromisso (opcional)."},
            "duracao_min": {"type": "integer", "description": "agendar: duração em minutos (opcional)."},
            "id": {"type": "string", "description": "responder: id do ciclo devolvido por agendar."},
            "resposta": {"type": "string", "description": "responder: a resposta de Igor, literal."},
            "subtarefa": {"type": "string", "description": "modelo: descrição da subtarefa."},
            "orcamento_usd": {"type": "number", "description": "modelo: orçamento restante (padrão 1,00)."},
        },
        "required": ["operacao"],
        "additionalProperties": False,
    },
}


def handle(args, **kwargs):
    operacao = (args or {}).get('operacao')
    try:
        from jev_hermes import agenda, ciclo, modelos
        if operacao == 'agendar':
            resultado = agenda.agendar(args.get('pedido'), titulo=args.get('titulo'),
                                       duracao_min=args.get('duracao_min'))
        elif operacao == 'responder':
            resultado = agenda.responder(args.get('id'), args.get('resposta'))
        elif operacao == 'abertos':
            resultado = {'abertos': [ciclo.resumo(e) for e in ciclo.abertos('agenda')]}
        elif operacao == 'modelo':
            resultado = modelos.escolher(args.get('subtarefa') or '', modelos.Orcamento(1.0 if args.get('orcamento_usd') is None else args['orcamento_usd']))
        else:
            resultado = {'status': 'invalid_input', 'motivo': f'operacao deve ser uma de {OPERACOES}'}
    except (KeyError, ValueError) as erro:
        resultado = {'status': 'invalid_input', 'motivo': str(erro)[:300]}
    except Exception as erro:
        resultado = {'status': 'fallback', 'motivo': f'{type(erro).__name__}: {str(erro)[:200]}',
                     'continue_with': 'hermes'}
    return json.dumps(resultado, ensure_ascii=False)


def register(ctx):
    ctx.register_tool(name="jev_fluxos", toolset="jev_fluxos", schema=SCHEMA, handler=handle)
