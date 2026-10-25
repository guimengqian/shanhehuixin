from pathlib import Path
import hashlib, json, zipfile
root = Path(__file__).resolve().parent
manifest = json.loads((root / 'website-manifest.json').read_text())
archive = root / 'website.zip'
with archive.open('wb') as out:
    for part in manifest['parts']:
        data = (root / part['name']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == part['sha256'], part['name']
        out.write(data)
assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['archive_sha256']
with zipfile.ZipFile(archive) as z:
    target = (root / '_site').resolve()
    for info in z.infolist():
        assert (target / info.filename).resolve().is_relative_to(target)
    z.extractall(target)
print('Website restored, including both complete films.')
