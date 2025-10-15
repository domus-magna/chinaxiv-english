#!/bin/bash
# Wrapper script for CI/CD pushes that skips self-review
# Usage: ./scripts/git-push-ci.sh [git push arguments]

echo "🚀 CI/CD Push: Skipping self-review checks"
git push --skip-self-review "$@"
