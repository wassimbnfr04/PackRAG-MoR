"""Project-local public Android tooling acquisition; no global installation."""
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/week1/environment'
OUT.mkdir(parents=True, exist_ok=True)

def download(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print('Downloading', url, flush=True)
        urllib.request.urlretrieve(url, target)

def main():
    target = ROOT / 'vendor/platform-tools.zip'
    download('https://dl.google.com/android/repository/platform-tools-latest-windows.zip', target)
    with zipfile.ZipFile(target) as z:
        for info in z.infolist():
            p = (ROOT / 'vendor' / info.filename).resolve()
            if not p.is_relative_to((ROOT / 'vendor').resolve()):
                raise ValueError('Unsafe tooling archive')
        z.extractall(ROOT / 'vendor')
    for model, name in [('HuggingFaceTB/SmolLM2-360M-Instruct','smollm2'),
                        ('ibm-granite/granite-embedding-97m-multilingual-r2','granite')]:
        with urllib.request.urlopen('https://huggingface.co/api/models/' + model) as r:
            data = json.load(r)
        (OUT / (name + '_model_metadata.json')).write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(model, data['sha'], flush=True)
    print('Tooling acquisition complete', flush=True)

if __name__ == '__main__':
    main()
