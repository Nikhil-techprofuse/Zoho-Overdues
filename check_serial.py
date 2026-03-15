import sqlite3

db = 'd:/Invoice clone/Zoho-Overdues/instance/database.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

lines = []

cur.execute('SELECT COUNT(*), SUM(CASE WHEN serial_no>0 THEN 1 ELSE 0 END), SUM(CASE WHEN serial_no=0 OR serial_no IS NULL THEN 1 ELSE 0 END) FROM daily_upload')
r = cur.fetchone()
lines.append(f'Total: {r[0]}  Assigned: {r[1]}  Missing(0): {r[2]}')

# Global duplicates (same serial_no across ALL records globally)
cur.execute('''SELECT serial_no, COUNT(*) as cnt FROM daily_upload
               WHERE is_active=1 AND serial_no>0
               GROUP BY serial_no HAVING cnt>1 ORDER BY cnt DESC LIMIT 10''')
dups = cur.fetchall()
lines.append(f'\nGlobal duplicate serial_no (across all owners): {len(dups)} found')
for d in dups[:10]:
    lines.append(f'  serial_no={d[0]} appears {d[1]}x')
    cur.execute('SELECT owner, transaction_no, serial_no, change_flag FROM daily_upload WHERE serial_no=? AND is_active=1', (d[0],))
    for rec in cur.fetchall():
        lines.append(f'    -> owner={rec[0]} txn={rec[1]} flag={rec[3]}')

# Latest upload batch
cur.execute('SELECT DISTINCT upload_timestamp FROM daily_upload ORDER BY upload_timestamp DESC LIMIT 4')
ts_list = [r[0] for r in cur.fetchall()]
for ts in ts_list:
    cur.execute('SELECT COUNT(*), MIN(serial_no), MAX(serial_no), SUM(CASE WHEN change_flag="new" THEN 1 ELSE 0 END) FROM daily_upload WHERE upload_timestamp=?', (ts,))
    r = cur.fetchone()
    lines.append(f'\nUpload {ts}: records={r[0]}, serial={r[1]}-{r[2]}, new={r[3]}')

# Per owner active
lines.append('\nActive per owner:')
cur.execute('SELECT owner, COUNT(*), MIN(serial_no), MAX(serial_no) FROM daily_upload WHERE is_active=1 GROUP BY owner ORDER BY owner')
for row in cur.fetchall():
    lines.append(f'  {str(row[0]):<25} count={row[1]:>3}  serial={row[2]}-{row[3]}')

conn.close()

output = '\n'.join(lines)
print(output)
with open('serial_check_result.txt', 'w') as f:
    f.write(output)
print('\nSaved to serial_check_result.txt')
