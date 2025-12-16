import React, { useState, useRef, useEffect } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Drawing pad state
  const canvasRef = useRef(null);
  const [drawingRecords, setDrawingRecords] = useState([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [lastPos, setLastPos] = useState(null);

  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#111827";
  }, []);

  const getPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const drawLine = (from, to, pressure) => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    ctx.beginPath();
    ctx.lineWidth = Math.max(1, (pressure || 0.5) * 4);
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
  };

  const handlePointerDown = (e) => {
    e.preventDefault();
    if (!canvasRef.current) return;
    canvasRef.current.setPointerCapture &&
      canvasRef.current.setPointerCapture(e.pointerId);
    const pos = getPos(e);
    const t = Date.now();
    const rec = {
      timestamp_ms: t,
      x: pos.x,
      y: pos.y,
      pressure: e.pressure ?? 0,
      button: 1,
    };
    setDrawingRecords((prev) => [...prev, rec]);
    setIsDrawing(true);
    setLastPos(pos);
    // small dot
    const ctx = canvasRef.current.getContext("2d");
    ctx.beginPath();
    ctx.fillStyle = "#111827";
    ctx.arc(pos.x, pos.y, Math.max(1, (e.pressure || 0.5) * 2), 0, Math.PI * 2);
    ctx.fill();
  };

  const handlePointerMove = (e) => {
    if (!isDrawing) return;
    const pos = getPos(e);
    const t = Date.now();
    const rec = {
      timestamp_ms: t,
      x: pos.x,
      y: pos.y,
      pressure: e.pressure ?? 0,
      button: 1,
    };
    setDrawingRecords((prev) => [...prev, rec]);
    drawLine(lastPos || pos, pos, e.pressure);
    setLastPos(pos);
  };

  const handlePointerUp = (e) => {
    if (!canvasRef.current) return;
    canvasRef.current.releasePointerCapture &&
      canvasRef.current.releasePointerCapture(e.pointerId);
    const pos = getPos(e);
    const t = Date.now();
    const rec = {
      timestamp_ms: t,
      x: pos.x,
      y: pos.y,
      pressure: e.pressure ?? 0,
      button: 0,
    };
    setDrawingRecords((prev) => [...prev, rec]);
    setIsDrawing(false);
    setLastPos(null);
  };

  const handleClearDrawing = () => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    ctx.clearRect(0, 0, c.width, c.height);
    setDrawingRecords([]);
  };

  const handleAnalyzeDrawing = async () => {
    if (drawingRecords.length === 0) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/analyze_strokes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records: drawingRecords }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: String(err) });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: String(err) });
    } finally {
      setLoading(false);
    }
  };

  const dementiaProb = result?.ml?.probability?.dementia_probability ?? null;
  const diagnosis = result?.ml?.probability?.diagnosis ?? null;
  const hasError = result?.error || result?.ml?.error;

  const getDiagnosisColor = () => {
    if (dementiaProb === null) return "bg-gray-200";
    return dementiaProb >= 50 ? "bg-red-500" : "bg-green-500";
  };

  const getDiagnosisText = () => {
    if (dementiaProb === null) return "분석 불가";
    return dementiaProb >= 50 ? "⚠️ 치매 의심" : "✓ 정상";
  };

  const formatProb = (p) => {
    if (p === null) return "분석 불가";
    if (p > 0 && p < 0.01) return "<0.01";
    return p.toFixed(2);
  };

  return (
    <div
      style={{
        backgroundImage: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        minHeight: "100vh",
      }}
      className="flex items-center justify-center p-4"
    >
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🧠 치매 예측 서비스
          </h1>
          <p className="text-purple-100 text-lg">
            WACOMPAD 기반 치매 진단 분석 시스템
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Form Section: CSV Upload + Drawing Pad */}
          <div className="p-8 border-b border-gray-200">
            <div className="space-y-6">
              {/* CSV Upload */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-gray-700 font-semibold mb-3">
                    CSV 파일 선택
                  </label>
                  <div className="relative">
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => setFile(e.target.files[0])}
                      className="w-full px-4 py-3 border-2 border-dashed border-purple-300 rounded-lg focus:outline-none focus:border-purple-500 transition file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
                    />
                  </div>
                  {file && (
                    <p className="mt-2 text-sm text-gray-600">
                      선택된 파일:{" "}
                      <span className="font-semibold">{file.name}</span>
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading || !file}
                  className={`w-full py-3 px-4 rounded-lg font-bold text-white text-lg transition duration-300 ${
                    loading || !file
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-gradient-to-r from-purple-500 to-pink-500 hover:shadow-lg transform hover:-translate-y-1"
                  }`}
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <svg
                        className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      분석 중...
                    </span>
                  ) : (
                    "📊 분석 시작"
                  )}
                </button>
              </form>

              {/* Drawing Pad */}
              <div>
                <label className="block text-gray-700 font-semibold mb-3">
                  직접 필기하기 (Wacom 펜 지원)
                </label>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex gap-3 mb-3">
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleAnalyzeDrawing();
                      }}
                      className={`py-2 px-4 rounded-md font-semibold text-white ${
                        loading
                          ? "bg-gray-400"
                          : "bg-indigo-600 hover:bg-indigo-700"
                      }`}
                      disabled={loading || drawingRecords.length === 0}
                    >
                      🖊️ 필기 분석
                    </button>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleClearDrawing();
                      }}
                      className="py-2 px-4 rounded-md font-semibold bg-gray-100 hover:bg-gray-200"
                    >
                      지우기
                    </button>
                    <div className="text-sm text-gray-500 mt-2">
                      펜 또는 마우스로 캔버스에 글을 써주세요. (압력 데이터가
                      가능한 디바이스에서 압력 전송)
                    </div>
                  </div>

                  <div className="w-full border rounded overflow-hidden">
                    <canvas
                      ref={canvasRef}
                      width={800}
                      height={400}
                      className="w-full h-64 touch-none"
                      style={{ background: "#fff" }}
                      onPointerDown={handlePointerDown}
                      onPointerMove={handlePointerMove}
                      onPointerUp={handlePointerUp}
                      onPointerCancel={handlePointerUp}
                    />
                  </div>

                  <div className="mt-3 text-xs text-gray-600">
                    캡처된 이벤트 수: {drawingRecords.length}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Result Section */}
          {result && (
            <div className="p-8 space-y-6 bg-gray-50">
              {hasError ? (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                  <p className="text-red-700 font-semibold">❌ 분석 실패</p>
                  <p className="text-red-600 text-sm mt-1">
                    {result.error || result.ml?.error}
                  </p>
                </div>
              ) : (
                <>
                  {/* Diagnosis Result - Large Prominent Display */}
                  {dementiaProb !== null && (
                    <div className="space-y-4">
                      <h2 className="text-2xl font-bold text-gray-800">
                        분석 결과
                      </h2>

                      {/* Big Circle with Probability */}
                      <div className="flex flex-col items-center justify-center py-8 bg-white rounded-xl border-2 border-purple-200">
                        <div className="relative w-48 h-48 flex items-center justify-center">
                          <div
                            className={`absolute inset-0 rounded-full ${getDiagnosisColor()} opacity-20`}
                          ></div>
                          <div className="text-center z-10">
                            <div
                              className={`text-6xl font-bold ${
                                dementiaProb >= 50
                                  ? "text-red-600"
                                  : "text-green-600"
                              }`}
                            >
                              {formatProb(dementiaProb)}%
                            </div>
                            <p className="text-gray-600 mt-2 text-sm">
                              치매 확률
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Diagnosis Status */}
                      <div
                        className={`p-6 rounded-lg border-2 ${
                          dementiaProb >= 50
                            ? "bg-red-50 border-red-300"
                            : "bg-green-50 border-green-300"
                        }`}
                      >
                        <p
                          className={`text-2xl font-bold text-center ${
                            dementiaProb >= 50
                              ? "text-red-700"
                              : "text-green-700"
                          }`}
                        >
                          {getDiagnosisText()}
                        </p>
                      </div>

                      {/* Probability Breakdown */}
                      <div className="grid grid-cols-2 gap-4 pt-4">
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                          <p className="text-gray-600 text-sm font-semibold">
                            정상 확률
                          </p>
                          <p className="text-2xl font-bold text-green-600 mt-1">
                            {formatProb(100 - dementiaProb)}%
                          </p>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                          <p className="text-gray-600 text-sm font-semibold">
                            치매 확률
                          </p>
                          <p className="text-2xl font-bold text-red-600 mt-1">
                            {formatProb(dementiaProb)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Preprocessing Details */}
                  {result.preprocessing && (
                    <div className="pt-4 border-t border-gray-300">
                      <button
                        onClick={() =>
                          document
                            .getElementById("preprocessing-details")
                            .classList.toggle("hidden")
                        }
                        className="text-purple-600 font-semibold hover:text-purple-700 transition"
                      >
                        📋 상세 전처리 정보 보기
                      </button>
                      <div
                        id="preprocessing-details"
                        className="hidden mt-4 bg-white p-4 rounded-lg border border-gray-200 text-sm text-gray-700 max-h-64 overflow-y-auto"
                      >
                        <pre className="whitespace-pre-wrap break-words font-mono text-xs">
                          {JSON.stringify(result.preprocessing, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Footer */}
          {!result && (
            <div className="p-8 text-center text-gray-500 text-sm bg-gray-50">
              <p>📤 CSV 파일을 선택하고 분석을 시작하세요</p>
            </div>
          )}
        </div>

        {/* Footer Info */}
        <div className="text-center mt-6 text-purple-100">
          <p className="text-sm">WACOMPAD-based Dementia Diagnosis AI System</p>
        </div>
      </div>
    </div>
  );
}

export default App;
