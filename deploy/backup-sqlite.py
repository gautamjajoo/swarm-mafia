"""Consistent SQLite snapshots to a private GCS bucket using VM identity."""
from contextlib import closing
import datetime
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from google.auth.compute_engine import Credentials
from google.cloud import storage

def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

source = Path(os.environ['OBSERVATORY_DB'])
if not source.is_file():
    raise SystemExit('Evidence database absent; no backup uploaded.')
root = Path('/srv/swarm-observatory/backups')
# Snapshot plus worst-case gzip size and a 2 GiB host reserve. Do not endanger
# shared workloads if the growing index outgrows this VM's backup headroom.
required = int(source.stat().st_size * 2.1) + 2 * 1024**3
available = shutil.disk_usage(root).free
if available < required:
    raise SystemExit(f'Backup deferred: insufficient free disk (need {required}, have {available} bytes).')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
with tempfile.TemporaryDirectory(dir=root) as work:
    snapshot = Path(work) / 'evidence.sqlite'
    with closing(sqlite3.connect(f'file:{source}?mode=ro', uri=True)) as src:
        with closing(sqlite3.connect(snapshot)) as dst:
            src.backup(dst, pages=4096, sleep=0.05)
            check = dst.execute('PRAGMA quick_check').fetchone()[0]
            if check != 'ok':
                raise RuntimeError('Backup consistency check failed')
            checkpoint = dst.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
            if checkpoint[0] != 0:
                raise RuntimeError('Snapshot checkpoint could not complete')
    database_sha256 = sha256(snapshot)
    archive = snapshot.with_suffix('.sqlite.gz')
    with snapshot.open('rb') as src, gzip.open(archive, 'wb', compresslevel=6) as dst:
        shutil.copyfileobj(src, dst)
    archive_sha256 = sha256(archive)
    name = f'sqlite/{stamp}.sqlite.gz'
    destination = f'gs://swarm-observatory-backups-504821/{name}'
    client = storage.Client(project='third-technique-504821-m4', credentials=Credentials())
    blob = client.bucket('swarm-observatory-backups-504821').blob(name)
    blob.chunk_size = 8 * 1024 * 1024
    blob.metadata = {
        'backup_format_version': '1',
        'database_sha256': database_sha256,
        'archive_sha256': archive_sha256,
        'database_bytes': str(snapshot.stat().st_size),
    }
    blob.upload_from_filename(str(archive), content_type='application/gzip',
                              if_generation_match=0, timeout=120)
    print(f'Consistent backup uploaded: {destination}; compressed bytes={archive.stat().st_size}; '
          f'archive_sha256={archive_sha256}; database_sha256={database_sha256}')
