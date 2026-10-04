# Swarm Observatory deployment

The API runs on the existing `unsc-v12-runner` VM in project
`third-technique-504821-m4`, zone `asia-south1-c`. Existing shared workloads and
network isolation rules are preserved. The existing IP was reserved as the
regional address `swarm-observatory-api`.

- API origin: `https://swarm-observatory.34.93.205.17.sslip.io`
- Gateway: dedicated `swarm-caddy.service`, automatically renewed Let's Encrypt TLS.
- Backend: `swarm-observatory.service`, one Uvicorn worker on `127.0.0.1:8765`.
- Code: `/home/jajoo_kairosity_ai/swarm-observatory/backend`.
- Runtime: `/home/jajoo_kairosity_ai/swarm-observatory/venv`.
- Database: `/home/jajoo_kairosity_ai/swarm-observatory/data/evidence.sqlite`.
- Dedicated storage: 80 GB `pd-balanced` disk `swarm-observatory-data`, mounted
  by UUID at `/srv/swarm-observatory`; the `data` path above is a symlink to
  `/srv/swarm-observatory/data`. Backup staging uses `/srv/swarm-observatory/backups`.
- Credentials: `/etc/swarm-observatory/backend.env`, root-owned mode 0600.
- Public ingress: TCP 80/443 only via dedicated `swarm-observatory-web` tag/rule.
- IAP remains the SSH path; the backend port is not public.

All gateway paths except `GET /health` require the exact bearer token. Backend
data endpoints independently verify the token. The health response contains
only a minimal status. Caddy admin API and access logs are disabled; backend
access logs are disabled to avoid recording search queries. Service diagnostics
remain available in journald. Browser requests must go through the authenticated
Sites Worker. Authorized CLI/MCP clients may call the HTTPS API directly using
private token-file configuration. Never expose the upstream token in browser
code or Vite variables.

`sslip.io` is an external DNS dependency. A production-owned domain can replace
the hostname in `Caddyfile`; preserve the authentication gate and verify TLS
before changing the Worker origin.

## Deploy and operate

Use `/opt/homebrew/bin/gcloud compute ssh unsc-v12-runner --zone asia-south1-c
--project third-technique-504821-m4 --tunnel-through-iap` for remote maintenance.

1. Upload these files to `~/swarm-deploy` and backend source to its dedicated directory.
2. Run `bash ~/swarm-deploy/provision-gateway.sh` to install the gateway and create
   the initial random credential. It preserves existing credentials on reruns.
3. Run `sudo python3 ~/swarm-deploy/configure-backend-env.py`.
4. Create the backend venv and install `backend/requirements.txt`.
5. Install the service files in `/etc/systemd/system/`, run `sudo systemctl
   daemon-reload`, then enable `swarm-observatory.service` and
   `swarm-observatory-backup.timer`.
6. After source changes, restart only `swarm-observatory.service`.
7. Inspect diagnostics with `sudo journalctl -u swarm-observatory -u swarm-caddy
   --since '10 minutes ago'`. Do not dump environment files or Caddy adapted JSON.

`deploy/runtime-versions.txt` captures the deployed system/venv Python versions
and exact `pip freeze` package versions used for verification. Use it to rebuild
the tested Python environment rather than resolving broad requirement ranges
afresh. It is a runtime snapshot, not a complete operating-system lockfile;
system packages, base image, and binary downloads are not fully locked.

Run `python3 deploy/export-worker-secret.py` locally to copy the bearer token via
IAP into `~/.codex/secrets/swarm-observatory/api-token` (mode 0600). The program
prints only the path. Feed that file directly to the Worker secret configuration
command through standard input. Keep the secret server-side. For rotation,
replace both token keys in the remote environment, update the Worker secret, and
restart both API and gateway services during a controlled window.

## Vertex AI

Vertex AI API is enabled. The VM service account has `roles/aiplatform.user` and
uses metadata/ADC credentials, with no service-account keys. Deployment sets
`GOOGLE_CLOUD_PROJECT=third-technique-504821-m4`,
`GOOGLE_CLOUD_LOCATION=global`, and `VERTEX_MODEL=gemini-3.5-flash`.
`verify-vertex.py` performs a tiny paid smoke test without sending dataset data.
On 2026-10-04 it returned `OK` (5 input, 1 visible output, 59 thinking tokens).
The model choice avoids the October 20 retirement of Gemini 2.5 Flash documented
in the [Google model lifecycle](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions).

