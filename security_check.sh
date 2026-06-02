#!/bin/bash
# security_check.sh - Project Security Audit Script

echo "--- 🛡️ Starting Security Audit ---"

echo -e "
[1/2] Running Bandit (SAST)..."
# -r: recursive, -ll: only medium/high severity, -iii: high confidence
bandit -r app/ -ll -iii

BANDIT_EXIT=$?

echo -e "
[2/2] Running Safety (Dependency Check)..."
# Checks installed packages against known vulnerabilities
safety check

SAFETY_EXIT=$?

echo -e "
--- 🏁 Audit Complete ---"

if [ $BANDIT_EXIT -eq 0 ] && [ $SAFETY_EXIT -eq 0 ]; then
    echo "✅ No critical security issues found."
    exit 0
else
    echo "⚠️ Security issues were detected. Please review the output above."
    exit 1
fi
