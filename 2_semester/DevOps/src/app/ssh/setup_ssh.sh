#!/bin/bash

mkdir -p /run/sshd
mkdir -p /root/.ssh && chmod 700 /root/.ssh

mv /tmp/app_key.pub /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

sed -i 's/^#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
