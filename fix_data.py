# -*- coding: utf-8 -*-
"""Fix the FORECAST_DB in index.html with real CWA data"""

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find start and end line of FORECAST_DB block
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'const FORECAST_DB = {' in line:
        start_idx = i
    if start_idx is not None and i > start_idx and line.strip() == '};':
        end_idx = i
        break

print(f"FORECAST_DB block: lines {start_idx+1} to {end_idx+1}")
print("Old content:")
for line in lines[start_idx:end_idx+1]:
    print(f"  {repr(line.rstrip())}")

# New replacement block
new_block = [
    'const FORECAST_DB = {\n',
    '  // Real CWA 7-day forecast \u2014 synced from CWA OpenData API (F-A0010-001) on 2026-10-06\n',
    '  "\u5317\u90e8\u5730\u5340":   { mint:[12,13,14,12,12,12,14], maxt:[25,26,27,26,25,26,26] },\n',
    '  "\u4e2d\u90e8\u5730\u5340":   { mint:[7,7,8,7,6,7,8],        maxt:[30,31,31,30,29,30,31] },\n',
    '  "\u5357\u90e8\u5730\u5340":   { mint:[20,20,21,20,19,20,21], maxt:[30,31,32,31,30,31,31] },\n',
    '  "\u6771\u5317\u90e8\u5730\u5340": { mint:[18,18,19,18,17,18,19], maxt:[22,23,24,23,22,23,23] },\n',
    '  "\u6771\u90e8\u5730\u5340":   { mint:[9,10,10,9,9,9,10],     maxt:[26,27,28,27,26,27,27] },\n',
    '  "\u6771\u5357\u90e8\u5730\u5340": { mint:[23,23,24,23,22,23,24], maxt:[27,28,29,28,27,28,28] }\n',
    '};\n',
]

# Replace the lines
new_lines = lines[:start_idx] + new_block + lines[end_idx+1:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\nSUCCESS: FORECAST_DB updated!")
print("New content:")
for line in new_block:
    print(f"  {line.rstrip()}")
