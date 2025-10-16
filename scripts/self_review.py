#!/bin/bash
# Simple self-review checklist for overengineering prevention
# Run this before marking any task complete

echo "🤖 SELF-REVIEW: Preventing Overengineering"
echo "========================================="
echo

echo "🔍 OVERENGINEERING REVIEW:"
echo "• Is there a simpler approach that solves 90% of the problem?"
echo "• Are we adding features 'just in case' rather than actual need?"
echo "• Can existing tools/patterns solve this instead of custom code?"
echo "• Is the complexity justified by the business value?"
echo

echo "🗂️ COMPLEXITY REDUCTION:"
echo "• Can we remove unnecessary abstractions or layers?"
echo "• Are there hardcoded values that could replace configuration?"
echo "• Can we eliminate separate services for single-purpose functionality?"
echo "• Is sophisticated state management needed, or would simple rules suffice?"
echo

echo "🐛 POTENTIAL BUGS & EDGE CASES:"
echo "• What happens if files are missing, corrupted, or have unexpected formats?"
echo "• Are there race conditions in concurrent operations?"
echo "• How does the solution handle network failures or API timeouts?"
echo "• What if the data volume is 10x larger than expected?"
echo

echo "⚡ OPTIMIZATIONS & PERFORMANCE:"
echo "• Are we making unnecessary API calls or file I/O operations?"
echo "• Can we cache expensive operations or results?"
echo "• Is there redundant processing or data transformation?"
echo "• Are we using the most efficient data structures and algorithms?"
echo

echo "✨ SIMPLICITY CHECKLIST:"
echo "• Does this solve the immediate problem without unnecessary features?"
echo "• Can a junior developer understand and maintain this code?"
echo "• Is the solution obvious and straightforward?"
echo "• Would you be proud to show this to a colleague as an example of clean code?"
echo

echo "🎯 KEY QUESTIONS FOR YOUR TASK:"
echo "1. What is the simplest solution that solves 90% of the problem?"
echo "2. Are we adding complexity that isn't justified by clear value?"
echo "3. Can existing patterns/tools solve this instead of custom code?"
echo "4. Is there unnecessary abstraction or indirection?"
echo "5. Are we solving the problem we have, or the one we imagine?"
echo

echo "💭 Take 2 minutes to reflect on these questions..."
echo "Press Enter when ready to continue"
read

echo
echo "✅ Self-review complete. Consider any simplifications before marking task done."
echo "If you identified issues, fix them before proceeding."
