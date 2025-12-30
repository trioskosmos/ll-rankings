import csv
from pathlib import Path

csv_path = Path('api/app/seeds/user_rankings.csv')
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)

# Find Rumi column
header = rows[0]
rumi_col = None
for i, h in enumerate(header):
    if 'Rumi' in h:
        rumi_col = i
        break

print(f'Rumi column: {rumi_col}')

# Search for ベロア character by character
db_name = 'ベロア'
print(f'Looking for: {repr(db_name)}')

for row_idx, row in enumerate(rows[1:], start=2):
    if len(row) <= rumi_col:
        continue
    entry = row[rumi_col]
    if 'ベロア' in entry or 'ベ' in entry:
        print(f'Row {row_idx}: {repr(entry[:60])}')
        # Compare chars
        for i, c in enumerate(entry):
            if c in 'ベロア':
                print(f'  Char {i}: {repr(c)} ord={ord(c)}')
                break

# Also check DB chars
print(f'\nDB name chars:')
for i, c in enumerate(db_name):
    print(f'  {i}: {repr(c)} ord={ord(c)}')
