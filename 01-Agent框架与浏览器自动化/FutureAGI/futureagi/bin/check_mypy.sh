#!/bin/bash

# Mypy baseline checker
# This script ensures that no new type errors are introduced
# while allowing existing errors (tracked in mypy-baseline.txt)

set -e

BASELINE_FILE="mypy-baseline.txt"
CURRENT_OUTPUT=$(mktemp)

echo "🔍 Running mypy type checking..."

# Run mypy and capture output
if mypy . > "$CURRENT_OUTPUT" 2>&1; then
    echo "✅ No type errors found! Great work!"
    rm "$CURRENT_OUTPUT"
    exit 0
fi

# If baseline doesn't exist, create it
if [ ! -f "$BASELINE_FILE" ]; then
    echo "⚠️  Baseline file not found. Creating initial baseline..."
    cp "$CURRENT_OUTPUT" "$BASELINE_FILE"
    echo "📝 Created $BASELINE_FILE with $(wc -l < "$BASELINE_FILE") lines"
    echo "ℹ️  This is your starting point. Future PRs cannot add new errors!"
    rm "$CURRENT_OUTPUT"
    exit 0
fi

# Compare current output with baseline
echo "📊 Comparing against baseline..."

# Sort both files for consistent comparison
sort "$CURRENT_OUTPUT" > "${CURRENT_OUTPUT}.sorted"
sort "$BASELINE_FILE" > "${BASELINE_FILE}.sorted"

# Find new errors (in current but not in baseline)
NEW_ERRORS=$(comm -13 "${BASELINE_FILE}.sorted" "${CURRENT_OUTPUT}.sorted")

# Find fixed errors (in baseline but not in current)
FIXED_ERRORS=$(comm -23 "${BASELINE_FILE}.sorted" "${CURRENT_OUTPUT}.sorted")

# Count errors
BASELINE_COUNT=$(wc -l < "$BASELINE_FILE")
CURRENT_COUNT=$(wc -l < "$CURRENT_OUTPUT")
NEW_ERROR_COUNT=$(echo "$NEW_ERRORS" | grep -v '^$' | wc -l || echo 0)
FIXED_ERROR_COUNT=$(echo "$FIXED_ERRORS" | grep -v '^$' | wc -l || echo 0)

echo ""
echo "📈 Type Error Summary:"
echo "  Baseline errors: $BASELINE_COUNT"
echo "  Current errors:  $CURRENT_COUNT"
echo "  New errors:      $NEW_ERROR_COUNT"
echo "  Fixed errors:    $FIXED_ERROR_COUNT"
echo ""

# Cleanup sorted temp files
rm "${CURRENT_OUTPUT}.sorted" "${BASELINE_FILE}.sorted"

# If there are new errors, fail
if [ "$NEW_ERROR_COUNT" -gt 0 ]; then
    echo "❌ NEW TYPE ERRORS DETECTED!"
    echo ""
    echo "The following type errors were not in the baseline:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$NEW_ERRORS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Please fix these type errors before committing."
    echo "Run 'make mypy-update-baseline' if these errors are intentional (discouraged)."
    rm "$CURRENT_OUTPUT"
    exit 1
fi

# If errors were fixed, congratulate and offer to update baseline
if [ "$FIXED_ERROR_COUNT" -gt 0 ]; then
    echo "🎉 GREAT JOB! You fixed $FIXED_ERROR_COUNT type error(s)!"
    echo ""
    echo "Fixed errors:"
    echo "$FIXED_ERRORS" | head -20
    if [ "$FIXED_ERROR_COUNT" -gt 20 ]; then
        echo "... and $(($FIXED_ERROR_COUNT - 20)) more"
    fi
    echo ""
    echo "✨ Please update the baseline to lock in this improvement:"
    echo "   make mypy-update-baseline"
    echo ""
    # Exit with success but indicate baseline should be updated
    rm "$CURRENT_OUTPUT"
    exit 0
fi

# No new errors, no fixed errors - all good!
echo "✅ Type checking passed! No new errors introduced."
rm "$CURRENT_OUTPUT"
exit 0
