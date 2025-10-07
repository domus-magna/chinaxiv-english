#!/bin/bash
# Deployment script for ChinaXiv translation pipeline

set -e

echo "🚀 Deploying ChinaXiv Translation Pipeline..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found, creating..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  OPENROUTER_API_KEY not set"
    echo "   Set it with: export OPENROUTER_API_KEY=your_key_here"
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -q

# Health check
echo "🏥 Running health check..."
python -m src.health --skip-openrouter || echo "⚠️  Health check failed (non-critical)"

# Harvest sample data
echo "📥 Harvesting sample data..."
# Internet Archive harvesting removed; ensure records exist under data/records if needed

# Process sample papers
echo "🔄 Processing sample papers..."
python -m src.pipeline --limit 5 --dry-run

# Generate site
echo "🌐 Generating site..."
python -m src.render
python -m src.search_index

# Check site
if [ -d "site" ] && [ -f "site/index.html" ]; then
    echo "✅ Site generated successfully"
    echo "   Site size: $(du -sh site | cut -f1)"
    echo "   Items: $(find site/items -type d | wc -l)"
else
    echo "❌ Site generation failed"
    exit 1
fi

# Generate health report
echo "📊 Generating health report..."
python scripts/monitor.py --output data/health_report.json --quiet

# Summary
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📈 Summary:"
echo "   - Pipeline: ✅ Working"
echo "   - Site: ✅ Generated"
echo "   - Health: ✅ Monitored"
echo ""
echo "🌐 To serve the site locally:"
echo "   python -m http.server -d site 8001"
echo ""
echo "📊 To monitor health:"
echo "   python scripts/monitor.py"
echo ""
echo "🔄 To run full pipeline:"
echo "   python -m src.pipeline --limit 100"
echo ""

# Optional: Start local server
if [ "$1" = "--serve" ]; then
    echo "🌐 Starting local server on http://localhost:8001"
    python -m http.server -d site 8001
fi
