from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, time, urllib.request, zipfile

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'website-manifest.json').read_text())
def ensure_part(part):
    name = part['name']
    assert Path(name).name == name
    target = root / name
    def valid():
        return target.exists() and target.stat().st_size == part['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest() == part['sha256']
    if valid():
        return
    origin = manifest.get('transfer_origin', '')
    assert origin.startswith('https://'), 'Missing public transfer origin'
    for attempt in range(4):
        try:
            with urllib.request.urlopen(origin.rstrip('/') + '/' + name, timeout=120) as response:
                data = response.read()
            assert len(data) == part['bytes'] and hashlib.sha256(data).hexdigest() == part['sha256'], name
            target.write_bytes(data)
            print('Verified ' + name, flush=True)
            return
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(ensure_part, manifest['parts']))
archive = root / 'website.zip'
with archive.open('wb') as out:
    for part in manifest['parts']:
        out.write((root / part['name']).read_bytes())
assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['archive_sha256']
with zipfile.ZipFile(archive) as z:
    target = (root / '_site').resolve()
    for info in z.infolist():
        assert (target / info.filename).resolve().is_relative_to(target)
    z.extractall(target)
print('Website restored, including both complete films.', flush=True)

# Small verified updates overlay the complete media archive.
for patch in manifest.get('overlays', []):
    name = patch['name']
    assert Path(name).name == name
    path = root / name
    data = path.read_bytes()
    assert len(data) == patch['bytes'] and hashlib.sha256(data).hexdigest() == patch['sha256'], name
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            assert (target / info.filename).resolve().is_relative_to(target)
        z.extractall(target)
    print('Applied verified update: ' + name, flush=True)
