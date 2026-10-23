"""Copy only the existing public pinned5443-byte template from the phone for URI tests."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'template-fixture-custody.json';assert not target.exists()
destination=ROOT/'product/android/app/src/androidTest/assets/asset-import-source/template-valid.jinja';assert not destination.exists()
argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/models/chat_template.jinja']
output=subprocess.run(argv,capture_output=True,check=True,timeout=30)
digest=hashlib.sha256(output.stdout).hexdigest();assert len(output.stdout)==5443 and digest=='ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef'
destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(output.stdout)
record=dict(status='PASS_PUBLIC_OFFICIAL_TEMPLATE_FIXTURE_EXACT_PHONE_BYTES_NOT_IMPORT_TEST',recorded_utc=datetime.now(timezone.utc).isoformat(),
    file=destination.relative_to(ROOT).as_posix(),bytes=5443,sha256=digest,commands=[dict(argv=argv,returncode=output.returncode,stderr=output.stderr.decode('utf-8',errors='replace'))],
    scope='One exact known public template path read-only; source unchanged. No model weights/export/private-key/keystore read or hash. This is a test source for actual granted content-URI transport, not a replacement template or a claimed passing URI/native/UI test.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
