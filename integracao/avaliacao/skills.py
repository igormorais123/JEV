"""O Jev contra os oito regex de sugestão de skill que já rodam nesta máquina.

Esta é a aplicação que o estudo mediu, e não uma analogia: classificar o assunto de uma
mensagem em opções fechadas. A linha de base não é inventada — são os `hookify.suggest-skill-*`
que hoje disparam em todo prompt do Igor, por `regex_match`, e o E1 mediu exatamente esse
confronto: Jev 92,5% contra 60,0% da regra por palavra.

O que está em jogo em token: cada disparo do regex injeta um aviso no contexto de um modelo
caro. Um aviso errado é contexto pago à toa; um tema perdido faz o Opus trabalhar sem a skill
que existia para aquilo.

    python avaliacao/skills.py --rodar
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from jev_router import cliente  # noqa: E402

HOOKIFY = Path.home() / '.claude'
AMOSTRA = RAIZ / 'avaliacao' / 'amostra.json'
GABARITO = RAIZ / 'avaliacao' / 'gabarito-skills.json'
DESTINO = RAIZ / 'avaliacao' / 'skills-resultado.json'

# As descrições saem do que cada hook anuncia hoje ao Igor.
TEMAS = {
    'juridico': 'Petição, recurso, processo, jurisprudência, audiência, prazo judicial, cliente do escritório.',
    'comunicacao': 'Texto para publicar: post, matéria, roteiro, card, apresentação, site institucional, aula.',
    'estrategia': 'Decisão de negócio, plano, prioridade, proposta comercial, preço, posicionamento.',
    'google': 'Gmail, Drive, Agenda, Planilhas, Apps Script, Docs do Google.',
    'infra': 'Servidor, VPS, deploy, Docker, rede, backup, máquina, sistema operacional, ambiente.',
    'pesquisa': 'Levantar informação, buscar fonte, revisar literatura, investigar dados, comparar opções.',
    'relatorio': 'Produzir relatório, dossiê, documento formal de resultado, PDF de entrega.',
    'receita': 'Dinheiro entrando: proposta comercial, cliente novo, preço, contrato, faturamento.',
    'nenhum': 'Nenhum dos temas acima: é programação comum, conversa, ajuste de código ou operação do projeto.',
}

PERGUNTA = {'tema': {
    'type': 'choice',
    'instructions': ('Qual e o assunto do pedido abaixo, feito por um advogado que tambem '
                     'programa? Escolha o tema principal; se nenhum se aplicar, escolha '
                     '"nenhum".'),
    'criteria': {chave: valor.replace('ç', 'c').replace('ã', 'a').replace('í', 'i')
                 .replace('é', 'e').replace('ó', 'o').replace('â', 'a').replace('ú', 'u')
                 .replace('ê', 'e').replace('á', 'a')
                 for chave, valor in TEMAS.items()},
}}


def regexes():
    """Lê os regex que de fato rodam hoje, dos arquivos do hookify."""
    saida = {}
    for caminho in sorted(HOOKIFY.glob('hookify.suggest-skill-*.local.md')):
        texto = caminho.read_text(encoding='utf-8', errors='replace')
        nome = re.search(r'name: suggest-skill-(\S+)', texto)
        padrao = re.search(r'pattern: (.+)', texto)
        if nome and padrao:
            try:
                saida[nome.group(1)] = re.compile(padrao.group(1).strip(), re.IGNORECASE)
            except re.error:
                continue
    return saida


def pela_regra(pedido, padroes):
    """O que os hooks fariam hoje: todos os que casam disparam ao mesmo tempo."""
    return [tema for tema, padrao in padroes.items() if padrao.search(pedido)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rodar', action='store_true')
    args = parser.parse_args()

    amostra = json.loads(AMOSTRA.read_text(encoding='utf-8'))['amostra']
    padroes = regexes()
    print(f'regex carregados: {sorted(padroes)}')

    if not args.rodar:
        for caso in amostra:
            print(f"{caso['id']}: regra={pela_regra(caso['pedido'], padroes)} | "
                  f"{' '.join(caso['pedido'].split())[:90]}")
        return

    gabarito = json.loads(GABARITO.read_text(encoding='utf-8'))['gabarito']
    linhas = []
    for caso in amostra:
        respostas, detalhe = cliente.perguntar(f"Pedido do usuário:\n{caso['pedido']}",
                                               PERGUNTA, origem='skills')
        alvo = (respostas or {}).get('tema') or {}
        linhas.append({'id': caso['id'], 'jev': alvo.get('choice'),
                       'confianca': alvo.get('confidence'),
                       'regra': pela_regra(caso['pedido'], padroes),
                       'erro': None if respostas else (detalhe or {}).get('erro')})

    acertos_jev = acertos_regra = total = 0
    disparos_falsos_regra = disparos_regra = 0
    erros_jev = []
    for linha in linhas:
        esperado = (gabarito.get(linha['id']) or {}).get('tema')
        if not esperado or not linha['jev']:
            continue
        total += 1
        if linha['jev'] == esperado:
            acertos_jev += 1
        else:
            erros_jev.append({'id': linha['id'], 'esperado': esperado, 'jev': linha['jev'],
                              'confianca': linha['confianca']})
        # A regra acerta quando dispara exatamente o tema certo, e só ele. Disparar três
        # avisos, um deles certo, é o que ela faz hoje e é contexto pago.
        disparos_regra += len(linha['regra'])
        if linha['regra'] == [esperado] or (not linha['regra'] and esperado == 'nenhum'):
            acertos_regra += 1
        disparos_falsos_regra += sum(1 for t in linha['regra'] if t != esperado)

    resultado = {
        'casos': total,
        'jev': {'acuracia': round(acertos_jev / total, 4), 'erros': erros_jev},
        'regra': {'acuracia': round(acertos_regra / total, 4),
                  'disparos_totais': disparos_regra,
                  'disparos_falsos': disparos_falsos_regra},
        'distribuicao_jev': Counter(l['jev'] for l in linhas).most_common(),
        'distribuicao_gabarito': Counter(v['tema'] for v in gabarito.values()).most_common(),
        'linhas': linhas,
    }
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"\nJev:   {acertos_jev}/{total} = {acertos_jev / total:.1%}")
    print(f"Regra: {acertos_regra}/{total} = {acertos_regra / total:.1%} "
          f"({disparos_regra} avisos disparados, {disparos_falsos_regra} deles errados)")

    for corte in (0.90, 0.95, 0.99):
        aceitos = [l for l in linhas if (l['confianca'] or 0) >= corte and l['jev']]
        erros = [l['id'] for l in aceitos
                 if (gabarito.get(l['id']) or {}).get('tema') != l['jev']]
        print(f"  corte {corte}: {len(aceitos)}/{total} aceitos, {len(erros)} errados {erros}")


if __name__ == '__main__':
    main()
