# latency API

This small Flask API computes per-region latency metrics.

Quick run (macOS / zsh):

1. Create and activate a virtual environment and install requirements

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the server (defaults to port 5001 to avoid macOS port conflicts):

```bash
python3 latency.py
# or override port
PORT=8080 python3 latency.py
```

3. Test with curl (POST JSON payload):

```bash
curl -v -X POST http://127.0.0.1:5001/api/latency \
  -H "Content-Type: application/json" \
  -d '{"regions":[{"region":"apac","latency_ms":120,"uptime_pct":99},{"region":"apac","latency_ms":200,"uptime_pct":98}], "threshold_ms":180}'
```

Notes
- If you POST an empty body the server will fall back to `q-vercel-latency.json` in the project root.
- The endpoint accepts either a flat list or an object with `regions` key. Latency keys accepted: `latency_ms` or `latency`. Uptime keys accepted: `uptime_ms` or `uptime_pct`.

License: MIT
