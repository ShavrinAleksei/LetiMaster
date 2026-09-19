#!/bin/bash

mkdir -p /logs

exec > >(tee -a /logs/jslint_stdout.log)
exec 2> >(tee -a /logs/jslint_stderr.log >&2)

echo "This is a jslint stderr message" >&2
echo "This is a jslint stdout message"

JS_FILES=$(find /app -name "*.js")

if [ -z "$JS_FILES" ]; then
    echo "ERROR: No JS files found in /app" >&2
    exit 1
fi

node ./jslint.mjs $JS_FILES

exit $?