## Backups and recovery

`swarm-observatory-backup.timer` takes daily consistent SQLite snapshots at 03:00
UTC plus up to 30 minutes jitter. `backup-sqlite.py` uses SQLite's online backup
API and checks the snapshot, closes/checkpoints the snapshot, then compresses and uploads it to
`gs://swarm-observatory-backups-504821/sqlite/`. The bucket has uniform access,
public access prevention, and a 30-day lifecycle. The VM has only object-creator
access to this bucket. An administrator retrieves backups when needed. New
backups store `archive_sha256`, `database_sha256`, and `database_bytes` in the
GCS object's custom metadata, calculated from the finalized backup files before
upload. The two initial ingestion-time backups predate this metadata contract.
The service allows up to two hours for a full-index snapshot, integrity check,
compression, and upload; the original 30-minute limit was increased for the
completed 10 GB index. Changing this timeout did not restart the active backup.

To restore, stop only `swarm-observatory.service`, retrieve a selected archive
using an authorized administrator's GCP session, decompress into a temporary
file, verify `PRAGMA quick_check`, and replace the database preserving owner and
mode. Preserve the displaced database and its WAL/SHM files for recovery. Start
the API and verify health plus an authenticated query. Never replace a live
SQLite database or mix a restored database with an old WAL.

The daily backup protects the ingested and derived evidence index; up to one
day of new index changes may be lost if its disk fails. Source datasets remain
in their original GCS location. Human investigation state is stored separately
in managed D1 storage. JSON export provides case-level portability; automated
D1 backup and restore have not been tested. This single-VM evidence API has no
automatic failover.

Backup preflight requires 2.1 times the database size plus 2 GiB free disk before
starting a snapshot. It fails safely if the growing index leaves insufficient
space; check the backup service result and increase dedicated storage capacity
before relying on backups for a larger corpus. The initial snapshot may contain
only the records indexed at snapshot time while ingestion is still active.

The dedicated volume is 80 GB because the region had 80 GB remaining under its
500 GB SSD quota; the requested 100 GB allocation was rejected. The boot volume
was not resized or reformatted. `mount-data-disk.sh` formats only the named new
blank 80 GB device, adds its UUID mount, and creates product directories.
`migrate-data.sh` is a one-time cutover after ingestion has stopped: it checkpoints
SQLite, checks both copies, verifies byte equality, preserves the old directory,
and switches the existing path to the new disk. Product units require this
mount before starting. Existing unrelated workloads do not depend on it.

The 2026-10-04 cutover preserved the original data at
`/home/jajoo_kairosity_ai/swarm-observatory/data.boot-copy-20261004T073131Z`.
Both SQLite quick checks and file checksum comparisons passed before cutover.
The disk is attached with `autoDelete=false` to preserve it if the VM is deleted.
The first cloud backup was verified at
`gs://swarm-observatory-backups-504821/sqlite/20261004T072410Z.sqlite.gz`
(277,327,238 compressed bytes); it predates the end of corpus ingestion.
The backup after storage migration also passed and was uploaded to
`gs://swarm-observatory-backups-504821/sqlite/20261004T073229Z.sqlite.gz`
(522,741,573 compressed bytes). The dedicated staging directory was cleaned
automatically after upload.

## Published Site perimeter verification

On 2026-10-04 at 08:04 UTC, the private Site at
`https://kairosity-observatory.gautamjajoo.chatgpt.site` denied all 24 external
requests with HTTP 401 before returning application data. Each row below was
tested in four combinations: no identity header versus a spoofed
`oai-authenticated-user-id`, and missing `Origin` versus the Site's own Origin.
No authentication cookies or credentials were supplied. Redirects were not
followed, and response bodies were neither printed nor persisted.

| Method | Path | Request body | Results across four combinations |
| --- | --- | --- | --- |
| GET | `/api/evidence/stats` | None | 401, 401, 401, 401 |
| GET | `/api/investigations` | None | 401, 401, 401, 401 |
| GET | `/api/investigations/nonexistent` | None | 401, 401, 401, 401 |
| POST | `/api/investigations` | Empty invalid JSON | 401, 401, 401, 401 |
| POST | `/api/investigations` | Malformed JSON | 401, 401, 401, 401 |
| PUT | `/api/investigations/nonexistent` | Malformed JSON | 401, 401, 401, 401 |

