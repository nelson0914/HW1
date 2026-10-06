# -*- coding: utf-8 -*-
import sqlite3, sys, json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM TemperatureForecasts ORDER BY regionName, dataDate")
rows = cur.fetchall()
conn.close()

region_days = defaultdict(list)
for row in rows:
    region_days[row['regionName']].append(dict(row))

order = ['北部地區','中部地區','南部地區','東北部地區','東部地區','東南部地區']
print("=== REAL 7-DAY FORECAST FROM DB (Oct 2026) ===")
for rname in order:
    days = sorted(region_days.get(rname, []), key=lambda x: x['dataDate'])
    if days:
        mints = [str(int(round(float(d['minT'])))) for d in days]
        maxts = [str(int(round(float(d['maxT'])))) for d in days]
        dates = [d['dataDate'] for d in days]
        print(f'"{rname}": mint=[{",".join(mints)}] maxt=[{",".join(maxts)}]')
        print(f'  dates: {dates}')
