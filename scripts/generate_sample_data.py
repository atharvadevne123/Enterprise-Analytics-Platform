#!/usr/bin/env python3
"""Generate sample CSV fixtures for local development and testing.

Creates lightweight synthetic data files under data/samples/ so developers
can run the pipeline locally without a live database.

Usage:
    python scripts/generate_sample_data.py
    python scripts/generate_sample_data.py --rows 50 --out-dir /tmp/samples
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path


def _dates(n: int, end: date | None = None) -> list[str]:
    if end is None:
        end = date.today()
    return [(end - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]


def write_ecommerce(out_dir: Path, rows: int) -> Path:
    path = out_dir / "ecommerce_daily_metrics.csv"
    fieldnames = [
        "date", "total_orders", "total_customers", "total_revenue",
        "average_order_value", "conversion_rate", "inventory_turnover",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for d in _dates(rows):
            orders = random.randint(200, 800)
            revenue = round(orders * random.uniform(80, 200), 2)
            w.writerow({
                "date": d,
                "total_orders": orders,
                "total_customers": random.randint(150, orders),
                "total_revenue": revenue,
                "average_order_value": round(revenue / orders, 2),
                "conversion_rate": round(random.uniform(0.02, 0.08), 4),
                "inventory_turnover": round(random.uniform(4.0, 12.0), 2),
            })
    return path


def write_supply_chain(out_dir: Path, rows: int) -> Path:
    path = out_dir / "supply_chain_daily_metrics.csv"
    fieldnames = [
        "date", "total_deliveries", "on_time_delivery_pct",
        "average_lead_time_days", "supplier_quality_score",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for d in _dates(rows):
            w.writerow({
                "date": d,
                "total_deliveries": random.randint(50, 300),
                "on_time_delivery_pct": round(random.uniform(0.82, 0.99), 4),
                "average_lead_time_days": round(random.uniform(2.0, 10.0), 1),
                "supplier_quality_score": round(random.uniform(0.75, 1.0), 4),
            })
    return path


def write_financial(out_dir: Path, rows: int) -> Path:
    path = out_dir / "financial_daily_metrics.csv"
    fieldnames = [
        "date", "total_revenue", "total_expense", "net_income", "gross_margin_pct",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for d in _dates(rows):
            revenue = round(random.uniform(50_000, 200_000), 2)
            expense = round(revenue * random.uniform(0.55, 0.80), 2)
            w.writerow({
                "date": d,
                "total_revenue": revenue,
                "total_expense": expense,
                "net_income": round(revenue - expense, 2),
                "gross_margin_pct": round((revenue - expense) / revenue * 100, 2),
            })
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate sample data CSVs")
    parser.add_argument("--rows", type=int, default=30, help="Number of rows per file")
    parser.add_argument("--out-dir", default="data/samples", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [
        write_ecommerce(out_dir, args.rows),
        write_supply_chain(out_dir, args.rows),
        write_financial(out_dir, args.rows),
    ]

    for p in files:
        print(f"  wrote {p} ({args.rows} rows)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
