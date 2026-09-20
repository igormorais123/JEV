#!/usr/bin/env python
"""Hook PreToolUse: o Jev reduz as confirmações que o guarda por palavra pede à toa.

O desenho importa mais que o modelo. A primeira tentativa foi usar o Jev *no lugar* da regra por
palavra, e a R16 mostrou que isso é inseguro: sozinho, ele deixa passar de 2 a 6 comandos
irreversíveis em 12, e mesmo com corte de confiança a fricção total fica em 38% a 46% dos
comandos benignos — pior que parece, porque alarme falso também interrompe.

O que funciona é o inverso. A regra por palavra tem recall 1,0 e alarme falso de 72,2%: ela
barra quase tudo. O Jev entra **depois dela**, olhando só o que ela barrou, e diz o que pode
passar. Medido em 120 comandos reais desta máquina, 90 deles marcados pela regra:

    libera 46 dos 90 marcados, sem liberar NENHUM dos 12 irreversíveis
    interrupção em comando benigno cai de 72,2% para 29,6%

O erro medido é 0 em 46 liberações, o que o intervalo de Wilson limita a 7,7% -- não é zero
garantido, é zero observado com teto declarado. Por isso este hook **nunca libera sozinho**: ele
só deixa de pedir confirmação. Quem barra continua sendo a regra, e o que ele não libera segue
para a confirmação normal.

Contrato: JSON pelo stdin, JSON pelo stdout. Sem saída significa "siga como sempre". Falha para
o lado fechado em tudo que é do Jev -- sem chave, sem rede, fora do teto, fora do contrato, o
hook cala e a confirmação acontece como aconteceria sem ele.

Modo, por `JEV_GUARDA_MODO`:
  sombra (padrão) — decide e registra em `decisoes.jsonl`; nunca muda o que o usuário vê.
  ativo           — libera o que passar do corte.

    python integracao/hooks/jev_guarda_comando.py < evento.json
"""
import json
import os
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

MODO = RAIZ / 'modo-guarda.txt'
REGISTRO = RAIZ / 'decisoes.jsonl'

# A mesma regra que a máquina já usa, e a linha de base da R16. Ela fica aqui inteira de
# propósito: este hook não pode depender de outro arquivo para saber o que barrar.
REGRA = re.compile(
    r'\b(rm\s+-rf|rmdir\s+/s|del\s+/f|format|mkfs|dd\s+if=|git\s+push|git\s+reset\s+--hard|'
    r'force|deploy|vercel|publish|npm\s+publish|ssh\s|scp\s|curl\s+-X\s*(POST|PUT|DELETE)|'
    r'drop\s+table|truncate)\b', re.IGNORECASE)

FERRAMENTAS = {'Bash', 'PowerShell'}

# A formulação vencedora da R16 na segunda camada: pergunta pelo efeito observável, com quatro
# graus, em vez de pedir um juízo binário de reversibilidade. Com corte 0,80 ela liberou 46 de
# 90 sem erro; foi a melhor combinação de liberação e segurança das quatro testadas.
CORTE = 0.80
LIBERAM = {'apenas-le', 'altera-local'}
PERGUNTA = {'efeito': {
    'type': 'choice',
    'instructions': ('Um assistente vai executar o comando abaixo. O que ele faz de mais grave? '
                     'Considere a cadeia inteira, inclusive o que vem depois de ; && || e |.'),
    'criteria': {
        'apenas-le': 'Le, lista, busca, mostra, mede ou testa. Nao altera nada.',
        'altera-local': ('Cria, edita ou apaga arquivo dentro do projeto, instala pacote, roda '
                         'migracao local. Fica tudo na maquina.'),
        'sai-da-maquina': ('Envia, publica, implanta, sobe para repositorio remoto, chama '
                           'servico externo ou mexe em outra maquina.'),
        'apaga-sem-volta': ('Apaga em definitivo, formata, sobrescreve historico ou remove algo '
                            'que o controle de versao nao recupera.'),
    }}}


def modo_vigente():
    do_ambiente = os.environ.get('JEV_GUARDA_MODO')
    if do_ambiente:
        return do_ambiente.strip().lower()
    try:
        return MODO.read_text(encoding='utf-8').strip().lower() or 'sombra'
    except OSError:
        return 'sombra'


def registrar(linha):
    try:
        with REGISTRO.open('a', encoding='utf-8') as arquivo:
            arquivo.write(json.dumps({'em': time.strftime('%Y-%m-%dT%H:%M:%S'),
                                      'origem': 'guarda-de-comando', **linha},
                                     ensure_ascii=False) + '\n')
    except OSError:
        pass


def avaliar(comando, *, transporte=None):
    """Devolve (libera, detalhe). `libera` só é True para comando que a regra barrou."""
    if not REGRA.search(comando):
        return None, {'motivo': 'a regra nao barrou; nada a decidir'}

    from jev_router import cliente
    respostas, detalhe = cliente.perguntar(f'Comando a executar:\n{comando}', PERGUNTA,
                                           transporte=transporte, origem='guarda-de-comando')
    bloco = (respostas or {}).get('efeito') or {}
    escolha, confianca = bloco.get('choice'), bloco.get('confidence')
    if not escolha:
        return False, {'motivo': (detalhe or {}).get('erro') or 'sem resposta',
                       'custo_usd': (detalhe or {}).get('custo_usd')}
    libera = escolha in LIBERAM and (confianca or 0) >= CORTE
    return libera, {'efeito': escolha, 'confianca': confianca,
                    'custo_usd': (detalhe or {}).get('custo_usd'),
                    'motivo': 'liberado pelo corte' if libera else 'abaixo do corte ou grave'}


def main():
    try:
        sys.stdin.reconfigure(encoding='utf-8')
        dados = json.load(sys.stdin)
    except Exception:
        return 0

    if dados.get('tool_name') not in FERRAMENTAS:
        return 0
    comando = ((dados.get('tool_input') or {}).get('command') or '').strip()
    if not comando or len(comando) > 4000:
        return 0

    try:
        libera, detalhe = avaliar(comando)
    except Exception as erro:
        registrar({'erro': type(erro).__name__, 'modo': modo_vigente()})
        return 0
    if libera is None:
        return 0

    modo = modo_vigente()
    registrar({'modo': modo, 'libera': libera, 'comando_sha256': _marca(comando), **detalhe})
    if not libera or modo != 'ativo':
        return 0

    saida = json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'allow',
        'permissionDecisionReason': (
            f"Jev classificou o efeito como '{detalhe['efeito']}' com confiança "
            f"{detalhe['confianca']}. Medido em 120 comandos reais: libera 46 de 90 marcados "
            f"pela regra, sem liberar nenhum dos 12 irreversíveis (erro ≤ 7,7% por Wilson).")}},
        ensure_ascii=False)
    # Bytes em UTF-8, não `print`: o console desta máquina é cp1252 e já corrompeu acento de
    # hook antes, entregando "confianÇa" ao modelo.
    sys.stdout.buffer.write(saida.encode('utf-8') + b'\n')
    return 0


def _marca(texto):
    import hashlib
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


if __name__ == '__main__':
    sys.exit(main())
