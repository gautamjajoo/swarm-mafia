"""Run on the selected GCE VM. Dataset bytes never pass through the Mac."""
import base64
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_XET_CHUNK_CACHE_SIZE_BYTES", "0")

from google.cloud import storage
from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parent
REPO = "aidigestorg/ai-village"
REVISION = "838b4150303ca8228e8edb432d8b8ccae353d258"
BUCKET = "kairosity-ai-village-504821"
PREFIX = "ai-village/"
TOKEN_FILE = ROOT / "hf-token"
completed = {}
started = time.time()


def log(message):
    print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), message, flush=True)


def main():
    global started
    if (ROOT / "status.json").exists():
        started = json.loads((ROOT / "status.json").read_text()).get("started_unix", started)
    token = TOKEN_FILE.read_text().strip()
    info = HfApi(token=token).dataset_info(REPO, revision=REVISION, files_metadata=True)
    files = []
    for f in info.siblings:
        files.append({"path": f.rfilename, "size": f.size, "git_oid": f.blob_id,
                      "sha256": f.lfs.sha256 if f.lfs else None})
    manifest = {"repository": REPO, "revision": REVISION, "files": files,
                "file_count": len(files), "total_bytes": sum(f["size"] for f in files)}
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    bucket = storage.Client().bucket(BUCKET)
    bucket.blob("_transfer/manifest.json").upload_from_string(json.dumps(manifest), content_type="application/json")
    (ROOT / "staging").mkdir(exist_ok=True)

    def status(state, **extra):
        data = {"state": state, "revision": REVISION, "file_count": len(files),
                "total_bytes": manifest["total_bytes"], "completed_files": len(completed),
                "completed_bytes": sum(x["size"] for x in completed.values()),
                "started_unix": started, "updated_unix": time.time(), **extra}
        (ROOT / "status.json").write_text(json.dumps(data, indent=2))
        bucket.blob("_transfer/status.json").upload_from_string(json.dumps(data), content_type="application/json")
        return data

    def transfer(f):
        name = f["path"]
        blob = bucket.blob(PREFIX + name)
        if blob.exists():
            blob.reload()
            metadata = blob.metadata or {}
            if blob.size != f["size"] or metadata.get("hf-revision") != REVISION or metadata.get("source-hash") != (f["sha256"] or f["git_oid"]):
                raise RuntimeError("Existing object does not match source: " + name)
            return {**f, "gcs_md5": blob.md5_hash, "generation": blob.generation}
        download_dir = ROOT / "staging" / ("hf-" + hashlib.sha256(name.encode()).hexdigest())
        for attempt in range(1, 6):
            try:
                download_start = time.monotonic()
                local = Path(hf_hub_download(REPO, name, repo_type="dataset", revision=REVISION,
                                            token=token, local_dir=download_dir))
                log(f"Downloaded {name}: {f['size'] / 1e6:.1f} MB in {time.monotonic() - download_start:.1f}s")
                sha = hashlib.sha256()
                md5 = hashlib.md5()
                git = hashlib.sha1(f"blob {f['size']}\0".encode())
                count = 0
                with local.open("rb") as source:
                    for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
                        count += len(chunk)
                        sha.update(chunk)
                        md5.update(chunk)
                        git.update(chunk)
                if count != f["size"]:
                    raise ValueError("Source size mismatch")
                if f["sha256"] and sha.hexdigest() != f["sha256"]:
                    raise ValueError("Source SHA256 mismatch")
                if not f["sha256"] and git.hexdigest() != f["git_oid"]:
                    raise ValueError("Source Git hash mismatch")
                expected_md5 = base64.b64encode(md5.digest()).decode()
                blob.metadata = {"hf-revision": REVISION, "source-hash": f["sha256"] or f["git_oid"], "sha256": sha.hexdigest()}
                # Generation zero prevents accidental overwrite; SDK validates CRC32C.
                try:
                    blob.upload_from_filename(str(local), if_generation_match=0, checksum="crc32c", timeout=600)
                except Exception:
                    if not blob.exists():
                        raise
                blob.reload()
                if blob.size != count or blob.md5_hash != expected_md5 or (blob.metadata or {}).get("sha256") != sha.hexdigest():
                    raise ValueError("Uploaded object integrity mismatch")
                shutil.rmtree(download_dir)
                return {**f, "gcs_md5": expected_md5, "generation": blob.generation}
            except Exception as exc:
                log(f"Retry {attempt}/5: {name}: {type(exc).__name__}")
                if attempt == 5:
                    raise RuntimeError("Transfer failed: " + name) from None
                time.sleep(min(60, 2 ** attempt))

    status("running")
    log(f"Starting {len(files)} files, {manifest['total_bytes']} bytes")
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(transfer, f): f for f in files}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                completed[result["path"]] = result
                status("running")
                log(f"Verified {len(completed)}/{len(files)}: {result['path']}")
        remote = {b.name.removeprefix(PREFIX): b for b in bucket.list_blobs(prefix=PREFIX)}
        if set(remote) != {f["path"] for f in files}:
            raise ValueError("Final file inventory mismatch")
        for f in files:
            b = remote[f["path"]]
            if b.size != f["size"] or b.md5_hash != completed[f["path"]]["gcs_md5"]:
                raise ValueError("Final object verification mismatch")
        audit = {**manifest, "verified_files": list(completed.values()), "verified_unix": time.time()}
        bucket.blob("_transfer/verification.json").upload_from_string(json.dumps(audit), content_type="application/json")
        final = status("complete")
        bucket.blob("_transfer/complete.json").upload_from_string(json.dumps(final), content_type="application/json")
        TOKEN_FILE.unlink(missing_ok=True)
        log("COMPLETE: every source file and uploaded checksum verified")
    except Exception as exc:
        status("failed", error=str(exc)[:300])
        log("FAILED: " + str(exc)[:300])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
