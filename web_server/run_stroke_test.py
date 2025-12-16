from fastapi.testclient import TestClient
import time
from main import app

client = TestClient(app)

# Create a simple synthetic stroke: pen down, several moves, pen up
now = int(time.time() * 1000)
records = []
# pen down
records.append({"timestamp_ms": now, "x": 50, "y": 50, "pressure": 0.5, "button": 1})
# moves
for i in range(1, 8):
    records.append({"timestamp_ms": now + i * 20, "x": 50 + i * 5, "y": 50 + i * 3, "pressure": 0.4 + i * 0.05, "button": 1})
# pen up
records.append({"timestamp_ms": now + 9 * 20, "x": 90, "y": 74, "pressure": 0.0, "button": 0})

resp = client.post('/analyze_strokes', json={"records": records})
print('status_code:', resp.status_code)
try:
    print('json_response:', resp.json())
except Exception as e:
    print('failed to decode json:', e, 'text:', resp.text)
