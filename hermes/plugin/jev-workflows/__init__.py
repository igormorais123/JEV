"""Plugin jev-workflows: a ferramenta explícita `jev_workflows` com os cinco fluxos do Jev.

O código de decisão mora em `/root/.hermes/integrations/jev/jev_hermes/workflows.py`; este
arquivo só expõe a ferramenta. Não registra gancho: nada roda sem o modelo chamar a ferramenta,
e nenhum tráfego passa por aqui automaticamente.

Judge pela ferramenta: tudo no JSON é escrito pelo modelo que chama a ferramenta — fonte, referência,
conteúdo e contagem são autodeclarados. Este plugin não tem verificador nem captura própria, então
não repassa observações e o judge termina sempre em `revisao_humana` (nunca `passou` nem `retry`).
`passou` só existe chamando `workflows.judge(..., observacoes=[Observacao...])` a partir de código do
harness que observou a evidência por conta própria (ou via `workflows.observar_arquivo`, com raízes
dadas pelo harness). Os ganchos `pre_verify` e `subagent_stop` existem nesta versão do Hermes, mas
não entregam essa observação — ligá-lo a eles fica para uma decisão posterior, com revisão humana.

Interruptores: `touch /root/.hermes/integrations/jev/DESLIGADO` faz o núcleo recusar toda chamada
(os fluxos voltam para revisão humana); `JEV_WORKFLOWS_OFFLINE=1` roda só a parte determinística.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(os.environ.get('JEV_HERMES_RAIZ', '/root/.hermes/integrations/jev'))
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

OPERACOES = ['judge', 'agente', 'modelo', 'triagem', 'experimento']

SCHEMA = {
    "name": "jev_workflows",
    "description": (
        "Fluxos consultivos com o Jev (Sistema 1 barato). Regra e conta ficam no código; o Jev só "
        "escolhe entre opções fechadas, sempre com escape. NUNCA executa ação: não despacha agente, "
        "não troca modelo, não publica, não reprova entrega. Confiança do Jev é sugestão, não métrica. "
        "judge: conclusão de tarefa de agente. Por esta ferramenta toda evidência é autodeclarada "
        "(fonte, referência, conteúdo e contagem vêm de quem chama), então o veredito é sempre "
        "revisao_humana, com motivos e critérios estruturados; passou/retry só existem pelo harness com "
        "evidência que ele próprio observou. "
        "agente/modelo: escolhe entre candidatos que você fornece, após filtro por capacidade, "
        "disponibilidade, contexto e orçamento. triagem: uma rota por item (até 60). experimento: "
        "compara resultados medidos com denominadores (IC95); não inventa número."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operacao": {"type": "string", "enum": OPERACOES},
            "entrada": {
                "type": "object",
                "description": (
                    "judge: {pedido_original, criterios:[{id,descricao}], evidencias:[{tipo:diff|teste|log|"
                    "artefato|outro, fonte (rótulo, não confere confiança):hermes|ci|executor|ferramenta|"
                    "sistema|humano|agente, referencia, "
                    "conteudo, resultado?:{executados,passaram,falharam,codigo_saida}}], resultado, "
                    "tentativa?, max_tentativas?, sensivel?, limiar_revisao?}. "
                    "agente: {tarefa:{descricao, capacidades_requeridas?, sensivel?}, candidatos:[{id, descricao, "
                    "capacidades, limites:{disponivel?, max_concorrencia?, ocupacao?, permite_sensivel?}}]}. "
                    "modelo: {tarefa:{descricao, tokens_entrada_estimados, tokens_saida_estimados, orcamento_usd?, "
                    "capacidades_requeridas?, sensivel?}, candidatos:[{id, descricao, capacidades, "
                    "usd_por_mtok_entrada, usd_por_mtok_saida, contexto_tokens, limites?}]}. "
                    "triagem: {rotas:[{id, descricao, sensivel?}], itens:[texto | {id, texto}], contexto?}. "
                    "experimento: {objetivo, criterios:[{metrica, direcao:maior|menor, limite?, amostra_minima?}] "
                    "(o primeiro é o principal), configuracoes:[{id, descricao, resultados:{metrica:"
                    "{sucessos,total} | {media,desvio,n}}}], consultar_jev?}. "
                    "ids: [a-z0-9][a-z0-9_.-]{0,39}."
                ),
            },
            "offline": {"type": "boolean", "default": False,
                        "description": "true: não chama o Jev; só a parte determinística."},
        },
        "required": ["operacao", "entrada"],
        "additionalProperties": False,
    },
}


def handle(args, **kwargs):
    try:
        from jev_hermes import workflows
        resultado = workflows.executar(args.get('operacao'), args.get('entrada'),
                                       offline=True if args.get('offline') is True else None)
    except Exception as erro:
        resultado = {"status": "fallback", "motivo": f"adapter_error: {type(erro).__name__}",
                     "continue_with": "hermes", "executa_acao": False}
        if isinstance(args, dict) and args.get('operacao') == 'judge':
            resultado['veredito'] = 'revisao_humana'
    return json.dumps(resultado, ensure_ascii=False)


def register(ctx):
    ctx.register_tool(name="jev_workflows", toolset="jev_workflows", schema=SCHEMA, handler=handle)
