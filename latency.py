from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import collections
import os
import json

# Initialize Flask app
app = Flask(__name__)

# 1. Enable CORS for POST requests from any origin
# The resource path matches the Vercel function path: `/api/latency`
CORS(app, resources={r"/api/latency": {"origins": "*", "methods": ["POST"]}})

def calculate_metrics(data):
    """
    Calculates avg_latency, p95_latency, avg_uptime, and breaches for each region.
    """
    results = {}
    # Default threshold is 180ms
    threshold = data.get("threshold_ms", 180) 

    # The input 'regions' is already structured as {"region_name": [records], ...}
    for region_name, records in data.get("regions", {}).items():
        if not records:
            # Handle the case of an empty record set for a region
            results[region_name] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue

        # Extract latencies and uptimes into NumPy arrays for efficient calculation
        # Accept either 'latency_ms' or 'latency' keys for latency values.
        latencies = np.array([r.get("latency_ms", r.get("latency", 0)) for r in records], dtype=float)
        # The source data may supply uptime as 'uptime_ms' or 'uptime_pct'. Prefer uptime_ms when present.
        uptimes = np.array([r.get("uptime_ms", r.get("uptime_pct", 0)) for r in records], dtype=float)

        # Calculate metrics (mean, 95th percentile, and breach count)
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        
        # Breaches: count of records where latency is strictly above the threshold
        breaches = np.sum(latencies > threshold)

        # 4. Return per-region metrics
        results[region_name] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": int(breaches)
        }
    
    return results

@app.route('/api/latency', methods=['POST'])
def get_metrics():
    # 2. Accept a POST request with JSON body. If none provided, fall back to local JSON file
    data = None
    try:
        data = request.get_json(silent=True)
    except Exception:
        data = None

    # If no JSON body provided, try reading the local q-vercel-latency.json file
    if not data:
        file_path = os.path.join(os.path.dirname(__file__), 'q-vercel-latency.json')
        if not os.path.exists(file_path):
            return jsonify({"error": "No JSON body provided and fallback file not found"}), 400
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception:
            return jsonify({"error": "Failed to read fallback JSON file"}), 500

    # The file or POST may provide either a flat list of records (as in q-vercel-latency.json)
    # or an object with a 'regions' key. Normalize both cases into a dict keyed by region.
    structured_regions = collections.defaultdict(list)

    if isinstance(data, dict) and 'regions' in data:
        # Already grouped by region: ensure it's a dict and use directly
        regions_obj = data.get('regions', {})
        if isinstance(regions_obj, dict):
            structured_regions.update(regions_obj)
        else:
            # If 'regions' is unexpectedly a list, treat as flat list below
            records_list = regions_obj
            for record in records_list:
                region_name = record.get('region')
                if region_name:
                    structured_regions[region_name].append(record)
    elif isinstance(data, list):
        # Flat list of records (this matches q-vercel-latency.json)
        for record in data:
            region_name = record.get('region')
            if region_name:
                structured_regions[region_name].append(record)
    else:
        return jsonify({"error": "Unexpected JSON structure. Expecting a list or object with 'regions' key."}), 400

    # Some datasets use 'uptime_pct' (0-100). If needed, convert to same scale as 'uptime_ms' by leaving as pct
    # The calculation function treats uptimes as generic numeric values (mean computed directly),
    # so we don't need to transform uptime_pct to uptime_ms. Documented behavior: avg_uptime will reflect the
    # provided unit (pct or ms).

    calculation_data = {
        "regions": dict(structured_regions),
        "threshold_ms": (data.get('threshold_ms') if isinstance(data, dict) else 180) or 180
    }

    metrics = calculate_metrics(calculation_data)

    return jsonify(metrics), 200

# Vercel needs the 'app' object exposed to serve the API function.