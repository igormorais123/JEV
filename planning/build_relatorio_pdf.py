"""Gera o PDF do relatório final, reaproveitando a tipografia do plano — e só ela.

[R13] A primeira versão chamava `build_pdf()` e copiava o arquivo que ele gravava. Como aquele
gerador escrevia sempre no caminho do plano e montava sempre a capa do plano, cada build do
relatório destruía o PDF do plano científico e produzia um relatório que abria anunciando
"ensaios dos sistemas ainda pendentes" — depois de todos os ensaios terminados. Os dois PDFs
ficaram byte a byte idênticos e assim foram versionados. Aqui o relatório traz a própria capa, e
os números dela saem do placar, não da memória.

Uso:
    python planning/build_relatorio_pdf.py
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ORIGEM = ROOT / 'docs' / 'RELATORIO-FINAL-JEV.md'
DESTINO = 'output/pdf/RELATORIO-FINAL-JEV.pdf'


def capa():
    from executor import gabarito, placar
    bloco = placar.montar()
    d80 = gabarito.desempenho_do_estudo()
    faixa, _ = placar.faixa_dos_gabaritos(d80)
    orcamento = bloco.get('orcamento') or {}
    gasto = orcamento.get('comprometido_nusd')
    gasto_txt = (f"US$ {gasto / 1e9:.9f}".replace('.', ',') if gasto is not None
                 else 'custo não disponível')
    veredito = bloco['veredito']
    return {
        'destino': DESTINO,
        'titulo_pdf': 'Jev - Relatório final de avaliação - Helena',
        'kicker': 'HELENA  /  PESQUISA APLICADA  /  RELATÓRIO FINAL',
        'titulo': 'Testamos todos.<br/>Este é o resultado.',
        'intro': veredito['titulo'] + '.',
        'metricas': [[f"{d80['casos_programados']} casos", faixa, gasto_txt],
                     ['Piloto e confirmação, famílias distintas',
                      'Faixa entre os três gabaritos concorrentes',
                      'Gasto acumulado dentro do teto de US$ 5']],
        'decisao': '<b>Veredito</b><br/>' + veredito['texto'],
        'nota': (f"Confiança {str(veredito['confianca']).replace('.', ',')} em 1,0, por descontos "
                 'declarados. Os motivos de cada desconto estão no painel e na seção 9.'),
        'data': ('19 de setembro de 2026<br/>Todos os números deste documento são recalculados a '
                 'partir dos relatórios em runs/ e do livro-caixa; nenhum é digitado à mão.'),
        'rodape': 'Relatório final. Ensaios concluídos; números recalculados dos dados brutos.',
        'mapa': ('Comece pelas seções 1 e 3. O método está nas seções 2 e 4 a 6. As ressalvas, o '
                 'que não foi testado e o histórico de revisão fecham o documento.'),
    }


def main():
    modulo = runpy.run_path(str(ROOT / 'planning' / 'build_deliverables.py'))
    alvo = Path(modulo['build_pdf'](ORIGEM.read_text(encoding='utf-8'), capa()))
    print(f'PDF do relatório final: {alvo.relative_to(ROOT)} '
          f'({alvo.stat().st_size / 1024:.0f} KB)')


if __name__ == '__main__':
    main()
