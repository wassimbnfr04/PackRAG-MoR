"""Read-only later shell clock/zone context; does not change phone time."""
import json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
target=HERE/'clock-context.json';assert not target.exists();records=[]
for name,args in [('shell-date',['date','+%Y-%m-%dT%H:%M:%S%z_%Z']),('shell-utc',['date','-u','+%Y-%m-%dT%H:%M:%S%z_%Z']),('epoch',['date','+%s']),('zone-property',['getprop','persist.sys.timezone'])]:
    command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell',*args];start=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,capture_output=True,check=True,timeout=30);(HERE/(name+'-stdout.txt')).write_bytes(result.stdout);(HERE/(name+'-stderr.txt')).write_bytes(result.stderr)
    records.append(dict(name=name,argv=command,started_host_utc=start,finished_host_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode,display=result.stdout.decode().strip()))
target.write_text(json.dumps(dict(status='LATER_READ_ONLY_SHELL_CLOCK_CONTEXT_NOT_RETROACTIVE_SYNC_OR_APP_ZONE_PROOF',commands=records,limits=['Shell date/epoch are observed later than initial process snapshot; no clocks changed','persist.sys.timezone string and observed shell UTC offset are distinct values; no Java app ZoneId assumption','Method intervals subtract same-device log timestamps; runner whole duration is recorded independently','First manual parenthesis-containing format failed remote shell parsing; corrected plain format succeeds; failed stderr remains only in tool transcript']),indent=2)+'\n')
print(json.dumps(dict(status='SAVED_READ_ONLY_CLOCK_CONTEXT',displays={r['name']:r['display'] for r in records})))
