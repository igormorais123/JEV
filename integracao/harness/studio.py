"""Studio wrapper: uses only the parent's local authenticated bridge."""
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'research/sources/jevstudio/framework'
sys.path.insert(0,str(path))
import framework_server as app

endpoint=os.environ.get('JEV_ENDPOINT','')
if not endpoint.startswith('http://127.0.0.1:'):
    raise RuntimeError('Studio deve ser iniciado por usar_ferramenta.py')
# Prevent an upstream dotenv from replacing the centrally managed route.
app._load_dotenv=lambda:None
app._endpoint=lambda:endpoint
app.main()
