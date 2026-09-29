"""CLI fallback for agents without the MCP loaded. Never prints exception contents."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integracao.jev_mcp import handle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--status', action='store_true')
    group.add_argument('--request', type=Path, help='JSON with name and arguments; no credentials')
    args = parser.parse_args()
    try:
        params = {'name': 'jev_status', 'arguments': {}} if args.status else json.loads(args.request.read_text(encoding='utf-8'))
        result = handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': params})
        print(json.dumps(result['result'], ensure_ascii=True))
        return int(result['result'].get('isError', False))
    except Exception as error:
        print(json.dumps({'status': 'abstain', 'error_type': type(error).__name__}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
