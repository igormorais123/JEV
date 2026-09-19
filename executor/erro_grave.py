"""Erro grave: confundir `cancelar` com qualquer outra classe, nos dois sentidos.

O pré-registro do E1 diz, desde 18/09/2026: "Erro grave é confundir `cancelar` com qualquer
outra classe, porque cancelar dispara ação irreversível no atendimento. **Reportado separadamente
da acurácia média.**" Ele nunca foi reportado. A décima terceira rodada de revisão adversarial
cobrou a falta, e a cobrança procede: acurácia média trata todos os erros como iguais, e a
métrica que o próprio protocolo declarou irreversível ficou de fora do relatório inteiro.

São dois erros distintos, e só um é irreversível:

- **falso `cancelar`** — o modelo diz `cancelar` onde o gabarito diz outra coisa. Dispara a ação
  irreversível. É o erro grave do pré-registro.
- **`cancelar` perdido** — o gabarito diz `cancelar` e o modelo diz outra coisa. Custa atraso,
  não destruição.

O limite superior é Clopper-Pearson unilateral a 95%, por família e por caso, porque com zero
erros observados a taxa pontual é 0 e só o limite diz alguma coisa.
"""
import json
from pathlib import Path

from .gabarito import adjudicado, do_anotador_local, do_autor
from .run_e9_prevalencia import limite_superior_erro

ROOT = Path(__file__).resolve().parents[1]
CLASSE_IRREVERSIVEL = 'cancelar'
# Os rotulos saem daqui direto para o painel, entao vao acentuados: o teste de localizacao
# pt-BR reprova qualquer texto publicado sem acento, e reprovou este.
RELATORIOS = {'piloto (E1)': 'runs/e1-triagem/relatorio.json',
              'confirmação (E7)': 'runs/e7-confirmacao/relatorio.json'}


def gabaritos():
    oficial, _ = adjudicado()
    return {'autor': {k: v['gold'] for k, v in do_autor().items()},
            'anotador local': do_anotador_local(),
            'oficial': {k: v['gold'] for k, v in oficial.items()}}


def medir(casos, ouro, campo='jev'):
    falsos, perdidos, familias_com_falso = [], [], set()
    familias = set()
    for caso in casos:
        alvo = ouro.get(caso['case_id'], caso['gold'])
        resposta = caso.get(campo)
        familias.add(caso['family'])
        if resposta == CLASSE_IRREVERSIVEL and alvo != CLASSE_IRREVERSIVEL:
            falsos.append(caso['case_id'])
            familias_com_falso.add(caso['family'])
        elif alvo == CLASSE_IRREVERSIVEL and resposta != CLASSE_IRREVERSIVEL:
            perdidos.append(caso['case_id'])
    n_casos, n_familias = len(casos), len(familias)
    return {
        'falso_cancelar': falsos,
        'cancelar_perdido': perdidos,
        'taxa_por_caso': round(len(falsos) / n_casos, 4) if n_casos else None,
        'limite_superior_por_caso': limite_superior_erro(len(falsos), n_casos),
        'familias_com_erro_grave': sorted(familias_com_falso),
        'limite_superior_por_familia': limite_superior_erro(len(familias_com_falso), n_familias),
        'casos': n_casos,
        'familias': n_familias,
    }


def relatorio():
    ouros = gabaritos()
    saida = {'definicao': ('erro grave = responder `cancelar` onde o gabarito diz outra coisa; '
                           'dispara ação irreversível. Pré-registrado no E1, seção "Erros '
                           'graves".'),
             'por_conjunto': {}}
    for nome, caminho in RELATORIOS.items():
        alvo = ROOT / caminho
        if not alvo.exists():
            continue
        dados = json.loads(alvo.read_text(encoding='utf-8'))
        bloco = {}
        for gab, ouro in ouros.items():
            bloco[gab] = {'jev': medir(dados['casos'], ouro, 'jev')}
            if 'regra' in (dados['casos'][0] if dados['casos'] else {}):
                bloco[gab]['regra'] = medir(dados['casos'], ouro, 'regra')
        saida['por_conjunto'][nome] = bloco
    return saida


if __name__ == '__main__':
    r = relatorio()
    destino = ROOT / 'runs' / 'erro-grave.json'
    destino.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
    for conjunto, bloco in r['por_conjunto'].items():
        print(f'== {conjunto}')
        for gab, quem in bloco.items():
            j = quem['jev']
            print(f"   {gab:15} jev: {len(j['falso_cancelar'])} falso-cancelar "
                  f"({j['falso_cancelar']}), {len(j['cancelar_perdido'])} perdido; "
                  f"teto por familia {j['limite_superior_por_familia']:.4f}")
            if 'regra' in quem:
                g = quem['regra']
                print(f"   {'':15} regra: {len(g['falso_cancelar'])} falso-cancelar, "
                      f"{len(g['cancelar_perdido'])} perdido")
    print(f'\nEscrito em {destino.relative_to(ROOT)}')
