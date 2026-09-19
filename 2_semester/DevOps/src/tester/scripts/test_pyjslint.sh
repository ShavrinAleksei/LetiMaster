#!/bin/bash

mkdir -p /logs

exec > >(tee -a /logs/pyjslint_stdout.log)
exec 2> >(tee -a /logs/pyjslint_stderr.log >&2)

echo "This is a pyjslint stderr message" >&2
echo "This is a pyjslint stdout message"

JS_FILES=$(find /app -name "*.js")

if [ -z "$JS_FILES" ]; then
    echo "ERROR: No JS files found in /app" >&2
    exit 1
fi

pyjslint  $JS_FILES

exit $?

