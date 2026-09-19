#!/bin/bash

/usr/sbin/sshd &
exec python3 main.py