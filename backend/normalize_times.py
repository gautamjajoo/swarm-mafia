"""One-time correction for pre-normalization derived timestamps; sources unchanged."""
import sys
from store import initialize, normalize_time

db = initialize(sys.argv[1])
changed = 0
while True:
    rows = db.execute("SELECT pk,timestamp FROM records WHERE timestamp IS NOT NULL AND length(timestamp)!=27 LIMIT 5000").fetchall()
    if not rows:
        break
    db.executemany("UPDATE records SET timestamp=? WHERE pk=?",[(normalize_time(value),pk) for pk,value in rows])
    db.commit()
    changed += len(rows)
    print("normalized_timestamp_rows",changed,flush=True)
db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
print("complete",changed)
