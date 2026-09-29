#!/usr/bin/env python3
"""Porteiro do job "Tese - parágrafo diário" (`8f2260d9fe4a`, 11h).

A busca acadêmica inteira é feita por código e pelo Jev; o agente acorda com os cinco melhores
candidatos ordenados e só confirma o DOI que escolher. A lógica e os perfis estão em
`jev_hermes/academico.py`; qualquer falha devolve o job ao comportamento antigo.
"""
import sys

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import academico, portao  # noqa: E402

JOB = 'tese-diaria'

if __name__ == '__main__':
    portao.executar(JOB, lambda: academico.executar(JOB))
