"""Portable JSON CLI for the Jev harness agent API. Stdout is one JSON envelope."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from integracao.harness.agent_client import Client
from integracao.harness.agent_layer import API_VERSION, error_body


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['bootstrap','manifest','status','preview','submit','job','wait','logs','cancel','configure'])
    inputs=parser.add_mutually_exclusive_group()
    inputs.add_argument('--json',help='JSON arguments; for long text prefer --request file or stdin')
    inputs.add_argument('--request',help='UTF-8 JSON file with operation arguments, or - for stdin')
    args=parser.parse_args()
    try:
        raw=args.json or (sys.stdin.read() if args.request=='-' else Path(args.request).read_text(encoding='utf-8-sig') if args.request else '{}')
        arguments=json.loads(raw)
        if not isinstance(arguments,dict):raise ValueError('Arguments must be an object.')
        if args.operation=='bootstrap' and arguments:raise ValueError('bootstrap takes no arguments.')
        client=Client()
        data=client.bootstrap() if args.operation=='bootstrap' else client.call(args.operation,arguments)
        print(json.dumps({'api_version':API_VERSION,'ok':True,'data':data},ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps(error_body(error),ensure_ascii=False))
        return 1

if __name__=='__main__':raise SystemExit(main())
