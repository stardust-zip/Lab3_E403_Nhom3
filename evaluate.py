"""
Evaluation Script: Parse telemetry logs and generate performance comparison.

Usage:
    python evaluate.py                  — Analyze today's logs
    python evaluate.py 2026-04-06       — Analyze a specific date's logs
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict


def parse_log_file(log_path: str) -> list:
    """Parse a JSON-lines log file into a list of events."""
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue
    return events


def analyze_metrics(events: list) -> dict:
    """Analyze LLM_METRIC events for performance stats."""
    metrics = [e["data"] for e in events if e.get("event") == "LLM_METRIC"]
    if not metrics:
        return {"count": 0}

    latencies = [m["latency_ms"] for m in metrics]
    total_tokens = [m.get("total_tokens", 0) for m in metrics]
    costs = [m.get("cost_estimate", 0) for m in metrics]

    return {
        "count": len(metrics),
        "latency_avg_ms": round(sum(latencies) / len(latencies), 1),
        "latency_min_ms": min(latencies),
        "latency_max_ms": max(latencies),
        "latency_p50_ms": sorted(latencies)[len(latencies) // 2],
        "tokens_avg": round(sum(total_tokens) / len(total_tokens), 1),
        "tokens_total": sum(total_tokens),
        "cost_total": round(sum(costs), 4),
    }


def analyze_agents(events: list) -> dict:
    """Analyze agent run events: steps, errors, success rate."""
    results = {"chatbot": [], "agent_v1": [], "agent_v2": []}

    for e in events:
        event_type = e.get("event", "")
        data = e.get("data", {})

        if event_type == "CHATBOT_END":
            results["chatbot"].append({
                "latency_ms": data.get("latency_ms", 0),
                "tokens": data.get("tokens", {}),
                "output_length": len(data.get("output", "")),
            })
        elif event_type == "AGENT_V1_END":
            results["agent_v1"].append({
                "status": data.get("status", "unknown"),
                "steps": data.get("steps", 0),
                "errors": data.get("errors", []),
            })
        elif event_type == "AGENT_V2_END":
            results["agent_v2"].append({
                "status": data.get("status", "unknown"),
                "steps": data.get("steps", 0),
                "errors": data.get("errors", []),
            })

    return results


def analyze_errors(events: list) -> list:
    """Extract all error events."""
    return [e for e in events if e.get("event") == "AGENT_ERROR"]


def print_report(events: list):
    """Print a human-readable evaluation report."""
    metrics = analyze_metrics(events)
    agent_results = analyze_agents(events)
    errors = analyze_errors(events)

    print("=" * 60)
    print("  EVALUATION REPORT — Lab 3: Chatbot vs ReAct Agent")
    print("=" * 60)

    # LLM Performance
    print("\n--- LLM Performance Metrics ---")
    if metrics["count"] == 0:
        print("  No LLM requests found in logs.")
    else:
        print(f"  Total LLM calls:     {metrics['count']}")
        print(f"  Avg latency:         {metrics['latency_avg_ms']}ms")
        print(f"  Min/Max latency:     {metrics['latency_min_ms']}ms / {metrics['latency_max_ms']}ms")
        print(f"  P50 latency:         {metrics['latency_p50_ms']}ms")
        print(f"  Avg tokens/request:  {metrics['tokens_avg']}")
        print(f"  Total tokens used:   {metrics['tokens_total']}")
        print(f"  Estimated total cost: ${metrics['cost_total']}")

    # Agent Results
    print("\n--- System Comparison ---")
    for system_name, runs in agent_results.items():
        if not runs:
            print(f"\n  [{system_name.upper()}] No runs recorded.")
            continue
        print(f"\n  [{system_name.upper()}] {len(runs)} run(s)")
        if system_name == "chatbot":
            avg_latency = sum(r["latency_ms"] for r in runs) / len(runs)
            print(f"    Avg latency: {avg_latency:.0f}ms")
        else:
            successes = sum(1 for r in runs if r["status"] == "success")
            avg_steps = sum(r["steps"] for r in runs) / len(runs)
            total_errors = sum(len(r["errors"]) for r in runs)
            print(f"    Success rate: {successes}/{len(runs)} ({successes/len(runs)*100:.0f}%)")
            print(f"    Avg steps:    {avg_steps:.1f}")
            print(f"    Total errors: {total_errors}")

    # Error Breakdown
    print("\n--- Error Breakdown ---")
    if not errors:
        print("  No errors recorded.")
    else:
        error_types = defaultdict(int)
        for e in errors:
            err_msg = e["data"].get("error", "UNKNOWN")
            if "PARSE_ERROR" in err_msg:
                error_types["Parse Error"] += 1
            elif "HALLUCINATION" in err_msg:
                error_types["Hallucination"] += 1
            elif "DUPLICATE" in err_msg:
                error_types["Duplicate Action"] += 1
            else:
                error_types["Other"] += 1
        for etype, count in error_types.items():
            print(f"  {etype}: {count}")

    print(f"\n{'='*60}")
    print("Report generated from telemetry logs.")
    print("=" * 60)


def main():
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    log_path = os.path.join("logs", f"{date_str}.log")

    if not os.path.exists(log_path):
        print(f"Log file not found: {log_path}")
        print("Run main.py first to generate logs.")
        sys.exit(1)

    events = parse_log_file(log_path)
    print(f"Loaded {len(events)} events from {log_path}\n")
    print_report(events)


if __name__ == "__main__":
    main()
