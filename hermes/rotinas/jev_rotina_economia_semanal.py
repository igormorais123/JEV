#!/usr/bin/env python3
"""Resumo semanal da economia do Jev para o WhatsApp (segundas às 8h05)."""
import sys
from pathlib import Path

sys.argv.append('--semanal')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jev_rotina_economia import main  # noqa: E402

if __name__ == '__main__':
    main()
