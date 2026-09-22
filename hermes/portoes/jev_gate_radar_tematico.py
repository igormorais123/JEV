#!/usr/bin/env python3
"""Porteiro do job "Radar temático (IA setor público)" (`452a2e509020`, sexta 17h).

O mesmo porteiro acadêmico da tese, com o perfil de vigilância temática: consultas voltadas a
adoção de IA no setor público e ciência comportamental em políticas, com preferência por Brasil
e América Latina, e oito candidatos no contexto, porque o job pede três artigos.
"""
import sys

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import academico, portao  # noqa: E402

JOB = 'radar-tematico'

if __name__ == '__main__':
    portao.executar(JOB, lambda: academico.executar(JOB))
