#!/usr/bin/env bash
# T036 live validation — Scenarios 1–8
# Run from the project root with a display session ($DISPLAY set).
# Credentials must be at ~/.config/home-water-usage/credentials.json.
# Each scenario opens an interactive Matplotlib window; close it to proceed.

set -e
cd "$(dirname "$0")/../.."

echo "========================================"
echo "Scenario 1 — Happy Path (SC-001)"
echo "Expected: all [✓] stages, graph window opens with usage line + 5 seasonal averages"
echo "========================================"
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31

echo ""
echo "========================================"
echo "Scenario 2 — No Exceedances in Range"
echo "Expected: [!] no exceedances warning, graph window with seasonal averages only"
echo "========================================"
uv run home-water-usage --start-date 2020-01-01 --end-date 2020-01-31

echo ""
echo "========================================"
echo "Scenario 3 — PDF Export (SC-006)"
echo "Expected: [✓] PDF saved to ./household-water-usage-2025-01-01-to-2025-12-31.pdf"
echo "========================================"
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 --save-pdf
ls -lh household-water-usage-2025-01-01-to-2025-12-31.pdf

echo ""
echo "========================================"
echo "Scenario 4 — Custom PDF Path"
echo "Expected: PDF written to /tmp/t036-report.pdf exactly"
echo "========================================"
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --save-pdf --pdf-path /tmp/t036-report.pdf
ls -lh /tmp/t036-report.pdf

echo ""
echo "========================================"
echo "Scenario 5 — Preserve Temp CSV (--no-delete-temp)"
echo "Expected: water-usage-run-2025-06-01-2025-06-30.csv remains after graph close"
echo "========================================"
uv run home-water-usage --start-date 2025-06-01 --end-date 2025-06-30 --no-delete-temp
ls water-usage-run-2025-06-01-2025-06-30.csv

echo ""
echo "========================================"
echo "Scenario 6 — Cache Refresh (--refresh-cache)"
echo "Expected: full Gmail re-fetch, [✓] History cache updated or [✓] Cache already up to date"
echo "========================================"
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 --refresh-cache

echo ""
echo "========================================"
echo "Scenario 7 — CLI Flag Overrides YAML Default (SC-002)"
echo "Expected: graph title reads 'My Custom Title'; run CSV persists after close"
echo "========================================"
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31 \
  --graph-title "My Custom Title" --no-delete-temp

echo ""
echo "========================================"
echo "Scenario 8 — Warm Cache Performance (SC-007, < 10s)"
echo "Expected: second run completes in under 10 seconds"
echo "========================================"
uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31
echo "--- timing second run ---"
time uv run home-water-usage --start-date 2025-01-01 --end-date 2025-12-31

echo ""
echo "========================================"
echo "All scenarios complete."
echo "========================================"
