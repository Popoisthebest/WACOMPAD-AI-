from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path
from analysis_runner import analyze
import time
import csv

app = FastAPI()

# CORS: 개발 환경에서 프론트엔드(예: http://localhost:3000)에서 백엔드로 요청할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKDIR = Path(__file__).resolve().parent


@app.post('/analyze')
async def analyze_endpoint(file: UploadFile = File(...)):
    # 저장
    upload_path = WORKDIR / 'uploads'
    upload_path.mkdir(exist_ok=True)
    file_path = upload_path / file.filename
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    try:
        result = analyze(str(file_path))
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

    return JSONResponse(result)


@app.post('/analyze_strokes')
async def analyze_strokes(payload: dict):
    # payload should be { "records": [ {timestamp_ms, x, y, pressure, button}, ... ], "debug": true }
    records = payload.get('records') if isinstance(payload, dict) else None
    debug = bool(payload.get('debug', False)) if isinstance(payload, dict) else False
    if not records or not isinstance(records, list):
        return JSONResponse({'error': 'No records provided'}, status_code=400)

    upload_path = WORKDIR / 'uploads'
    upload_path.mkdir(exist_ok=True)
    filename = f'strokes_{int(time.time() * 1000)}.csv'
    file_path = upload_path / filename

    # write CSV with expected column names for analyze()
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['시간', 'X', 'Y', '압력_NORMAL', '버튼'])
        for r in records:
            try:
                if isinstance(r, (list, tuple)):
                    t, x, y, pressure, button = r
                elif isinstance(r, dict):
                    t = r.get('timestamp_ms') or r.get('t') or r.get('시간')
                    x = r.get('x')
                    y = r.get('y')
                    pressure = r.get('pressure') or r.get('압력') or r.get('압력_NORMAL')
                    button = r.get('button') or r.get('버튼')
                else:
                    continue
                writer.writerow([t, x, y, pressure, button])
            except Exception:
                # skip malformed rows
                continue

    try:
        result = analyze(str(file_path), debug=debug)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

    return JSONResponse(result)


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
