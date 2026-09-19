#!/bin/bash

mkdir -p /logs
exec 1> >(tee -a /logs/pylint_stdout.log)
exec 2> >(tee -a /logs/pylint_stderr.log >&2)

echo "This is a pylinttest stderr message" >&2
echo "This is a pylinttest stdout message"

TARGET_FILES=$(find /app -name "*.py")

if [ -z "$TARGET_FILES" ]; then
    echo "ERROR: No Python files found in /app" >&2
    exit 1
fi

pylint --disable=all \
       --enable=C0114,C0116,C0304,C0413,C3001,W0601,W0612,W0613,W0622,E0602 \
        $TARGET_FILES

exit $?