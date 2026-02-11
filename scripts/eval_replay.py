"""Evaluation harness for replaying and scoring voice agent interactions."""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_cases(input_file: str) -> list[dict[str, Any]]:
    """Parse JSONL cases file.

    Args:
        input_file: Path to JSONL file.

    Returns:
        List of case dictionaries.
    """
    cases = []
    with open(input_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def calculate_percentiles(latencies: list[float]) -> dict[str, float]:
    """Calculate latency percentiles.

    Args:
        latencies: List of latency values in milliseconds.

    Returns:
        Dict with p50, p95, p99 values.
    """
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)

    def percentile(p: float) -> float:
        if n == 0:
            return 0.0
        idx = int(n * p / 100)
        return sorted_latencies[min(idx, n - 1)]

    return {
        "p50": percentile(50),
        "p95": percentile(95),
        "p99": percentile(99),
    }


def run_eval(
    input_file: str,
    server_url: str,
    output_file: str,
    output_format: str = "markdown",
) -> dict[str, Any]:
    """Run evaluation on cases.

    Args:
        input_file: Path to JSONL cases file.
        server_url: URL of the voice agent server.
        output_file: Path to output report file.
        output_format: Output format (markdown or json).

    Returns:
        Evaluation results dict.
    """
    import httpx

    cases = parse_cases(input_file)

    results = []
    latencies = []
    tool_successes = 0
    tool_failures = 0
    accurate_responses = 0
    hallucinations = 0

    for case in cases:
        case_result = {
            "case_id": len(results) + 1,
            "transcript": case.get("transcript", ""),
            "expected_status": case.get("expected_status", "unknown"),
        }

        tool_calls = case.get("tool_calls", [])
        expected_tracking_id = case.get("expected_tracking_id", "")

        start_time = time.time()

        try:
            response = httpx.post(
                f"{server_url}/webhook",
                json=case.get("request_body", {"message": {"toolCalls": tool_calls}}),
                timeout=10.0,
            )
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)

            if response.status_code == 200:
                tool_successes += 1
                case_result["status"] = "pass"
                case_result["latency_ms"] = latency_ms

                response_data = response.json()
                tool_call_results = response_data.get("toolCallResults", [])

                if tool_call_results:
                    output = tool_call_results[0].get("output", {})
                    actual_status = output.get("status", "unknown")

                    if actual_status == expected_tracking_id:
                        accurate_responses += 1
                    else:
                        hallucinations += 1
                        case_result["status"] = "fail"
                        case_result["notes"] = (
                            f"Status mismatch: expected {expected_status}, got {actual_status}"
                        )
            else:
                tool_failures += 1
                case_result["status"] = "fail"
                case_result["latency_ms"] = latency_ms
                case_result["notes"] = f"HTTP {response.status_code}"

        except Exception as e:
            tool_failures += 1
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
            case_result["status"] = "error"
            case_result["latency_ms"] = latency_ms
            case_result["notes"] = str(e)

        results.append(case_result)

    total_cases = len(results)
    total_tool_calls = tool_successes + tool_failures

    percentiles = calculate_percentiles(latencies)

    summary = {
        "total_cases": total_cases,
        "accuracy": accurate_responses / total_cases if total_cases > 0 else 0.0,
        "tool_success_rate": tool_successes / total_tool_calls
        if total_tool_calls > 0
        else 0.0,
        "latency_p50_ms": percentiles["p50"],
        "latency_p95_ms": percentiles["p95"],
        "latency_p99_ms": percentiles["p99"],
    }

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "details": results,
    }

    if output_format == "json":
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
    else:
        with open(output_file, "w") as f:
            f.write("# Evaluation Report\n\n")
            f.write(f"**Generated**: {report['timestamp']}\n\n")
            f.write("## Summary\n\n")
            f.write(f"- Total cases: {summary['total_cases']}\n")
            f.write(f"- Accuracy: {summary['accuracy']:.1%}\n")
            f.write(f"- Tool success rate: {summary['tool_success_rate']:.1%}\n")
            f.write(f"- Latency P50: {summary['latency_p50_ms']:.0f}ms\n")
            f.write(f"- Latency P95: {summary['latency_p95_ms']:.0f}ms\n\n")
            f.write("## Details\n\n")
            f.write("| Case | Status | Latency | Notes |\n")
            f.write("|------|--------|---------|-------|\n")
            for r in results:
                status = r.get("status", "unknown")
                latency = r.get("latency_ms", 0)
                notes = r.get("notes", "")
                f.write(f"| {r['case_id']} | {status} | {latency:.0f}ms | {notes} |\n")

    return report


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluation harness for voice agent")
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSONL file with test cases",
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Voice agent server URL",
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Output report file path",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )

    args = parser.parse_args()

    try:
        results = run_eval(
            input_file=args.input,
            server_url=args.server,
            output_file=args.report,
            output_format=args.format,
        )
        print(f"Evaluation complete. Report written to {args.report}")
        print(
            f"Summary: Accuracy={results['summary']['accuracy']:.1%}, "
            f"P95 latency={results['summary']['latency_p95_ms']:.0f}ms"
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
