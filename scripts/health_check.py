#!/usr/bin/env python3
"""Health check script for all Enterprise Analytics Platform services.

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --host 0.0.0.0

Exits with 0 if all services are healthy, 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from typing import Dict, List, Tuple


SERVICES: Dict[str, int] = {
    "analytics-api": 8000,
    "forecasting-service": 8001,
    "anomaly-detection": 8002,
}


def check_service(name: str, port: int, host: str = "localhost") -> Tuple[bool, str]:
    """Check health of a single service.

    Args:
        name: Human-readable service name.
        port: Port the service listens on.
        host: Hostname or IP of the service.

    Returns:
        (is_healthy, message) tuple.
    """
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            if resp.status == 200:
                return True, f"OK ({resp.status})"
            return False, f"Unhealthy ({resp.status})"
    except urllib.error.URLError as exc:
        return False, f"Unreachable: {exc.reason}"
    except Exception as exc:
        return False, f"Error: {exc}"


def run_health_checks(host: str = "localhost") -> List[Tuple[str, bool, str]]:
    """Run health checks for all services and return results."""
    results = []
    for name, port in SERVICES.items():
        healthy, message = check_service(name, port, host)
        results.append((name, healthy, message))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Health check all platform services")
    parser.add_argument("--host", default="localhost", help="Service hostname (default: localhost)")
    args = parser.parse_args()

    results = run_health_checks(host=args.host)

    all_healthy = True
    for name, healthy, message in results:
        status = "HEALTHY" if healthy else "UNHEALTHY"
        print(f"  {status:<10} {name:<30} {message}")
        if not healthy:
            all_healthy = False

    if all_healthy:
        print("\nAll services healthy.")
        return 0
    else:
        print("\nOne or more services are unhealthy.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
