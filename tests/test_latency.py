import sys
import os
import json
from collections import defaultdict

# Ensure project root is on sys.path so tests can import latency.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np

import latency


def test_small_payload_metrics():
    # Two records for apac: latencies 120 and 200, uptimes 99 and 98, threshold 180
    records = [
        {"region": "apac", "latency_ms": 120, "uptime_pct": 99},
        {"region": "apac", "latency_ms": 200, "uptime_pct": 98},
    ]

    structured = defaultdict(list)
    for r in records:
        structured[r["region"]].append(r)

    calc_data = {"regions": dict(structured), "threshold_ms": 180}
    out = latency.calculate_metrics(calc_data)

    assert "apac" in out
    apac = out["apac"]
    # avg_latency = (120 + 200) / 2 = 160.0
    assert apac["avg_latency"] == 160.0
    # p95: numpy.percentile([120,200],95) == 196.0
    assert apac["p95_latency"] == 196.0
    # avg_uptime = (99 + 98) / 2 = 98.5
    assert apac["avg_uptime"] == 98.5
    # breaches: only 200 > 180
    assert apac["breaches"] == 1


def test_fallback_file_parsing_structure():
    # Load the provided q-vercel-latency.json file and ensure calculate_metrics
    # returns a dict with per-region entries and the expected fields.
    with open("q-vercel-latency.json", "r") as f:
        data = json.load(f)

    structured = defaultdict(list)
    for r in data:
        region = r.get("region")
        if region:
            structured[region].append(r)

    calc_data = {"regions": dict(structured), "threshold_ms": 180}
    out = latency.calculate_metrics(calc_data)

    # Expect at least these regions from the sample dataset
    for expected in ["apac", "emea", "amer"]:
        assert expected in out
        region_metrics = out[expected]
        # Ensure all metric keys exist and are numeric
        for key in ["avg_latency", "p95_latency", "avg_uptime", "breaches"]:
            assert key in region_metrics
            assert isinstance(region_metrics[key], (int, float))
