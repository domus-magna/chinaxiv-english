#!/usr/bin/env bash
set -euo pipefail

PR_NUMBER=20
LOG_FILE="pr20-watch.log"
STATE_FILE=".pr20-watch.state"

# Resolve repo and PR branch
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")"
BRANCH="$(gh pr view "$PR_NUMBER" --json headRefName -q .headRefName 2>/dev/null || echo "")"

touch "$STATE_FILE" "$LOG_FILE"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting watcher for PR #$PR_NUMBER ($REPO branch=$BRANCH)" | tee -a "$LOG_FILE"

while true; do
  # Fetch PR comments and reviews
  PR_JSON="$(gh pr view "$PR_NUMBER" --json comments,reviews 2>/dev/null || echo '{}')"
  INLINE_JSON="$(gh api repos/$REPO/pulls/$PR_NUMBER/comments 2>/dev/null || echo '[]')"

  # Compute a digest to detect changes
  DIGEST="$(printf "%s\n%s" "$PR_JSON" "$INLINE_JSON" | shasum | awk '{print $1}')"
  LAST_DIGEST="$(cat "$STATE_FILE" 2>/dev/null || echo '')"

  if [[ "$DIGEST" != "$LAST_DIGEST" ]]; then
    COMMENTS_COUNT=$(echo "$PR_JSON" | jq -r '(.comments | length) // 0')
    REVIEWS_COUNT=$(echo "$PR_JSON" | jq -r '(.reviews | length) // 0')
    INLINE_COUNT=$(echo "$INLINE_JSON" | jq -r 'length')

    LATEST_PR_TIME=$(echo "$PR_JSON" | jq -r '[.comments[]?.createdAt, .reviews[]?.submittedAt] | map(select(. != null)) | max // empty')
    LATEST_INLINE_TIME=$(echo "$INLINE_JSON" | jq -r 'map(.created_at) | max // empty')

    # Fetch latest run for the branch, if available
    RUN_JSON="$(gh run list --branch "$BRANCH" --limit 1 --json databaseId,headBranch,status,conclusion,updatedAt,displayTitle 2>/dev/null || echo '[]')"
    RUN_STATUS=$(echo "$RUN_JSON" | jq -r '.[0].status // empty')
    RUN_CONCLUSION=$(echo "$RUN_JSON" | jq -r '.[0].conclusion // empty')
    RUN_TITLE=$(echo "$RUN_JSON" | jq -r '.[0].displayTitle // empty')
    RUN_UPDATED=$(echo "$RUN_JSON" | jq -r '.[0].updatedAt // empty')

    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] PR#${PR_NUMBER} updated: comments=${COMMENTS_COUNT}, reviews=${REVIEWS_COUNT}, inline=${INLINE_COUNT}; latestPR=${LATEST_PR_TIME:-n/a}, latestInline=${LATEST_INLINE_TIME:-n/a}; CI=${RUN_STATUS:-n/a}/${RUN_CONCLUSION:-n/a} (${RUN_TITLE:-n/a}) @ ${RUN_UPDATED:-n/a}" | tee -a "$LOG_FILE"

    echo "$DIGEST" > "$STATE_FILE"
  fi

  sleep 120
done

