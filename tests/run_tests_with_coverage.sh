#!/bin/bash
# Clean previous coverage data
NAME=$(basename $(realpath .))
DOCS=/tmp/"$NAME"_coverage
export COVERAGE_FILE=/tmp/."$NAME"_coverage
echo [$NAME] $DOCS
rm -f "$COVERAGE_FILE"*
rm -rf $DOCS

# Run tests with coverage
python -m pytest -s tests/ \
  --cov=$NAME \
  --cov-append \
  --cov-report=term-missing || exit 1

# Combine all coverage data
python -m coverage combine

# Generate HTML report in /tmp
python -m coverage html \
  --directory="$DOCS" \
  --title="$NAME Coverage Report"

echo "Coverage report generated at: $DOCS/index.html"