"""Cumulative observed runner events across saved log snapshots; terminal JUnit remains authoritative."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;folder=HERE/'development-progress'
finished=set();failed=set();latest=None
for p in sorted(folder.glob('*.txt')):
    for line in p.read_text(encoding='utf-8').splitlines():
        if ' I TestRunner: finished: ' in line:finished.add(line.split(' I TestRunner: finished: ',1)[1])
        if ' E TestRunner: failed: ' in line:failed.add(line.split(' E TestRunner: failed: ',1)[1])
        if ' I TestRunner: started: ' in line:latest=line.split(' I TestRunner: started: ',1)[1]
print(json.dumps(dict(cumulative_observed_finished_methods=len(finished),cumulative_observed_failed_methods=len(failed),latest_observed_method=latest,
    scope='Union of retained PID12346 log snapshots; it is a lower bound if any event was never captured. Full terminal JUnit/original custody determines37-method acceptance.')))
