"""O preço declarado tem de ser o preço bruto do provedor, na unidade certa.

[R13] Ao declarar o comparador econômico do E10, escrevi `50_000` onde o correto era
`50_000_000`: US$ 0,00000005 por token são US$ 0,05 por milhão, que são 50 milhões de
nanodólares por milhão. O erro de três casas decimais teria feito a reserva bloquear mil vezes
menos do que a chamada poderia custar — e o executor financeiro inteiro existe para que a
reserva cubra o pior caso. Nada foi enviado com o valor errado, mas nada impedia.

Este teste refaz a conta a partir de `raw_pricing`, que é o que o provedor publica.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRECOS = ROOT / 'executor' / 'prices.json'
CAMPOS = (('prompt', 'input_nusd_per_million_tokens'),
          ('completion', 'output_nusd_per_million_tokens'))


class PrecoDeclaradoBateComOBruto(unittest.TestCase):

    def setUp(self):
        self.modelos = json.loads(PRECOS.read_text(encoding='utf-8'))['models']

    def test_cada_preco_declarado_deriva_do_preco_publicado(self):
        for nome, entrada in self.modelos.items():
            bruto = entrada.get('raw_pricing')
            if not bruto:
                continue
            for chave_bruta, chave_declarada in CAMPOS:
                if chave_bruta not in bruto or chave_declarada not in entrada:
                    continue
                with self.subTest(modelo=nome, campo=chave_declarada):
                    esperado = round(float(bruto[chave_bruta]) * 1e6 * 1e9)
                    self.assertEqual(entrada[chave_declarada], esperado,
                                     f'{nome}: {chave_declarada} não corresponde a '
                                     f'{bruto[chave_bruta]} USD por token')

    def test_tetos_de_reserva_sao_inteiros_positivos(self):
        for nome, entrada in self.modelos.items():
            with self.subTest(modelo=nome):
                for campo in ('context_length', 'max_completion_tokens'):
                    valor = entrada.get(campo)
                    self.assertIsInstance(valor, int, f'{nome}: {campo} não é inteiro')
                    self.assertGreater(valor, 0, f'{nome}: {campo} não é positivo')


if __name__ == '__main__':
    unittest.main()
