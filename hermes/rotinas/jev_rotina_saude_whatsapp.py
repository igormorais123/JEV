#!/usr/bin/env python3
"""Saúde do coletor do WhatsApp pessoal, às 8h. Regra determinística: nada de modelo.

Os monitores do Fábio, a inteligência diária e o livro de pagamentos dependem do coletor. Ele
pode cair em silêncio (deslogado, aguardando novo pareamento) e as rotinas continuam rodando
sobre um banco parado. Esta rotina avisa quando o guardião marca o acesso como não saudável ou
quando a última mensagem capturada tem mais de 24 horas. Tudo em ordem: sem mensagem.
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import portao  # noqa: E402

STATUS = Path('/root/.hermes/state/whatsapp-personal/access-status.json')
BANCO = Path('/root/.hermes/state/whatsapp-personal/messages.sqlite')


def main():
    status = json.loads(STATUS.read_text(encoding='utf-8')) if STATUS.exists() else {}
    ultima = None
    if BANCO.exists():
        conexao = sqlite3.connect(f'file:{BANCO}?mode=ro', uri=True)
        ultima = conexao.execute('SELECT MAX(timestamp) FROM messages').fetchone()[0]
        conexao.close()
    horas = (time.time() - ultima) / 3600 if ultima else None
    problemas = []
    if not status.get('ok'):
        problemas.append(f"guardião marca acesso como '{status.get('state', 'desconhecido')}'")
    if horas is None or horas > 24:
        problemas.append('nenhuma mensagem capturada' if horas is None
                         else f'última mensagem capturada há {horas / 24:.1f} dia(s)'.replace('.', ','))
    portao.registrar('saude-whatsapp', bool(problemas), '; '.join(problemas) or 'coletor saudável')
    if not problemas:
        return
    print('⚠ Coletor do WhatsApp pessoal parado')
    print('Problema: ' + '; '.join(problemas) + '.')
    print('Efeito: monitores do Fábio, inteligência diária e livro de pagamentos estão lendo um banco parado.')
    if status.get('state') == 'pairing_pending':
        print('Para resolver: no PC, rode  C:\\Users\\IgorPC\\.hermes\\bin\\hermes-whatsapp-personal-access.ps1 '
              '-Action pair  e leia o QR com o celular.')


if __name__ == '__main__':
    main()
