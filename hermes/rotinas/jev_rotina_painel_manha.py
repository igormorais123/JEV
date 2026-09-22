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
from jev_hermes import nucleo, pendencias, portao, prazos  # noqa: E402

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


GESTO_DO_PEDIDO = {
    'responder': 'responder {c}', 'decidir': 'decidir e responder {c}', 'pagamento': 'conferir o pagamento com {c}',
    'enviar-algo': 'enviar a {c} o que pediu', 'agendar': 'confirmar o horário com {c}',
}


def whatsapp():
    """Pendências do WhatsApp pessoal: quem espera Igor e o que ele prometeu e não cumpriu."""
    esperando, _ = pendencias.esperando_igor()
    promessas, _ = pendencias.promessas_abertas()
    itens = []
    for c in esperando:
        itens.append({'tipo': 'whatsapp', 'titulo': f"{c['contato']} espera você: {c['trecho'][:70]}",
                      'gesto': GESTO_DO_PEDIDO.get(c['pedido'], 'responder {c}').format(c=c['contato']),
                      'estado': 'PENDENCIA NO WHATSAPP (contato espera Igor):\n' + c['estado'][-2500:]})
    for c in promessas:
        itens.append({'tipo': 'whatsapp', 'titulo': f"Você prometeu a {c['contato']}: {c['trecho'][:70]}",
                      'gesto': f"cumprir ou dar retorno a {c['contato']}",
                      'estado': f"PROMESSA DE IGOR AINDA SEM ENTREGA, para {c['contato']}:\n{c['trecho']}"})
    return itens, None


def prazos_abertos():
    """Prazos de e-mail em aberto nos próximos 10 dias (controle de prazos do Jev)."""
    itens = []
    for l in prazos.em_aberto(dias_a_frente=10):
        if l['estado'] != 'pendente':
            continue
        dia = l['prazo'][8:10] + '/' + l['prazo'][5:7]
        itens.append({'tipo': 'prazo', 'titulo': f"Prazo {dia}: {l['assunto'][:90]}",
                      'gesto': f"entregar até a véspera ({dia} é o prazo final)", 'prazo': dia,
                      'faltam': (datetime.fromisoformat(l['prazo']).date() - datetime.now(FUSO).date()).days,
                      'estado': f"PRAZO FINAL DE IGOR EM {l['prazo']}: {l['assunto']}\n{l['evidencia'] or ''}"})
    return itens, None


def main():
    hoje = datetime.now(FUSO).replace(hour=0, minute=0, second=0, microsecond=0)
    itens = []
    avisos = []
    for fonte in (lambda: (compromissos(hoje), None), demandas, whatsapp, prazos_abertos):
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
        if item['tipo'] == 'prazo' and item.get('faltam', 99) <= 2:
            item['nota'] = 3   # regra fixa: prazo final em até dois dias é sempre urgente
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
    vencendo = [i for i in itens if i['tipo'] == 'prazo']
    if vencendo:
        linhas.append(f'⚖️ Prazos ({len(vencendo)}): ' + '; '.join(i['titulo'][:80] for i in vencendo[:4]) + '.')
    zap = [i for i in itens if i['tipo'] == 'whatsapp']
    if zap:
        linhas.append(f'💬 WhatsApp ({len(zap)}): ' + '; '.join(i['titulo'][:80] for i in zap[:4])
                      + ('; …' if len(zap) > 4 else '') + '.')
    if avisos:
        linhas.append('Obs.: ' + '; '.join(avisos) + '.')
    portao.registrar('painel-manha', True, f"prioridade: {topo['tipo']}", itens=len(itens),
                     custo_jev_usd=nucleo.resumo_das_chamadas(resultados)['custo_usd'])
    print('\n'.join(linhas))


if __name__ == '__main__':
    main()
