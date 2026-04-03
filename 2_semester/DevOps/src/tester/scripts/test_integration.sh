#!/bin/bash

mkdir -p /logs
exec > >(tee -a /logs/integration_stdout.log)
exec 2> >(tee -a /logs/integration_stderr.log >&2)

echo "This is a integration stderr message" >&2
echo "This is a pylinintegrationttest stdout message"

python3 /tester/scripts/test_integration.py
exit $?