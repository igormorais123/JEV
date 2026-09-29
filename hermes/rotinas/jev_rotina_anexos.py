#!/usr/bin/env python3
"""Triagem de anexo recebido, duas vezes por dia (8h e 15h). Sem modelo principal.

O Jev diz que tipo de documento é cada anexo novo pelo nome e pelo assunto; quando o tipo tem
lista de checklist (peça processual, decisão judicial, contrato), o arquivo é baixado e auditado
(`jev_hermes/anexos.py`). Esta rotina avisa só o que acendeu VERMELHO — o resto fica no banco e
entra no painel da manhã. Sem vermelho, fica calada.
"""
import sys

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import anexos, portao  # noqa: E402

JOB = 'anexos'


def main():
    novidades, custo = anexos.atualizar(dias=3)
    portao.registrar(JOB, bool(novidades), f'{len(novidades)} anexo(s) com ponto vermelho',
                     custo_jev_usd=custo)
    if not novidades:
        return
    linhas = ['📎 Anexos recebidos — pontos que pedem leitura']
    for item in novidades:
        pontos = '; '.join(f"{v['item']} = {v['resposta']}" for v in item['vermelhos'])
        linhas.append(f"• {item['nome'][:70]} ({item['tipo']}) — de {item['de'][:40]}")
        linhas.append(f"  {pontos}")
    linhas.append('Triagem do Jev, não parecer: confira no documento antes de responder.')
    print('\n'.join(linhas))


if __name__ == '__main__':
    main()
