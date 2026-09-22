#!/usr/bin/env python3
"""Controle de prazos por e-mail, a cada 2 horas das 7h às 21h. Sem modelo principal.

O Jev tria a caixa, lê os fios que podem ter prazo e decide o prazo final de Igor e se ele já
entregou (`jev_hermes/prazos.py`). Esta rotina põe o prazo na agenda (dia anterior, 9h) e avisa
no WhatsApp só o que mudou: prazo novo, prazo que mudou de data, entrega reconhecida, ou fio que
pede conferência. Sem mudança, fica calada.
"""
import sys

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import portao, prazos  # noqa: E402

JOB = 'prazos'


def main():
    mudancas, custo = prazos.atualizar()
    novos = [m for m in mudancas if m['estado'] == 'pendente']
    entregues = [m for m in mudancas if m['estado'] == 'entregue' and m['antes'] in ('pendente', 'revisar')]
    conferir = [m for m in mudancas if m['estado'] == 'revisar' and m['antes'] != 'revisar']
    portao.registrar(JOB, bool(novos or entregues or conferir),
                     f'{len(novos)} prazo(s), {len(entregues)} entregue(s), {len(conferir)} a conferir',
                     custo_jev_usd=custo)
    if not (novos or entregues or conferir):
        return
    linhas = ['⚖️ Controle de prazos (Jev)']
    for m in sorted(novos, key=lambda x: x['prazo']):
        agenda = ' · na agenda' if m.get('agenda') in ('criado', 'movido') else ''
        linhas.append(prazos.linha_do_prazo(m) + agenda)
    for m in entregues:
        linhas.append(f"✅ entregue: {m['assunto'][:90]}")
    for m in conferir:
        linhas.append(prazos.linha_do_prazo(m))
    abertos = prazos.em_aberto()
    if len(abertos) > len(novos):
        linhas.append(f'Em aberto no total: {len(abertos)}.')
    print('\n'.join(linhas))


if __name__ == '__main__':
    main()
