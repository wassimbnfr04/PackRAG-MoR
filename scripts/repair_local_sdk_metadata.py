"""Repair metadata for already checksummed SDK archives; no downloads."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from install_android_sdk import ROOT,write_package_metadata

paths=json.loads((ROOT/'artifacts/week1/environment/android_tool_paths.json').read_text())
repository=ET.parse(ROOT/'artifacts/week1/environment/android_repository.xml').getroot()
for package,dest in [('platforms;android-37.0','platforms/android-37.0'),('build-tools;37.0.0','build-tools/37.0.0')]:
    target=Path(paths['sdk'])/dest
    assert (target/'source.properties').exists()
    node=next(e for e in repository.findall('remotePackage') if e.attrib['path']==package)
    write_package_metadata(repository,node,target)
    print('Registered checksummed local package',package)
