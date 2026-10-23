"""Persist explicit human installer choice and new foreground authorization."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'visual3-running-0001.json';assert not target.exists()
note=('Separate visual0003 RUNNING '+datetime.now(timezone.utc).isoformat()+
    ' on frozen build0075/599 inputs/host73, run_visual_installed_0001.py verifying both '
    'installed public APK SHA256 values before instrumentation with no reinstall. '
    'Owner explicitly confirmed I chose Ne pas envoyer; continue, and a fresh four-minute '
    'unlocked untouched window, announced at launch. This human confirmation resolves the '
    'earlier unknown Play Protect choice without rewriting earlier observations; no APK '
    'upload/security-settings bypass by agent. Visual0001 install timeout and visual0002 '
    'observed PACKAGE UPDATED interruption remain FAIL with zero passed controls. '
    'No source/build/APK change until terminal/original collection; then independently '
    'review both unmodified PNGs. Known50/source4 unchanged after failed attempts. '
    'Eleven adjacent guard-only proposals prepared, not applied. F2 full closure pending, '
    'F3/F4 held; continuous all-M4 instruction active, final owner packs excluded, mobile data on.')
target.write_text(json.dumps(dict(status='RUNNING_SEPARATE_VISUAL3_NOT_ACCEPTED',note=note),indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    path=ROOT/name;header,rest=path.read_text(encoding='utf-8').split('\n',1)
    path.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print('RUNNING_SEPARATE_VISUAL3_NOT_ACCEPTED')
