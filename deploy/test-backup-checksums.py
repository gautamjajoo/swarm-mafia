"""Synthetic round-trip and tampering checks; no production DB or GCS requests."""
from contextlib import redirect_stdout
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import sqlite3
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent

with tempfile.TemporaryDirectory(prefix='checksum-test-', dir='/srv/swarm-observatory/backups') as tmp:
    root = Path(tmp)
    live = root / 'fixture.sqlite'
    with sqlite3.connect(live) as db:
        db.executescript("""
        CREATE TABLE sources(table_name TEXT,expected INTEGER,indexed INTEGER,status TEXT);
        INSERT INTO sources VALUES('fixture',2,2,'complete');
        CREATE TABLE records(table_name TEXT,source_id TEXT);
        INSERT INTO records VALUES('fixture','one'),('fixture','two');
        """)
    stored = root / 'mock-cloud-object.gz'
    objects = {}

    class Blob:
        def __init__(self, name):
            self.name = name
            self.metadata = {}
        def upload_from_filename(self, filename, **kwargs):
            assert kwargs['if_generation_match'] == 0
            shutil.copyfile(filename, stored)
            archive_bytes = stored.read_bytes()
            database_bytes = gzip.decompress(archive_bytes)
            assert self.metadata['archive_sha256'] == hashlib.sha256(archive_bytes).hexdigest()
            assert self.metadata['database_sha256'] == hashlib.sha256(database_bytes).hexdigest()
            assert self.metadata['database_bytes'] == str(len(database_bytes))
            self.size = stored.stat().st_size
            self.generation = 1
            self.crc32c = 'mock-boundary-no-network'
        def reload(self, **kwargs):
            pass
        def download_to_filename(self, filename, **kwargs):
            assert kwargs['if_generation_match'] == 1
            assert kwargs['checksum'] == 'auto'
            shutil.copyfile(stored, filename)

    class Client:
        def bucket(self, name):
            assert name == 'swarm-observatory-backups-504821'
            return self
        def blob(self, name):
            if name not in objects:
                objects[name] = Blob(name)
            return objects[name]

    with patch('google.cloud.storage.Client', return_value=Client()), \
         patch.dict(os.environ, {'OBSERVATORY_DB': str(live)}), redirect_stdout(io.StringIO()):
        runpy.run_path(str(HERE / 'backup-sqlite.py'), run_name='__main__')
    assert len(objects) == 1
    name, blob = next(iter(objects.items()))
    spec = importlib.util.spec_from_file_location('restore_verifier', HERE / 'verify-backup-restore.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verifier.LIVE_DB = live
    verifier.ROOT = root / 'verification'

    def verify():
        with patch('google.cloud.storage.Client', return_value=Client()), \
             patch.object(sys, 'argv', ['verify', '--object', name]), redirect_stdout(io.StringIO()):
            verifier.main()

    verify()
    report_path = next(verifier.ROOT.glob('restore-*.json'))
    report = json.loads(report_path.read_text())
    assert report['status'] == 'passed' and report['backup_time_digests_match']
    assert report['verification_copy_removed'] and report['restored']['total_record_rows'] == 2
    original = dict(blob.metadata)
    for key, expected_fragment in [('archive_sha256', 'Archive SHA-256'),
                                   ('database_sha256', 'Restored database SHA-256')]:
        blob.metadata = dict(original, **{key: '0' * 64})
        try:
            verify()
        except RuntimeError as error:
            assert expected_fragment in str(error)
        else:
            raise AssertionError(f'{key} mismatch was accepted')
    blob.metadata = {}
    try:
        verify()
    except SystemExit as error:
        assert 'backup-time archive_sha256' in str(error)
    else:
        raise AssertionError('Missing digests were accepted')
print('PASS: backup metadata matches finalized files; isolated restore succeeds; archive/DB mismatch and missing metadata rejected. No production DB or GCS requests.')
