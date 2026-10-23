# Unicode query data

Query normalization tables implement Unicode 15.0.0 NFKC, default lowercase,
case properties and word/whitespace categories. Data is derived from Unicode
data and the pinned Python 3.12 Unicode 15 engine. Original Unicode data is
copyright Unicode, Inc.; retain the accompanying Unicode15-LICENSE.txt.

Official inputs are from https://www.unicode.org/Public/15.0.0/ucd/ . Their
acquisition URLs, timestamps, byte counts and SHA256 identities are recorded in
artifacts/v1.3/m4/unicode15-inputs-0001/acquisition.json. The license text is the
official text available at acquisition, not represented as a frozen 2022 text.

Regenerate with the pinned .venv-pack Python using:

```
python -X utf8 -m scripts.v13_query_unicode --inputs artifacts/v1.3/m4/unicode15-inputs-0001 --check
```

The JSON table and generated Kotlin table must reproduce byte for byte. The
official normalization corpus is copied unchanged to host and Android test
inputs. Archive-name case folding remains an independent existing contract.
