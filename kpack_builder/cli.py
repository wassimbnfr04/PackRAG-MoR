import argparse
import json
import zipfile
from pathlib import Path
from nacl.signing import SigningKey
from .core import validate, query_identifier, write_archive, verified_manifest

def main():
    p=argparse.ArgumentParser(prog='kpack'); sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build'); b.add_argument('--out',type=Path,required=True)
    for name in ('validate','inspect','query'):
        s=sub.add_parser(name); s.add_argument('pack',type=Path); s.add_argument('--public-key',type=Path,required=True); s.add_argument('--developer-mode',action='store_true')
        if name=='query': s.add_argument('identifier')
    s=sub.add_parser('sign'); s.add_argument('directory',type=Path); s.add_argument('--key',type=Path,required=True); s.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.command=='build':
        from .build import build
        result=build(args.out)
    elif args.command=='sign':
        m=json.loads((args.directory/'manifest.json').read_bytes())
        payload={f['path']:(args.directory/f['path']).read_bytes() for f in m['files']}
        write_archive(args.out,m,payload,SigningKey(args.key.read_bytes())); result={'signed':str(args.out)}
    elif args.command=='query': result=query_identifier(args.pack,[args.public_key.read_bytes()],args.identifier,developer_mode=args.developer_mode)
    else: result=validate(args.pack,[args.public_key.read_bytes()],developer_mode=args.developer_mode)
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__': main()
