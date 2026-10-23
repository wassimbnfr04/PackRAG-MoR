import json
import os
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import hashlib
import copy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def write_package_metadata(repository, node, target):
    # Archives contain legacy source.properties, which cannot describe the new
    # decimal API levels. Supply SDK-local metadata copied from Google's index.
    root=ET.Element('{http://schemas.android.com/repository/android/common/02}repository',{
        'xmlns:sdk':'http://schemas.android.com/sdk/android/repo/repository2/03',
        'xmlns:generic':'http://schemas.android.com/repository/android/generic/02'})
    for license in repository.findall('license'):root.append(copy.deepcopy(license))
    local=copy.deepcopy(node);local.tag='localPackage'
    for tag in ['archives','channelRef']:
        for child in local.findall(tag):local.remove(child)
    root.append(local)
    ET.ElementTree(root).write(target/'package.xml',encoding='utf-8',xml_declaration=True)

def main():
    paths=json.loads((ROOT/'artifacts/week1/environment/android_tool_paths.json').read_text())
    env=os.environ.copy();env['JAVA_HOME']=paths['jdk'];env['ANDROID_USER_HOME']=str(ROOT/'.cache/android')
    Path(env['ANDROID_USER_HOME']).mkdir(parents=True,exist_ok=True)
    sdk=paths['sdk']
    base=[paths['sdkmanager'],'--sdk_root='+sdk]
    subprocess.run(base+['--licenses'],input='y\n'*200,text=True,env=env,check=True)
    # Command-line tools 23 forwards legacy semicolon IDs incorrectly to its new
    # Android CLI. Use the checksummed upstream repository archives directly.
    packages={'platforms;android-37.0':'platforms/android-37.0',
              'build-tools;37.0.0':'build-tools/37.0.0',
              'ndk;30.0.16248370':'ndk/30.0.16248370','cmake;3.31.1':'cmake/3.31.1'}
    repository=ET.fromstring((ROOT/'artifacts/week1/environment/android_repository.xml').read_bytes())
    for package,dest in packages.items():
        target=Path(sdk)/dest
        node=next(e for e in repository.findall('remotePackage') if e.attrib['path']==package)
        if (target/'source.properties').exists():
            write_package_metadata(repository,node,target)
            continue
        archive=next(e for e in node.findall('archives/archive') if e.findtext('host-os') in ('windows',None))
        complete=archive.find('complete'); url=complete.findtext('url'); local=ROOT/'vendor'/Path(url).name
        if not local.exists():
            print('Downloading',package,url,flush=True)
            urllib.request.urlretrieve('https://dl.google.com/android/repository/'+url,local)
        checksum=complete.find('checksum'); algorithm=checksum.attrib.get('type','sha1')
        digest=hashlib.new(algorithm,local.read_bytes()).hexdigest()
        assert digest==checksum.text,'SDK archive checksum mismatch'
        target.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(local) as z:
            roots={e.filename.split('/')[0] for e in z.infolist()}
            strip=next(iter(roots))+'/' if len(roots)==1 else ''
            for e in z.infolist():
                relative=e.filename[len(strip):] if strip else e.filename
                if not relative:continue
                output=(target/relative).resolve()
                if not output.is_relative_to(target.resolve()):raise ValueError('Unsafe SDK archive')
                if e.is_dir():output.mkdir(parents=True,exist_ok=True)
                else:output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(z.read(e))
        print('Installed',package,'checksum',digest,flush=True)
        write_package_metadata(repository,node,target)
    assert all((Path(sdk)/d/'source.properties').exists() for d in packages.values()),'SDK installation incomplete'
    print('Verified Android SDK packages installed',packages,flush=True)

if __name__=='__main__':main()
