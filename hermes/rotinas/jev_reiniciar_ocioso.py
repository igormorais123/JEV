#!/usr/bin/env python3
"""Reinicia o hermes-gateway só quando Igor está ocioso há 15 min (carrega o plugin novo)."""
import sqlite3, subprocess, time
LOG = '/root/.hermes/logs/jev-reinicio-ocioso.log'
def log(m):
    open(LOG, 'a').write(time.strftime('%Y-%m-%dT%H:%M:%SZ ', time.gmtime()) + m + '\n')
inicio = time.time()
while time.time() - inicio < 4 * 3600:
    c = sqlite3.connect('file:/root/.hermes/state.db?mode=ro', uri=True)
    ultimo = c.execute('select max(timestamp) from messages').fetchone()[0] or 0
    c.close()
    if time.time() - ultimo > 15 * 60:
        r = subprocess.run(['systemctl', 'restart', 'hermes-gateway'], capture_output=True, text=True)
        time.sleep(10)
        ativo = subprocess.run(['systemctl', 'is-active', 'hermes-gateway'], capture_output=True, text=True).stdout.strip()
        log(f'reiniciado (ocioso ha {round((time.time()-ultimo)/60)} min): rc={r.returncode} estado={ativo}')
        break
    time.sleep(60)
else:
    log('desisti: 4 h sem ociosidade; reinicie a mao')
