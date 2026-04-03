#!/bin/bash

echo "Running tests with TEST_STEPS=${TEST_STEPS:-all}"

STEP_NAMES=("pylint" "jslint" "integration" "pyjslint")
SCRIPT_NAMES=("test_pylint.sh" "test_jslint.sh" "test_integration.sh" "test_pyjslint.sh")

PASSED=0
TOTAL=0

for i in "${!STEP_NAMES[@]}"; do
    STEP_NAME="${STEP_NAMES[$i]}"
    SCRIPT_NAME="${SCRIPT_NAMES[$i]}"
    
    if [[ "${TEST_STEPS:-all}" != "all" && "${TEST_STEPS}" != *"$STEP_NAME"* ]]; then
        echo "[SKIP] $STEP_NAME (not in TEST_STEPS)"
        continue
    fi
    
    TOTAL=$((TOTAL + 1))
    echo "[RUN] $STEP_NAME"
    
    bash "/tester/scripts/$SCRIPT_NAME"
    
    if [ $? -eq 0 ]; then
        echo "[PASS] $STEP_NAME"
        PASSED=$((PASSED + 1))
    else
        echo "[FAIL] $STEP_NAME"
    fi

done

echo "$PASSED / $TOTAL tests passed"