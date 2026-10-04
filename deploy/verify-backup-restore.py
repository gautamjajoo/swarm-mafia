"""Restore a private GCS snapshot to isolated VM storage and compare with live counts.

Requires temporary object-read permission for this one backup. Never changes
the production database. Successful verification deletes only its own temp copy.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
from google.auth.compute_engine import Credentials
from google.cloud import storage

BUCKET = 'swarm-observatory-backups-504821'
LIVE_DB = Path('/srv/swarm-observatory/data/evidence.sqlite')
ROOT = Path('/srv/swarm-observatory/backups/verification')

def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def database_summary(path, immutable=False, check_integrity=True):
    uri = f'file:{path}?mode=ro' + ('&immutable=1' if immutable else '')
    db = sqlite3.connect(uri, uri=True, timeout=30)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        status = db.execute('PRAGMA quick_check').fetchone()[0] if check_integrity else 'not_run_counts_only'
        if check_integrity and status != 'ok':
            raise RuntimeError('SQLite quick_check failed')
        source_rows = [dict(zip(('table_name', 'expected', 'indexed', 'status'), row))
                       for row in db.execute('SELECT table_name,expected,indexed,status FROM sources ORDER BY table_name')]
        if not source_rows or not all(row['status'] == 'complete' for row in source_rows):
            raise RuntimeError('Full-ingestion restore verification requires every source to be complete')
        records = dict(db.execute('SELECT table_name,COUNT(*) FROM records GROUP BY table_name ORDER BY table_name'))
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'record_fts_%' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        counts = {name: db.execute('SELECT COUNT(*) FROM "'+name.replace('"', '""')+'"').fetchone()[0]
                  for name in tables}
        return {'quick_check': status, 'sources': source_rows,
                'record_counts_by_source': records, 'table_counts': counts,
                'total_record_rows': sum(records.values())}
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--object', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'sqlite/\d{8}T\d{6}Z\.sqlite\.gz', args.object):
        raise SystemExit('Expected an exact product backup object name')
    if not os.path.ismount('/srv/swarm-observatory'):
        raise SystemExit('Dedicated volume is not mounted')
    os.umask(0o077)
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    client = storage.Client(project='third-technique-504821-m4', credentials=Credentials())
    blob = client.bucket(BUCKET).blob(args.object)
    blob.reload(timeout=60)
    metadata = blob.metadata or {}
    for key in ('archive_sha256', 'database_sha256'):
        if not re.fullmatch(r'[0-9a-f]{64}', metadata.get(key, '')):
            raise SystemExit(f'Backup object lacks a valid backup-time {key}; verification refused')
    expected_database_bytes = int(metadata.get('database_bytes', '0'))
    if expected_database_bytes <= 0:
        raise SystemExit('Backup object lacks valid backup-time database size')
    required = expected_database_bytes + int(blob.size) + 2 * 1024**3
    available = shutil.disk_usage(ROOT).free
    if available < required:
        raise SystemExit(f'Restore verification deferred: need {required}, have {available} free bytes')
    stamp = args.object.removeprefix('sqlite/').removesuffix('.sqlite.gz')
    work = Path(tempfile.mkdtemp(prefix='restore-'+stamp+'-', dir=ROOT))
    report_path = ROOT / ('restore-'+stamp+'.json')
    report = {'object_uri': f'gs://{BUCKET}/{args.object}', 'generation': blob.generation,
              'object_crc32c': blob.crc32c, 'compressed_bytes': int(blob.size),
              'expected_archive_sha256': metadata['archive_sha256'],
              'expected_database_sha256': metadata['database_sha256'],
              'expected_database_bytes': expected_database_bytes,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'production_database_modified': False, 'verification_directory': str(work)}
    try:
        archive = work / 'evidence.sqlite.gz'
        restored = work / 'evidence.sqlite'
        blob.download_to_filename(str(archive), if_generation_match=int(blob.generation),
                                  checksum='auto', timeout=120)
        report['archive_sha256'] = sha256(archive)
        if report['archive_sha256'] != report['expected_archive_sha256']:
            raise RuntimeError('Archive SHA-256 differs from the backup-time object metadata')
        with gzip.open(archive, 'rb') as src, restored.open('wb') as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        report['restored_database_bytes'] = restored.stat().st_size
        report['restored_database_sha256'] = sha256(restored)
        if report['restored_database_bytes'] != expected_database_bytes:
            raise RuntimeError('Restored database size differs from backup-time object metadata')
        if report['restored_database_sha256'] != report['expected_database_sha256']:
            raise RuntimeError('Restored database SHA-256 differs from backup-time object metadata')
        report['backup_time_digests_match'] = True
        report['restored'] = database_summary(restored, immutable=True)
        report['live'] = database_summary(LIVE_DB, check_integrity=False)
        comparison_fields = ('sources', 'record_counts_by_source', 'table_counts', 'total_record_rows')
        if any(report['restored'][key] != report['live'][key] for key in comparison_fields):
            raise RuntimeError('Restored source coverage or table counts differ from the current production database')
        report['status'] = 'passed'
        report['completed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report_path.write_text(json.dumps(report, indent=2)+'\n')
        # Only this script-created directory is removed; the cloud backup and
        # production database are never removed or replaced.
        shutil.rmtree(work)
        report['verification_copy_removed'] = True
        report_path.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'status': report['status'], 'report_path': str(report_path),
                          'object_uri': report['object_uri'],
                          'record_rows': report['restored']['total_record_rows'],
                          'sources': len(report['restored']['sources']),
                          'archive_sha256': report['archive_sha256'],
                          'restored_database_sha256': report['restored_database_sha256'],
                          'backup_time_digests_match': True,
                          'verification_copy_removed': True}))
    except Exception as error:
        report.update(status='failed', error_type=type(error).__name__, error=str(error))
        report_path.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'status': 'failed', 'report_path': str(report_path),
                          'verification_copy_preserved': True, 'error_type': type(error).__name__}))
        raise

if __name__ == '__main__':
    main()
