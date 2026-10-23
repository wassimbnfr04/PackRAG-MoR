"""Install project-local JDK/Gradle/SDK archives from upstream publishers."""
import hashlib
import json
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VENDOR=ROOT/'vendor'

def fetch(url,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        print('Downloading',url,flush=True)
        urllib.request.urlretrieve(url,target)
    print(target.name,target.stat().st_size,hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)

def unzip(path,target):
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            resolved=(target/info.filename).resolve()
            if not resolved.is_relative_to(target.resolve()): raise ValueError('Unsafe tooling path')
        z.extractall(target)

def main():
    jdk=VENDOR/'microsoft-jdk-17.0.20.1-windows-x64.zip'
    fetch('https://aka.ms/download-jdk/microsoft-jdk-17.0.20.1-windows-x64.zip',jdk)
    unzip(jdk,VENDOR/'java')
    gradle=VENDOR/'gradle-9.6.0-bin.zip'; fetch('https://services.gradle.org/distributions/gradle-9.6.0-bin.zip',gradle); unzip(gradle,VENDOR)
    with urllib.request.urlopen('https://dl.google.com/android/repository/repository2-3.xml') as r: xml=r.read()
    (ROOT/'artifacts/week1/environment/android_repository.xml').write_bytes(xml)
    doc=ET.fromstring(xml)
    packages=[e for e in doc.findall('remotePackage') if e.attrib['path'].startswith('cmdline-tools;')]
    stable=[e for e in packages if e.find('channelRef').attrib['ref']=='channel-0']
    chosen=max(stable,key=lambda e:tuple(int(e.find('revision').findtext(k,'0')) for k in ('major','minor','micro')))
    archive=next(e for e in chosen.findall('archives/archive') if e.findtext('host-os')=='windows')
    url=archive.findtext('complete/url'); path=VENDOR/Path(url).name; fetch('https://dl.google.com/android/repository/'+url,path)
    unzip(path,VENDOR/'android-cli')
    paths=dict(jdk=str(next((VENDOR/'java').glob('jdk-*'))),gradle=str(VENDOR/'gradle-9.6.0/bin/gradle.bat'),sdkmanager=str(VENDOR/'android-cli/cmdline-tools/bin/sdkmanager.bat'),sdk=str(VENDOR/'android-sdk'),cmdline_tools_package=chosen.attrib['path'])
    (ROOT/'artifacts/week1/environment/android_tool_paths.json').write_text(json.dumps(paths,indent=2),encoding='utf-8')
    print(paths,flush=True)

if __name__=='__main__':main()
