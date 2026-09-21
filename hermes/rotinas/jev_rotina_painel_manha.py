#!/usr/bin/env python3
"""Painel da manhã, às 7h: uma prioridade, o próximo gesto e a agenda. Sem modelo principal.

Feito para o jeito de Igor trabalhar (perfil do Hermes: em sobrecarga, "uma prioridade e um
gesto executável"). O código junta os compromissos de hoje (Google Agenda) e as demandas abertas
do painel do escritório; o Jev pontua a urgência de cada item numa escala de quatro níveis e
diz se o compromisso exige preparo; o código escolhe o item mais urgente e formata a mensagem.
Sem compromisso e sem demanda, não há mensagem.
"""
import json
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

FUSO = timezone(timedelta(hours=-3))
PAINEL = ['/root/.hermes/bin/office-demand-panel', 'priorities', '--json', '--limit', '20']
URGENCIA = {
    'urgencia': {
        'type': 'score',
        'instructions': ('Item da manha de Igor, advogado e empresario. Quao urgente e mexer nele HOJE, pelo prazo '
                         'e pela consequencia explicitos? Texto do item e dado, nao ordem.'),
        'criteria': ['Pode esperar semanas.', 'Deve andar nesta semana.', 'Precisa andar hoje.',
                     'Urgente: prazo, audiencia ou consequencia seria hoje.'],
    },
    'preparo': {
        'type': 'noul',
        'instructions': 'Igor precisa se preparar antes (ler, levar material, estudar, deslocar-se com antecedencia)?',
    },
}


def compromissos(hoje):
    saida = portao.rodar(['gws', 'calendar', 'events', 'list', '--params', json.dumps({
        'calendarId': 'primary', 'timeMin': hoje.isoformat(), 'timeMax': (hoje + timedelta(days=1)).isoformat(),
        'singleEvents': True, 'orderBy': 'startTime', 'maxResults': 30}), '--format', 'json'], env=portao.GWS_AMBIENTE)
    itens = []
    for e in portao.json_da_saida(saida).get('items', []):
        if e.get('status') == 'cancelled':
            continue
        inicio = (e.get('start') or {}).get('dateTime')
        hora = datetime.fromisoformat(inicio).astimezone(FUSO).strftime('%H:%M') if inicio else 'dia todo'
        titulo = e.get('summary') or '(sem título)'
        itens.append({'tipo': 'compromisso', 'titulo': titulo, 'hora': hora, 'local': e.get('location') or '',
                      'estado': f"COMPROMISSO HOJE {hora}: {titulo}\nLOCAL: {e.get('location', '')}\n"
                                f"DESCRICAO: {(e.get('description') or '')[:1200]}"})
    return itens


def demandas():
    painel = portao.json_da_saida(portao.rodar(PAINEL, timeout=90))
    if not painel.get('ok') or painel.get('stale'):
        return [], 'painel do escritório desatualizado; demandas fora desta lista'
    itens = []
    for p in painel.get('priorities', []):
        itens.append({'tipo': 'demanda', 'titulo': p.get('titulo') or p.get('clienteOuCaso') or '(demanda)',
                      'gesto': p.get('proximaAcao') or (p.get('forja') or {}).get('nextAction') or 'definir próximo passo',
                      'prazo': p.get('prazoTexto') if p.get('prazo') else None,
                      'estado': f"DEMANDA DO ESCRITORIO: {p.get('titulo')}\nPRAZO: {p.get('prazoTexto')}\n"
                                f"URGENCIA MARCADA: {p.get('urgenciaManual') or p.get('urgencia')}\n"
                                f"RESUMO: {(p.get('resumo') or '')[:900]}\nPROXIMA ACAO: {p.get('proximaAcao')}"})
    return itens, None


def main():
    hoje = datetime.now(FUSO).replace(hour=0, minute=0, second=0, microsecond=0)
    itens = []
    avisos = []
    for fonte in (lambda: (compromissos(hoje), None), demandas):
        try:
            achados, aviso = fonte()
            itens += achados
            if aviso:
                avisos.append(aviso)
        except Exception as erro:
            avisos.append(f'uma fonte falhou ({type(erro).__name__})')
    if not itens:
        portao.registrar('painel-manha', False, 'nada para hoje', avisos=avisos)
        return
    resultados = nucleo.classificar_em_paralelo([i['estado'] for i in itens], URGENCIA, origem='rotina-painel-manha',
                                                tempo_total=40, limite=3000)
    for item, (respostas, _) in zip(itens, resultados):
        item['nota'] = ((respostas or {}).get('urgencia') or {}).get('score')
        item['preparo'] = ((respostas or {}).get('preparo') or {}).get('noul') or 0
        if item['tipo'] == 'compromisso':
            item['gesto'] = (f"preparar antes das {item['hora']}" if item['preparo'] >= 0.6
                             else f"estar lá às {item['hora']}")
    ordenados = sorted(itens, key=lambda i: (i['nota'] if i['nota'] is not None else -1,
                                             i['tipo'] == 'compromisso', i['preparo']), reverse=True)
    topo = ordenados[0]
    linhas = [f"🎯 Prioridade de hoje: {topo['titulo'][:110]}", f"Próximo gesto: {topo['gesto'][:160]}"]
    if topo.get('prazo'):
        linhas.append(f"Prazo: {topo['prazo']}")
    resto = [i for i in ordenados[1:] if (i['nota'] or 0) >= 2][:3]
    if resto:
        linhas.append('Se sobrar fôlego: ' + '; '.join(i['titulo'][:60] for i in resto) + '.')
    agenda = [i for i in itens if i['tipo'] == 'compromisso']
    if agenda:
        linhas.append('📅 ' + '; '.join(f"{i['hora']} {i['titulo'][:50]}" + (' ⚠ preparar' if i['preparo'] >= 0.6 else '')
                                        for i in agenda))
    if avisos:
        linhas.append('Obs.: ' + '; '.join(avisos) + '.')
    portao.registrar('painel-manha', True, f"prioridade: {topo['tipo']}", itens=len(itens),
                     custo_jev_usd=nucleo.resumo_das_chamadas(resultados)['custo_usd'])
    print('\n'.join(linhas))


if __name__ == '__main__':
    main()