Reproduce with `python3 deploy/verify-site-perimeter.py`; the sanitized result
matrix is in `deploy/site-perimeter-results.json`. Requests use only read
operations or invalid bodies against nonexistent resources. Site audience and
access settings were not changed. The native successful deployment response
exposed only the custom Site URL, with no direct Worker alias URL. No alternate
hostname was inferred or probed. These checks establish denial at the published
perimeter from this external client; they do not independently test an
unexposed origin alias or replace application authorization tests.

Native Sites ownership metadata confirms the owner account is
`f20201638@pilani.bits-pilani.ac.in`. A browser signed into the separate jajoo
account is correctly denied; this is not evidence that the owner's access is
broken. The existing native service-bearer bypass does not inject a user
identity, so application routes correctly return 401 for that identity-less
service request. Access policy was not changed to work around either denial.
The production D1 migration is confirmed by the native database overview;
an owner-authenticated browser write has not been verified.

The two initial backups above were taken during ingestion. After the importer
and final derived-index writes finished, the full-index backup completed on
2026-10-04 at 09:33:29 UTC, covering all 13 completed sources and 3,646,304 records.
Its object is
`gs://swarm-observatory-backups-504821/sqlite/20261004T090627Z.sqlite.gz`,
generation `1791106409061678`, with 3,294,500,203 compressed bytes and a
9,985,875,968-byte SQLite snapshot. The object stores these backup-time digests:

- Archive SHA-256: `4d1c9f884b211d41689f9dab16d90c33a2cbb4b0b98a232994bf8b7463cb43f2`
- Database SHA-256: `85b8353babc799971d016d6893448d19f8bc9e106c68600df7c0c15347fa730d`
- GCS CRC32C: `gxVejw==`

The isolated VM-only restore passed on 2026-10-04 at 10:05:58 UTC. Both computed
SHA-256 digests matched the backup-time object metadata, the download passed
GCS integrity validation, and restored SQLite `quick_check` returned `ok`.
All 13 completed sources, 3,646,304 records, and all checked table counts matched
the live database through a read-only connection. The generated verification
directory was removed; the cloud snapshot remains intact and production was
never replaced or modified. The exact temporary object-read grant was revoked,
and its absence was confirmed in the returned IAM policy. Only the sanitized
report, [full-backup-restore-results.json](full-backup-restore-results.json),
was copied to the local workspace.

The backup took 27 minutes 2 seconds (09:06:27–09:33:29 UTC). Restore validation
took 31 minutes 17.507 seconds (09:34:41.167–10:05:58.674 UTC). Total elapsed time
from backup start through recorded cleanup and grant revocation was 59 minutes
45.555 seconds, ending at 10:06:12.555 UTC. The restored integrity check and
external-content FTS/table count comparisons account for substantial disk reads;
no second live integrity scan was run.

After that full backup, run `verify-backup-restore.py --object
sqlite/<backup-timestamp>.sqlite.gz` with the VM venv. The verification uses a
temporary, object-scoped read grant for the VM identity, downloads only to the
dedicated volume, and decompresses into an isolated directory. It verifies GCS
download integrity, requires and compares archive/database SHA-256 hashes
against the backup-time GCS object metadata, checks the expected database size, runs SQLite
`quick_check`, and compares source coverage and all table counts with the live
database using read-only connections. It requires every source to be complete.
The verification report remains in
`/srv/swarm-observatory/backups/verification/restore-<backup-timestamp>.json`.
Only after the report is saved and all checks pass does it remove its generated
verification copy. It preserves a failed copy for diagnosis, leaves the cloud
snapshot intact, and never replaces the production database. Revoke the
temporary object-read grant after the check. The local wrapper
`run-restore-verification.py --object sqlite/<backup-timestamp>.sqlite.gz`
automates the exact object-scoped, two-hour read grant and revokes it in a
`finally` block. It checks the returned IAM policy for removal and copies only
the sanitized JSON report to `deploy/full-backup-restore-results.json`; database
and archive bytes remain on the VM.
