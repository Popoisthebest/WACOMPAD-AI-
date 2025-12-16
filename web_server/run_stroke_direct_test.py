import os
import time
from pathlib import Path
from analysis_runner import analyze

# prepare synthetic records
now = int(time.time() * 1000)
records = []
records.append((now, 50, 50, 0.5, 1))
for i in range(1, 8):
    records.append((now + i * 20, 50 + i * 5, 50 + i * 3, 0.4 + i * 0.05, 1))
records.append((now + 9 * 20, 90, 74, 0.0, 0))

# write CSV
WORKDIR = Path(__file__).resolve().parent
uploads = WORKDIR / 'uploads'
uploads.mkdir(exist_ok=True)
filename = f'strokes_direct_{int(time.time() * 1000)}.csv'
file_path = uploads / filename
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('시간,X,Y,압력_NORMAL,버튼\n')
    for r in records:
        f.write(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n")

print('Wrote CSV to', file_path)

# call analyze
res = analyze(str(file_path))
print('Result keys:', list(res.keys()))
print('Preprocessing keys:', list(res.get('preprocessing', {}).keys()))
print('ML:', res.get('ml'))
