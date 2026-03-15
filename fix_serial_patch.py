"""
Comprehensive serial_no deduplication:
- Any record with a serial_no already used by an earlier record (lower DB id)
  gets reassigned to max_serial + 1, max + 2, etc.
- This ensures EVERY record in the DB has a globally unique serial_no.
"""
import sqlite3

db = 'd:/Invoice clone/Zoho-Overdues/instance/database.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

# Load all records ordered by id (first-seen order)
cur.execute('SELECT id, transaction_no, serial_no, change_flag FROM daily_upload ORDER BY id')
all_records = cur.fetchall()

# Find current max
cur.execute('SELECT MAX(serial_no) FROM daily_upload')
max_sn = cur.fetchone()[0] or 0

seen = set()
fixes = []

for rec_id, txn, sn, flag in all_records:
    if sn and sn > 0:
        if sn in seen:
            fixes.append((rec_id, txn, sn))  # duplicate — needs new number
        else:
            seen.add(sn)
    else:
        fixes.append((rec_id, txn, sn))     # zero/null — also needs number

print(f'Total records   : {len(all_records)}')
print(f'Current max S.No: {max_sn}')
print(f'Records to fix  : {len(fixes)}')
print()

next_sn = max_sn
for rec_id, txn, old_sn in fixes:
    next_sn += 1
    cur.execute('UPDATE daily_upload SET serial_no=? WHERE id=?', (next_sn, rec_id))
    print(f'  id={rec_id:<6} txn={str(txn):<20} {old_sn} -> {next_sn}')

conn.commit()

# Final verification
cur.execute('SELECT MAX(serial_no) FROM daily_upload')
new_max = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM daily_upload WHERE serial_no=0 OR serial_no IS NULL')
zeros = cur.fetchone()[0]
cur.execute('SELECT serial_no, COUNT(*) FROM daily_upload GROUP BY serial_no HAVING COUNT(*)>1')
dups = cur.fetchall()

print(f'\n--- After fix ---')
print(f'Max serial_no: {new_max}')
print(f'serial_no = 0: {zeros}')
print(f'Duplicates   : {len(dups)} {"✅ None — all unique!" if not dups else str(dups[:5])}')

conn.close()
