"""Grant one backup object temporarily, verify on VM, fetch JSON report, revoke.

Run locally as an authorized GCP administrator. Only the sanitized verification
report reaches this machine; database and archive bytes remain on the VM.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import uuid

GCLOUD = '/opt/homebrew/bin/gcloud'
BUCKET = 'swarm-observatory-backups-504821'
MEMBER = 'serviceAccount:unsc-v12-runner@third-technique-504821-m4.iam.gserviceaccount.com'
SSH = [GCLOUD, 'compute', 'ssh', 'unsc-v12-runner', '--zone', 'asia-south1-c',
       '--project', 'third-technique-504821-m4', '--tunnel-through-iap']

def command(arguments):
    result = subprocess.run(arguments, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:] or f'Command exited {result.returncode}')
    return result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--object', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'sqlite/\d{8}T\d{6}Z\.sqlite\.gz', args.object):
        raise SystemExit('Expected an exact product backup object name')
    stamp = args.object.removeprefix('sqlite/').removesuffix('.sqlite.gz')
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
    resource = f'projects/_/buckets/{BUCKET}/objects/{args.object}'
    condition = {'title': 'restore-verification-'+uuid.uuid4().hex[:12],
                 'description': 'Temporary read of one backup for isolated VM restore verification',
                 'expression': f'resource.name == "{resource}" && request.time < timestamp("{expires}")'}
    report = None
    report_path = Path(__file__).resolve().parent / 'full-backup-restore-results.json'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', prefix='swarm-restore-condition-') as config:
        json.dump(condition, config)
        config.flush()
        binding = [f'gs://{BUCKET}', '--member='+MEMBER, '--role=roles/storage.objectViewer',
                   '--condition-from-file='+config.name]
        command([GCLOUD, 'storage', 'buckets', 'add-iam-policy-binding', *binding])
        print('Granted temporary read for the exact backup object; running VM-only verification.', flush=True)
        try:
            remote_command = ('/home/jajoo_kairosity_ai/swarm-observatory/venv/bin/python '
                              '/home/jajoo_kairosity_ai/swarm-deploy/verify-backup-restore.py --object '
                              + shlex.quote(args.object))
            summary = command([*SSH, '--command', remote_command])
            print(summary.strip(), flush=True)
            remote_report = f'/srv/swarm-observatory/backups/verification/restore-{stamp}.json'
            report = json.loads(command([*SSH, '--command', 'cat '+shlex.quote(remote_report)]))
            report['temporary_read_scope'] = resource
            report['temporary_read_grant_revoked'] = False
            report_path.write_text(json.dumps(report, indent=2)+'\n')
        finally:
            policy = json.loads(command([GCLOUD, 'storage', 'buckets', 'remove-iam-policy-binding', *binding,
                                         '--format=json']))
            if any(item.get('condition', {}).get('title') == condition['title'] and MEMBER in item.get('members', [])
                   for item in policy.get('bindings', [])):
                raise RuntimeError('Temporary read binding remains in the returned IAM policy')
            print('Exact temporary object-read grant revoked.', flush=True)
            if report is not None:
                report['temporary_read_grant_revoked'] = True
                report['temporary_read_binding_absent_from_returned_policy'] = True
                report_path.write_text(json.dumps(report, indent=2)+'\n')
    print(f'Sanitized verification report saved: {report_path}', flush=True)

if __name__ == '__main__':
    main()
