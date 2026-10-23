"""Sequential source-bound regression and real walking smoke for D3 iterations.

This is an intermediate integration gate, never final milestone acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from scripts.v13_result_manifest import ROOT, digest, public_source_files


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--regression',type=Path,required=True)
    parser.add_argument('--smoke',type=Path,required=True)
    args=parser.parse_args()
    run=(ROOT/args.run).resolve()
    regression=(ROOT/args.regression).resolve()
    smoke=(ROOT/args.smoke).resolve()
    for path in (run,regression,smoke):
        if not path.is_relative_to(ROOT/'artifacts/v1.3/m4') or path.exists():
            raise RuntimeError('Use fresh workspace M4 evidence directories')
    run.mkdir(parents=True)
    sources={path.relative_to(ROOT).as_posix():digest(path) for path in public_source_files(ROOT)}
    def save(name,value):
        (run/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    save('inputs.json',{'source_sha256':sources,'scope':'INTERMEDIATE_D3_NOT_MILESTONE_ACCEPTANCE'})
    env=dict(os.environ)
    temp=run/'host-temp';temp.mkdir()
    env['TEMP']=env['TMP']=str(temp)
    results=[]
    def execute(name,command):
        start=datetime.now(timezone.utc).isoformat()
        with (run/(name+'.stdout.txt')).open('wb') as out,(run/(name+'.stderr.txt')).open('wb') as err:
            child=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err)
        row={'name':name,'command':command,'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':child.returncode}
        results.append(row);save('execution.json',results)
        print(name,child.returncode,flush=True)
        return child.returncode
    command=[sys.executable,'-X','utf8','-m','pytest','tests','product/tests','-p','no:cacheprovider',
             '--basetemp',str(regression)+'-temp','--junitxml',str(regression/'combined-junit.xml'),'-q']
    code=execute('regression',command)
    manifest=execute('regression-manifest',[sys.executable,'-X','utf8','-m','scripts.v13_result_manifest',str(regression),'--command',' '.join(command)])
    if code or manifest:
        raise RuntimeError('Regression failure: do not progress')
    if execute('real-walking',[sys.executable,'-X','utf8','-m','scripts.v13_smoke','--run',str(smoke)]):
        raise RuntimeError('Real walking failure: do not progress')
    changed=[name for name,value in sources.items() if digest(ROOT/name)!=value]
    current={p.relative_to(ROOT).as_posix() for p in public_source_files(ROOT)}
    if changed or current!=set(sources):
        raise RuntimeError('Source changed during validation')
    save('result.json',{'status':'PASS','scope':'INTERMEDIATE_D3_NOT_MILESTONE_ACCEPTANCE',
         'regression':str(regression.relative_to(ROOT)),'real_walking':str(smoke.relative_to(ROOT)),
         'sources_unchanged':len(sources),'executions':results})
    print('Intermediate D3 regression and real walking PASS',flush=True)


if __name__=='__main__':main()
