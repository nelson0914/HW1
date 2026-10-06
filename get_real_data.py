import database, json
from collections import defaultdict

# Get data from the local SQLite database (7-day forecasts stored there)
stats = database.get_summary_statistics()
print("DB Stats:", json.dumps(stats, ensure_ascii=False, indent=2))
print()

# Get all 7-day forecasts from database
import sqlite3
conn = sqlite3.connect('data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM forecasts ORDER BY regionName, dataDate")
rows = cur.fetchall()
conn.close()

region_days = defaultdict(list)
for row in rows:
    region_days[row['regionName']].append(dict(row))

print("=== REAL 7-DAY DATA FROM DB ===")
for rname in ['北部地區','中部地區','南部地區','東北部地區','東部地區','東南部地區']:
    days = sorted(region_days.get(rname, []), key=lambda x: x['dataDate'])
    mints = [str(int(round(d['minT']))) for d in days]
    maxts = [str(int(round(d['maxT']))) for d in days]
    dates = [d['dataDate'] for d in days]
    print(f'  "{rname}": {{ mint:[{",".join(mints)}], maxt:[{",".join(maxts)}] }},')
    print(f'    dates: {dates}')
    print()
