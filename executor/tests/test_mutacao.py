"""Auditoria de mutação: perturbar o dado bruto tem de mover o painel.

[R13] Foi assim que a décima terceira rodada achou dois cartões cegos. Os testes de coerência
comparam o painel publicado com o painel gerado, e os dois batiam — porque os dois liam o mesmo
número congelado. Um número gravado dentro do relatório no momento em que o experimento rodou
parece correto exatamente enquanto ninguém mexe nos dados.

O teste troca cinco acertos por erros em cada relatório que tem lista de casos e exige que algum
cartão do painel mude. Um cartão que não reage ao próprio dado não está medindo o dado.
"""
import importlib
import json
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / 'runs'
CLASSE_QUE_NAO_EXISTE = 'classe-inexistente-para-forcar-erro'


def montar():
    from executor import gabarito, placar
    importlib.reload(gabarito)
    importlib.reload(placar)
    return placar.montar()


def relatorios_com_casos():
    achados = []
    for fonte in sorted(RUNS.glob('*/relatorio.json')):
        casos = json.loads(fonte.read_text(encoding='utf-8')).get('casos')
        if isinstance(casos, list) and casos and isinstance(casos[0], dict) and 'gold' in casos[0]:
            achados.append(fonte)
    return achados


@unittest.skipUnless(relatorios_com_casos(), 'nenhum experimento executado')
class OPainelReageAoDadoBruto(unittest.TestCase):

    def test_trocar_acertos_por_erros_move_algum_cartao(self):
        base = montar()
        for fonte in relatorios_com_casos():
            with self.subTest(relatorio=fonte.name):
                copia = fonte.with_suffix('.mutacao-bkp')
                shutil.copy(fonte, copia)
                try:
                    dados = json.loads(fonte.read_text(encoding='utf-8'))
                    trocados = 0
                    for caso in dados['casos']:
                        if caso.get('jev') and caso['jev'] == caso.get('gold'):
                            caso['jev'] = CLASSE_QUE_NAO_EXISTE
                            trocados += 1
                            if trocados >= 5:
                                break
                    self.assertTrue(trocados, f'{fonte.name} não tinha acerto para mutar')
                    fonte.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                                     encoding='utf-8')
                    novo = montar()
                    mudaram = [c['chave'] for c, b in zip(novo['cartoes'], base['cartoes'])
                               if c != b]
                    self.assertTrue(mudaram,
                                    f'{trocados} acertos viraram erro em {fonte.name} e nenhum '
                                    'cartão do painel se mexeu: algum número está congelado')
                finally:
                    shutil.copy(copia, fonte)
                    copia.unlink()
        montar()


if __name__ == '__main__':
    unittest.main()
