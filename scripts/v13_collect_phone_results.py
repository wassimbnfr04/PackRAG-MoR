"""Save original ADB JSON bytes after a complete successful instrumentation run."""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from scripts.v13_result_manifest import ROOT
from product.packrag.config import file_sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--files',required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT/'artifacts/v1.3')
    manifest=json.loads((run/'instrumentation-manifest.json').read_text())
    assert manifest['status']=='PASS' and manifest['variant'] in ('debug','demo')
    names=args.files.split(',');assert names and len(names)==len(set(names))
    assert all(re.fullmatch(r'[a-zA-Z0-9_.-]+\.json',name) and Path(name).name==name for name in names)
    raw=run/'original-adb';target=run/'collected-results.json';assert not raw.exists() and not target.exists()
    payloads={};commands=[];primary=[]
    for name in names:
        command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s',manifest['serial'],'shell','run-as','org.packrag.product','cat','files/'+name]
        started=datetime.now(timezone.utc).isoformat()
        result=subprocess.run(command,capture_output=True,timeout=30,check=True)
        parsed=json.loads(result.stdout);assert parsed['status']=='PASS',name
        if (run/name).exists():
            assert json.loads((run/name).read_text(encoding='utf-8'))==parsed,name
            primary.append(name)
        commands.append(dict(argv=command,started_at=started,ended_at=datetime.now(timezone.utc).isoformat(),
            returncode=result.returncode,stderr_utf8=result.stderr.decode('utf-8',errors='replace')))
        payloads[name]=result.stdout
    raw.mkdir();saved={}
    for name,payload in payloads.items():
        (raw/name).write_bytes(payload);saved[name]=hashlib.sha256(payload).hexdigest()
        if not (run/name).exists():
            with (run/name).open('xb') as output:output.write(payload)
    target.write_text(json.dumps(dict(status='PASS',recorded_utc=datetime.now(timezone.utc).isoformat(),
        collector_sha256=file_sha(Path(__file__)),serial=manifest['serial'],apk_sha256=manifest['apk_sha256'],
        saved_sha256=saved,formatted_primary_parsed_equal=primary,commands=commands,
        scope='ORIGINAL_RESULT_BYTES_FROM_THE_COMPLETED_SELECTED_RUN_NOT_NEW_INSTRUMENTATION'),indent=2)+'\n',encoding='utf-8')
    print('Collected original successful phone results:',len(saved),flush=True)


if __name__=='__main__':main()
