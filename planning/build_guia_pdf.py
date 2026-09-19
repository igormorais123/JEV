"""Gera o PDF do guia prático, com a mesma tipografia do relatório final.

O guia é o documento para quem vai decidir o que fazer com o Jev, e não para quem vai auditar o
método. A capa traz os três números que essa decisão usa — quanto ele acerta, quanto custa a
revisão com e sem ele, e o que ainda não está resolvido — todos lidos do placar e do livro-caixa
na hora de gerar, nunca digitados aqui.

Uso:
    python planning/build_guia_pdf.py
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ORIGEM = ROOT / 'docs' / 'GUIA-PRATICO-JEV.md'
DESTINO = 'output/pdf/GUIA-PRATICO-JEV.pdf'
CORPORA = ('runs/e1-triagem/relatorio.json', 'runs/e7-confirmacao/relatorio.json',
           'runs/e11-desempate/relatorio.json', 'runs/e12-replicacao/relatorio.json')


def corte_que_zera_o_erro():
    """O corte de confiança que não deixa passar erro no corpus mais recente, e sua cobertura.

    A capa trazia o corte de 0,90 e a cobertura de 87,5% dos dois primeiros corpora — e o corpo
    do guia recomenda 0,99, porque no corpus novo o 0,90 deixa passar um erro com confiança 0,98.
    Capa contradizendo o documento é pior do que capa sem número.
    """
    import json
    e12 = ROOT / 'runs' / 'e12-replicacao' / 'relatorio.json'
    if not e12.exists():
        return None, '—'
    casos = json.loads(e12.read_text(encoding='utf-8'))['casos']
    gold = {c['case_id']: c['gold'] for c in casos}
    for corte in (0.90, 0.95, 0.99):
        aceitos = [c for c in casos if (c.get('jev_confidence') or 0) >= corte]
        if not [c for c in aceitos if c.get('jev') != gold[c['case_id']]]:
            return corte, f'{len(aceitos) / len(casos) * 100:.1f}'.replace('.', ',') + '%'
    return None, 'nenhum corte zera o erro'


def capa():
    from executor import gabarito, placar
    bloco = placar.montar()
    desempenho = gabarito.desempenho_do_estudo(CORPORA)
    faixa, _ = placar.faixa_dos_gabaritos(desempenho)
    corte, cobertura = corte_que_zera_o_erro()
    orcamento = bloco.get('orcamento') or {}
    gasto = orcamento.get('comprometido_nusd')
    gasto_txt = (f"US$ {gasto / 1e9:.9f}".replace('.', ',') if gasto is not None
                 else 'custo não disponível')
    return {
        'destino': DESTINO,
        'titulo_pdf': 'Jev - Guia prático de uso - Helena',
        'kicker': 'HELENA  /  PESQUISA APLICADA  /  GUIA DE DECISÃO',
        'titulo': 'O que fazer<br/>com o Jev.',
        'intro': ('Onde ele se destaca, quanto se ganha, onde é preciso ter cuidado e o que '
                  'ainda falta para decidir adoção.'),
        'metricas': [[faixa, cobertura, gasto_txt],
                     ['Acurácia nos 230 casos, entre os três gabaritos',
                      ('Resolvidas sem pessoa no corte de '
                       + (f'{corte:.2f}'.replace('.', ',') if corte else '—')
                       + ', sem erro observado'),
                      'Custo de toda a avaliação, de um teto de US$ 5']],
        'decisao': ('<b>Em uma frase</b><br/>O Jev funciona e supera com folga o método simples '
                    'que se usa hoje; o que ainda não está provado é que ele seja necessário '
                    'diante de um LLM genérico e barato — e essa dúvida não se resolve com mais '
                    'medição, e sim com dado real e anotação humana.'),
        'nota': ('Documento de decisão. O método, as contra-hipóteses e o histórico de revisão '
                 'estão no relatório final, em docs/RELATORIO-FINAL-JEV.md.'),
        'data': ('19 de setembro de 2026<br/>Todos os números são recalculados dos relatórios em '
                 'runs/ e do livro-caixa; nenhum é digitado à mão.'),
        'cabecalho': 'JEV  /  GUIA PRÁTICO  /  HELENA',
        'cabecalho_direita': '19.09.2026 · dados do E1 ao E12',
        'rodape': 'Guia prático. Decisão de uso, com os cuidados que os dados impõem.',
        'mapa': ('As seções 1 a 4 dizem para que serve e como aplicar, com exemplos reais. A 5 '
                 'e a 7 trazem os cuidados; a 6, os custos. A seção 8 trata dos 15 sistemas do '
                 'ecossistema e a 9 traz o placar de todos os experimentos, com a consequência '
                 'prática de cada um.'),
    }


def main():
    modulo = runpy.run_path(str(ROOT / 'planning' / 'build_deliverables.py'))
    alvo = Path(modulo['build_pdf'](ORIGEM.read_text(encoding='utf-8'), capa()))
    print(f'PDF do guia prático: {alvo.relative_to(ROOT)} '
          f'({alvo.stat().st_size / 1024:.0f} KB)')


if __name__ == '__main__':
    main()
