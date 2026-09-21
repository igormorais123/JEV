#!/usr/bin/env python3
"""Agenda do dia, às 7h, com o Jev marcando o que exige preparo. Sem modelo principal.

O código lê os compromissos de hoje no Google Agenda; o Jev diz, para cada um, se exige
preparo (cliente, audiência, apresentação, prova, viagem), se é rotina ou pessoal. Dia sem
compromisso não gera mensagem.
"""
import json
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

FUSO = timezone(timedelta(hours=-3))
PERGUNTA = {
    'preparo': {
        'type': 'choice',
        'instructions': ('Compromisso na agenda de Igor, advogado e empresario. Ele precisa se preparar '
                         'antes (ler, levar material, estudar, deslocar-se com antecedencia)?'),
        'criteria': {
            'exige-preparo': 'Reuniao com cliente, audiencia, sustentacao, apresentacao, aula, prova ou viagem.',
            'rotina': 'Compromisso recorrente ou interno que dispensa preparo.',
            'pessoal': 'Compromisso pessoal ou de saude.',
            'nao-se-aplica': 'Lembrete ou marcacao sem compromisso real.',
        },
    },
}


def main():
    hoje = datetime.now(FUSO).replace(hour=0, minute=0, second=0, microsecond=0)
    saida = portao.rodar(['gws', 'calendar', 'events', 'list', '--params', json.dumps({
        'calendarId': 'primary', 'timeMin': hoje.isoformat(), 'timeMax': (hoje + timedelta(days=1)).isoformat(),
        'singleEvents': True, 'orderBy': 'startTime', 'maxResults': 30}), '--format', 'json'],
        env=portao.GWS_AMBIENTE)
    eventos = [e for e in portao.json_da_saida(saida).get('items', []) if e.get('status') != 'cancelled']
    if not eventos:
        portao.registrar('agenda-dia', False, 'dia sem compromisso')
        return
    estados = [f"TITULO: {e.get('summary', '')}\nLOCAL: {e.get('location', '')}\n"
               f"DESCRICAO: {(e.get('description') or '')[:1500]}" for e in eventos]
    resultados = nucleo.classificar_em_paralelo(estados, PERGUNTA, origem='rotina-agenda-dia',
                                                tempo_total=25, limite=3000)
    linhas = [f'📅 Agenda de hoje ({hoje:%d/%m}) — {len(eventos)} compromisso(s)']
    preparar = 0
    for e, (respostas, _) in zip(eventos, resultados):
        inicio = (e.get('start') or {})
        if inicio.get('dateTime'):
            quando = datetime.fromisoformat(inicio['dateTime']).astimezone(FUSO).strftime('%H:%M')
        else:
            quando = 'dia todo'
        classe, confianca = nucleo.escolha(respostas, 'preparo')
        marca = ''
        if classe == 'exige-preparo' and (confianca or 0) >= 0.6:
            marca = '  ⚠ preparar'
            preparar += 1
        local = f" — {e['location'][:60]}" if e.get('location') else ''
        linhas.append(f"• {quando} {e.get('summary', '(sem título)')[:90]}{local}{marca}")
    if preparar:
        linhas.append(f'{preparar} compromisso(s) marcado(s) pelo Jev como exigindo preparo.')
    portao.registrar('agenda-dia', True, f'{len(eventos)} compromisso(s), {preparar} com preparo',
                     custo_jev_usd=nucleo.resumo_das_chamadas(resultados)['custo_usd'])
    print('\n'.join(linhas))


if __name__ == '__main__':
    main()
