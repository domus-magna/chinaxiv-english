#!/bin/bash
# Run ChinaXiv harvest in background

cd "$(dirname "$0")/.."

# Kill any existing harvest
if [ -f data/harvest.pid ]; then
    OLD_PID=$(cat data/harvest.pid)
    kill $OLD_PID 2>/dev/null || true
    rm -f data/harvest.pid
fi

# Start harvest in background
echo "Starting ChinaXiv optimized harvest for Apr–Oct 2025..."
nohup python3.11 -m src.harvest_chinaxiv_optimized \
    --start 202504 \
    --end 202510 \
    --rate-limit 0.3 \
    > data/harvest.log 2>&1 &

# Save PID
echo $! > data/harvest.pid

echo "Harvest started! (PID: $!)"
echo ""
echo "Monitor with:"
echo "  python3.11 -m src.harvest_monitor status"
echo "  python3.11 -m src.harvest_monitor watch"
echo ""
echo "View logs with:"
echo "  tail -f data/harvest.log"
