"""A rotina que mantém a medição viva sem ninguém lembrar de rodá-la.

    python integracao/camadas/rotina.py            # mede, concilia, regera, audita, commita
    python integracao/camadas/rotina.py --so-medir # só a página das camadas (rápido, para o fim de sessão)

Roda em dois lugares: no `SessionEnd` do Claude Code (só a medição, para a página estar
fresca ao fim de cada sessão) e numa tarefa agendada do Windows, uma vez por dia (a rotina
inteira). O que ela faz, na ordem, cada passo só se o anterior passou:

1. `medir.py --gravar`: recalcula `docs/CAMADAS-CLAUDE-CODE.md` do registro das camadas.
2. `conciliar_caixa.py --gravar`: as chamadas dos hooks entram no livro-caixa e o guia
   precisa declarar o total certo, senão a auditoria quebra ("quem gasta atualiza o número").
3. Regera as páginas que citam o caixa (cem hipóteses, cem perguntas, dossiê, bateria).
4. `auditoria.py`: reconfere cada número publicado; se algo não fechar, a rotina PARA e
   não commita, e o motivo fica no log.
5. Commit local, por lista explícita de arquivos, só se houver mudança. Nunca faz push.

Nada aqui chama o Jev nem gasta dinheiro. Log em `integracao/estado/rotina.log`; a última
execução fica em `integracao/estado/rotina-ultima.json`, e a página de medição a exibe.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PROJETO = RAIZ.parent
ESTADO = RAIZ / 'estado'
LOG = ESTADO / 'rotina.log'
ULTIMA = ESTADO / 'rotina-ultima.json'

ARQUIVOS_DO_COMMIT = [
    'docs/CAMADAS-CLAUDE-CODE.md', 'integracao/avaliacao/camadas-medicao.json',
    'docs/GUIA-PRATICO-JEV.md', 'docs/CEM-HIPOTESES.md', 'docs/CEM-PERGUNTAS-ESTRATEGICAS.md',
    'docs/DOSSIE-DE-EVIDENCIAS.md', 'docs/BATERIA-COMPLEMENTAR.md', 'docs/AUDITORIA-DE-NUMEROS.md',
    'runs/extrato-ledger.json',
]

PASSOS_COMPLETOS = [
    ('medir', [sys.executable, 'integracao/camadas/medir.py', '--gravar']),
    ('conciliar', [sys.executable, 'laboratorio/conciliar_caixa.py', '--gravar']),
    ('cem hipoteses', [sys.executable, '-m', 'laboratorio.h100.relatorio']),
    ('cem perguntas', [sys.executable, '-m', 'laboratorio.q100.relatorio']),
    ('dossie', [sys.executable, 'laboratorio/gerar_dossie.py']),
    ('bateria', [sys.executable, 'laboratorio/gerar_bateria.py']),
    ('auditoria', [sys.executable, 'laboratorio/auditoria.py']),
]


def _log(mensagem):
    ESTADO.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as arquivo:
        arquivo.write(f'{time.strftime("%Y-%m-%dT%H:%M:%S")} {mensagem}\n')


def _rodar(nome, comando, tempo=300):
    inicio = time.time()
    proc = subprocess.run(comando, cwd=str(PROJETO), capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=tempo)
    duracao = round(time.time() - inicio, 1)
    cauda = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or ['']
    _log(f'{nome}: código {proc.returncode} em {duracao}s — {cauda[0][:160]}')
    return proc.returncode == 0, cauda[0]


def _commit(passos):
    subprocess.run(['git', 'add', '--'] + ARQUIVOS_DO_COMMIT, cwd=str(PROJETO), capture_output=True)
    mudou = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=str(PROJETO)).returncode == 1
    if not mudou:
        _log('commit: nada mudou')
        return False
    mensagem = ('chore: medição automática das camadas do Jev\n\n'
                f'Rotina diária: {", ".join(passos)}. Sem chamada paga; sem push.\n\n'
                'Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n')
    proc = subprocess.run(['git', 'commit', '-q', '-F', '-'], cwd=str(PROJETO), input=mensagem,
                          capture_output=True, text=True, encoding='utf-8')
    _log(f'commit: código {proc.returncode} {proc.stderr.strip()[:120]}')
    return proc.returncode == 0


def executar(so_medir=False):
    passos = PASSOS_COMPLETOS[:1] if so_medir else PASSOS_COMPLETOS
    feitos = []
    resultado = {'em': time.strftime('%Y-%m-%dT%H:%M:%S'), 'modo': 'so-medir' if so_medir else 'completa',
                 'ok': True, 'passos': feitos, 'commit': False}
    for nome, comando in passos:
        ok, cauda = _rodar(nome, comando)
        feitos.append({'passo': nome, 'ok': ok, 'saida': cauda[:160]})
        if not ok:
            resultado.update({'ok': False, 'parou_em': nome})
            break
    if resultado['ok'] and not so_medir:
        resultado['commit'] = _commit([p['passo'] for p in feitos])
    ESTADO.mkdir(parents=True, exist_ok=True)
    ULTIMA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--so-medir', action='store_true')
    args = parser.parse_args()
    resultado = executar(args.so_medir)
    print(json.dumps({k: v for k, v in resultado.items() if k != 'passos'}, ensure_ascii=False))
    return 0 if resultado['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
